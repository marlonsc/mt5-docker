"""Headless MetaQuotes demo-account provisioning for the MT5 terminal under Wine.

Drives the terminal's ``File -> Open an Account`` wizard via ``xdotool`` on the
Xvfb display so the container can create a demo account with ZERO human
interaction.

Design (attach-only -- no OCR, no password capture):
  * After the wizard finishes the MT5 terminal is LOGGED IN to the new demo
    account. The gRPC bridge then attaches via ``mt5.initialize()`` (no creds)
    and ``AccountInfo()`` returns the login -- so the password is never needed
    here.
  * The account login is read from the terminal WINDOW TITLE (MT5 puts the
    account number in the title once logged in), not via OCR.
  * Idempotent: if the terminal is already logged in (title carries a login) or
    ``auto_demo.json`` already records one, this is a no-op.

FRAGILITY: this is GUI automation against a moving target. The keystroke
sequence and the waits may need tuning across MT5 builds/locales. On failure a
screenshot is written to ``$CONFIG_DIR/auto_demo_failure.xwd`` and the script
exits non-zero; the operator can always fall back to manual creation via the
VNC web UI (port 3000). All timings and form values are env-overridable (see
the CONFIG block) so the build can be adjusted without code changes.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

# Configuration. Every value below can be overridden via an environment variable.
DISPLAY = os.environ.get("DISPLAY", ":0")
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
RESULT_FILE = CONFIG_DIR / "auto_demo.json"
FAILURE_SHOT = CONFIG_DIR / "auto_demo_failure.xwd"

SERVER = os.environ.get("MT5_DEMO_SERVER", "MetaQuotes-Demo")
FIRST_NAME = os.environ.get("MT5_DEMO_FIRST", "Auto")
LAST_NAME = os.environ.get("MT5_DEMO_LAST", "Trader")
WINDOW_WAIT = int(os.environ.get("MT5_DEMO_WINDOW_WAIT", "120"))
LOGIN_WAIT = int(os.environ.get("MT5_DEMO_LOGIN_WAIT", "60"))
STEP_DELAY = float(os.environ.get("MT5_DEMO_STEP_DELAY", "1.5"))

# Wizard layout, calibrated for the centered "Open an Account" dialog on a
# 1024x768 KasmVNC display with the terminal in Wine virtual-desktop (/desktop=)
# mode -- the mode that makes MT5 menus/dialogs render instead of black. The
# values are root-window pixel coordinates; re-calibrate via a screenshot if the
# display size or MT5 build changes. Demo-only data; the password is never read.
MENU_DOWN_TO_OPEN_ACCOUNT = int(os.environ.get("MT5_DEMO_MENU_DOWN", "10"))
DOB_YEAR = os.environ.get("MT5_DEMO_DOB_YEAR", "1990")
PHONE = os.environ.get("MT5_DEMO_PHONE", "11988887777")
COMPANY_ROW_XY = (300, 271)
FIRST_NAME_XY = (366, 229)
LAST_NAME_XY = (366, 257)
DOB_YEAR_XY = (392, 287)
EMAIL_XY = (420, 328)
PHONE_XY = (500, 357)
AGREE_XY = (299, 545)
NEXT_XY = (714, 636)
FINISH_XY = (714, 636)

# A logged-in MT5 window title carries the account number (>= 6 digits).
LOGIN_TITLE_RE = re.compile(r"\b(\d{6,})\b")


def log(msg: str) -> None:
    """Emit a structured-ish line to stdout (captured by the container logs)."""
    print(f"[open_demo_account] {msg}", flush=True)  # noqa: T201


def _run(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a local X11 tool, always forcing DISPLAY for the headless server."""
    return subprocess.run(  # noqa: S603
        args,
        check=False,
        text=True,
        capture_output=capture,
        env={**os.environ, "DISPLAY": DISPLAY},
    )


def _xdotool(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return _run(["xdotool", *args], capture=capture)


def find_terminal_window() -> str | None:
    """Return the main MT5 terminal window id (title carries 'MetaTrader'), if any.

    The wizard/menus open child windows that also match a bare 'MetaTrader'
    search, so prefer the window whose title actually contains 'MetaTrader 5'.
    """
    res = _xdotool("search", "--name", "MetaTrader", capture=True)
    ids = [w for w in res.stdout.split() if w.strip()]
    for wid in ids:
        if "MetaTrader 5" in window_title(wid):
            return wid
    if ids:
        return ids[-1]
    # Virtual-desktop mode: the single managed X window is "<name> - Wine Desktop"
    # and the MT5 title/login live INSIDE it; drive keys/clicks into that window.
    desk = _xdotool("search", "--name", "Wine Desktop", capture=True)
    desk_ids = [w for w in desk.stdout.split() if w.strip()]
    return desk_ids[-1] if desk_ids else None


def _dismiss_popups() -> None:
    """Close MT5 first-run popups that steal keyboard focus (best-effort).

    On first launch MT5 raises a 'Welcome to LiveUpdate' window (and, after a
    failed wizard attempt, an untitled web-view dialog). Either one grabs the
    foreground, so the wizard keystrokes land in the wrong window -- the root
    cause of an empty/black wizard. We close LiveUpdate windows via wmctrl and
    press Escape a couple of times to dismiss any open menu. Never fatal here.
    """
    res = _run(["wmctrl", "-l"], capture=True)
    for line in res.stdout.splitlines():
        # `wmctrl -l` lines are "<id> <desktop> <host> <title>"; the LiveUpdate
        # marker only ever appears in the title, so match the whole line and
        # close by the window id (first field).
        if "LiveUpdate" in line:
            wid = line.split(None, 1)[0]
            _run(["wmctrl", "-ic", wid])
            log(f"closed LiveUpdate popup: {wid}")
    main_wid = find_terminal_window()
    if main_wid is not None:
        _xdotool("key", "--window", main_wid, "Escape")
        _xdotool("key", "--window", main_wid, "Escape")


def window_title(wid: str) -> str:
    """Return the X11 title of the given window id."""
    return _xdotool("getwindowname", wid, capture=True).stdout.strip()


def current_login() -> str | None:
    """Read the logged-in account number from the terminal title, if present."""
    wid = find_terminal_window()
    if wid is None:
        return None
    match = LOGIN_TITLE_RE.search(window_title(wid))
    return match.group(1) if match else None


def gen_email() -> str:
    """Build a unique e-mail per attempt (backstop vs MetaQuotes per-email limits)."""
    return f"auto+{uuid.uuid4().hex[:12]}@example.com"


def wait_for_terminal(timeout: int) -> str | None:
    """Poll until the MT5 terminal window appears, or return None on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        wid = find_terminal_window()
        if wid is not None:
            return wid
        time.sleep(2)
    return None


def screenshot() -> None:
    """Best-effort failure capture; never mask the real error if this fails."""
    try:
        _run(["xwd", "-root", "-silent", "-out", str(FAILURE_SHOT)])
        log(f"saved failure screenshot to {FAILURE_SHOT}")
    except (subprocess.SubprocessError, OSError) as exc:
        log(f"could not capture screenshot: {exc}")


def _activate(wid: str) -> None:
    _xdotool("windowactivate", "--sync", wid)
    time.sleep(STEP_DELAY)


def _key(*keys: str) -> None:
    # Send to the FOCUSED window (no `--window`): Wine menu accelerators only
    # fire for real keyboard focus, so synthetic per-window key events are
    # silently ignored -- this was a root cause of the wizard never opening.
    for k in keys:
        _xdotool("key", k)
        time.sleep(STEP_DELAY)


def _type(text: str) -> None:
    _xdotool("type", "--delay", "80", text)
    time.sleep(STEP_DELAY)


def _click(xy: tuple[int, int]) -> None:
    x, y = xy
    _xdotool("mousemove", str(x), str(y), "click", "1")
    time.sleep(STEP_DELAY)


def run_wizard(wid: str, email: str) -> None:
    """Drive File -> Open an Account -> MetaQuotes demo, end to end.

    Proven against MT5 build 5836 in Wine virtual-desktop (/desktop=) mode on a
    1024x768 display. Menu navigation is by Down-count because the three
    "Open ..." File entries share an ambiguous accelerator; the form is filled by
    clicking each field at its calibrated coordinate because the Tab order skips
    the date-picker and the phone country combo.
    """
    _activate(wid)
    # File menu -> walk down to "Open an Account" -> enter it.
    _key("alt+f")
    for _ in range(MENU_DOWN_TO_OPEN_ACCOUNT):
        _key("Down")
    _key("Return")
    time.sleep(STEP_DELAY * 3)
    # Page 1: explicitly select the MetaQuotes Ltd. row. It is NOT always
    # pre-selected -- a fresh dialog can open with the company list unfocused,
    # leaving Next disabled, which misaligns the entire downstream walk (the
    # form keystrokes then land in the company search box). Click, then advance.
    _click(COMPANY_ROW_XY)
    _key("alt+n")
    time.sleep(STEP_DELAY * 2)
    # Page 2: "Open a demo account" radio is preselected -> Next.
    _key("alt+n")
    time.sleep(STEP_DELAY * 2)
    # Page 3: registration form (click each field; Tab order is unreliable here).
    _click(FIRST_NAME_XY)
    _type(FIRST_NAME)
    _click(LAST_NAME_XY)
    _type(LAST_NAME)
    # Date of birth: click the YEAR segment and overwrite with a past year
    # (month/day default to today, a valid birthday); blank/future year is
    # rejected and keeps Next disabled.
    _click(DOB_YEAR_XY)
    _type(DOB_YEAR)
    _click(EMAIL_XY)
    _type(email)
    # Mobile phone: national number only (the +country code is a separate combo);
    # too many digits turns the field red and blocks Next.
    _click(PHONE_XY)
    _xdotool("key", "ctrl+a")
    _type(PHONE)
    # Tick the terms checkbox (Next stays disabled until it is checked).
    _click(AGREE_XY)
    # Create the account (contacts MetaQuotes), then confirm on the result page.
    _key("alt+n")
    time.sleep(STEP_DELAY * 6)
    _click(FINISH_XY)
    time.sleep(STEP_DELAY * 3)


def write_result(login: str | None, email: str) -> None:
    """Persist the provisioned account (login/server/email, no password) as JSON.

    Written even when the login could not be read back (login=None in /desktop=
    mode): its presence is the idempotency guard that stops the wizard from
    creating a NEW account on every boot (which would hit MetaQuotes rate limits).
    The real login is confirmed at runtime by the gRPC bridge via AccountInfo().
    """
    payload = {
        "login": login,
        "server": SERVER,
        "email": email,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "auto_create_demo_account",
        "login_confirmed": login is not None,
    }
    # Fail loud: if the idempotency file cannot be written (config volume not
    # writable / full disk), that is a real fault, not something to swallow.
    # Re-raise with an actionable message (chain preserved) so the run exits
    # non-zero and the operator fixes the volume -- never pretend success.
    try:
        RESULT_FILE.write_text(json.dumps(payload, indent=2))
    except OSError as exc:
        msg = f"cannot persist {RESULT_FILE}: {exc} -- is the /config volume writable?"
        log(f"FATAL: {msg}")
        raise OSError(msg) from exc
    log(f"wrote {RESULT_FILE} (login={login}, server={SERVER})")


def _wait_for_login(timeout: int) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        login = current_login()
        if login is not None:
            return login
        time.sleep(3)
    return None


def main() -> int:
    """Provision a demo account if needed and return a process exit code."""
    log(f"DISPLAY={DISPLAY} server={SERVER}")

    existing = current_login()
    if existing is not None:
        log(f"terminal already logged in (login={existing}); nothing to do")
        if not RESULT_FILE.exists():
            write_result(existing, os.environ.get("MT5_DEMO_EMAIL", ""))
        return 0
    if RESULT_FILE.exists():
        log(f"{RESULT_FILE} already present; assuming account provisioned")
        return 0

    wid = wait_for_terminal(WINDOW_WAIT)
    if wid is None:
        log(f"ERROR: MT5 terminal window not found within {WINDOW_WAIT}s")
        screenshot()
        return 1

    # Let the first-run LiveUpdate settle, then clear focus-stealing popups so the
    # wizard keystrokes reach the terminal (not the LiveUpdate/web-view window).
    time.sleep(STEP_DELAY * 4)
    _dismiss_popups()
    time.sleep(STEP_DELAY * 2)
    wid = find_terminal_window() or wid

    email = gen_email()
    log(f"driving Open-an-Account wizard (email={email})")
    try:
        run_wizard(wid, email)
    except (subprocess.SubprocessError, OSError) as exc:
        log(f"ERROR: wizard automation failed: {exc}")
        screenshot()
        return 1

    login = _wait_for_login(LOGIN_WAIT)
    if login is None:
        # In Wine /desktop= mode (needed so the wizard renders) the login lives in
        # the in-desktop MT5 title bar, not the X window name, so it often can't
        # be read here. Don't invent a login: the wizard has driven account
        # creation and the gRPC bridge confirms the real account via
        # AccountInfo() at runtime. Keep a screenshot for audit.
        log(
            "wizard completed but login not readable from the desktop title "
            "(expected in /desktop= mode); the gRPC bridge will report the "
            "account via AccountInfo()",
        )
        screenshot()
        # Record the attempt so we do NOT create another account next boot.
        write_result(None, email)
        return 0

    write_result(login, email)
    log(f"demo account ready: login={login} server={SERVER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
