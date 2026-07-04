"""Headless MetaQuotes demo-account provisioning for the MT5 terminal under Wine.

Drives the terminal's ``File -> Open an Account`` wizard via ``xdotool`` on the
Xvfb display so the container can create a demo account with ZERO human
interaction.

Design (real authorization, no OCR):
  * After the wizard finishes the MT5 terminal is LOGGED IN to the new demo
    account. The script confirms that live authorization from the terminal log
    before writing ``auto_demo.json``.
  * The account login is read from the terminal LOG (``new demo account 'NNNN'
    opened`` / ``'NNNN': authorized``) -- authoritative in /desktop= mode where
    the X window title does NOT carry the login -- with the title as a fast
    fallback. No OCR.
  * Idempotent: if the terminal is already logged in or ``auto_demo.json``
    matches a currently authorized login, this is a no-op.

RESTART-SURVIVAL (login persists across container/terminal restart): the MT5
terminal re-reads ``startup.ini`` and re-attempts login on EVERY boot, so a
restart survives the login IFF ``startup.ini`` carries a valid Login+Password.
Two paths: (a) supply ``MT5_LOGIN/PASSWORD/SERVER`` -> generate_mt5_config
writes them -> survives restart today; (b) zero-touch auto-demo -> the wizard
captures the MetaQuotes-GENERATED password from the final page and persists
Login+Password+Server to startup.ini.

FRAGILITY: this is GUI automation against a moving target. The keystroke
sequence and the waits may need tuning across MT5 builds/locales. Failure paths
exit non-zero without persisting GUI screenshots because the wizard can display
generated credentials on screen. All timings and form values are env-overridable
(see the CONFIG block) so the build can be adjusted without code changes.
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
from typing import cast

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

# Configuration. Every value below can be overridden via an environment variable.
DISPLAY = os.environ.get("DISPLAY", ":0")
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
RESULT_FILE = CONFIG_DIR / "auto_demo.json"

# MT5 writes a per-day terminal log here; it is the AUTHORITATIVE source of the
# new account's login (the X window title does NOT carry it in /desktop= mode).
WINEPREFIX = Path(os.environ.get("WINEPREFIX", str(CONFIG_DIR / ".wine")))
MT5_LOG_DIR = WINEPREFIX / "drive_c/Program Files/MetaTrader 5/logs"
# The terminal auto-login config: the terminal RE-READS this on every boot, so
# writing Login+Password here makes the demo SURVIVE restart (relogin). Must
# match the layout generate_mt5_config writes in setup.sh.
STARTUP_INI = WINEPREFIX / "drive_c/MT5Config/startup.ini"
# Persist the captured demo credentials for restart-survival (default on).
PERSIST_CREDS = os.environ.get("MT5_DEMO_PERSIST_CREDS", "1") == "1"
FORCE_CREATE = os.environ.get("MT5_DEMO_FORCE_CREATE", "0") == "1"
# A real MT5 master password is a short single-line token; anything outside this
# length range is a wrong-field / whole-page copy and must be rejected.
PW_MIN_LEN = 6
PW_MAX_LEN = 32

SERVER = os.environ.get("MT5_DEMO_SERVER", "MetaQuotes-Demo")
FIRST_NAME = os.environ.get("MT5_DEMO_FIRST", "Auto")
LAST_NAME = os.environ.get("MT5_DEMO_LAST", "Trader")
WINDOW_WAIT = int(os.environ.get("MT5_DEMO_WINDOW_WAIT", "120"))
LOGIN_WAIT = int(os.environ.get("MT5_DEMO_LOGIN_WAIT", "60"))
STEP_DELAY = float(os.environ.get("MT5_DEMO_STEP_DELAY", "1.5"))

# Wizard layout, calibrated for a 1024x768 KasmVNC display with the terminal in
# Wine virtual-desktop (/desktop=) mode -- the mode that makes MT5 menus/dialogs
# render instead of black. The values are root-window pixel coordinates.
DOB_YEAR = os.environ.get("MT5_DEMO_DOB_YEAR", "1990")
PHONE = os.environ.get("MT5_DEMO_PHONE", "11988887777")


def _xy_env(name: str, default: tuple[int, int]) -> tuple[int, int]:
    """Read a calibrated x,y coordinate from the environment."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    x_raw, y_raw = raw.split(",", maxsplit=1)
    return int(x_raw), int(y_raw)


FILE_MENU_XY = _xy_env("MT5_DEMO_FILE_MENU_XY", (22, 42))
OPEN_ACCOUNT_MENU_XY = _xy_env("MT5_DEMO_OPEN_ACCOUNT_MENU_XY", (85, 344))
COMPANY_ROW_XY = _xy_env("MT5_DEMO_COMPANY_ROW_XY", (300, 271))
FIRST_NAME_XY = _xy_env("MT5_DEMO_FIRST_NAME_XY", (366, 229))
LAST_NAME_XY = _xy_env("MT5_DEMO_LAST_NAME_XY", (366, 257))
DOB_YEAR_XY = _xy_env("MT5_DEMO_DOB_YEAR_XY", (392, 287))
EMAIL_XY = _xy_env("MT5_DEMO_EMAIL_XY", (420, 328))
PHONE_XY = _xy_env("MT5_DEMO_PHONE_XY", (500, 357))
AGREE_XY = _xy_env("MT5_DEMO_AGREE_XY", (299, 545))
NEXT_XY = _xy_env("MT5_DEMO_NEXT_XY", (714, 636))
FINISH_XY = _xy_env("MT5_DEMO_FINISH_XY", (714, 636))
# Final (result) page: the "Copy the registration information to clipboard"
# link copies the generated login/master/investor credentials exactly. We parse
# the master password from that clipboard payload (xclip, no OCR).
COPY_INFO_XY = _xy_env("MT5_DEMO_COPY_INFO_XY", (405, 489))

# A logged-in MT5 window title carries the account number (>= 6 digits).
LOGIN_TITLE_RE = re.compile(r"\b(\d{6,})\b")

# MT5 terminal-log markers for the demo account login (authoritative in
# /desktop= mode). "new demo account 'NNNN' opened" is written once at creation;
# "'NNNN': authorized" is written on every successful (re)login.
LOG_NEW_ACCOUNT_RE = re.compile(r"new demo account '(\d+)' opened")
LOG_AUTHORIZED_RE = re.compile(r"'(\d+)': authorized on")
TERMINAL_DAILY_LOG_RE = re.compile(r"\d{8}\.log")

LogCursor = tuple[str, int]


def log(msg: str) -> None:
    """Emit a structured-ish line to stdout (captured by the container logs)."""
    print(f"[open_demo_account] {msg}", flush=True)  # noqa: T201


def _run(
    args: list[str],
    *,
    capture: bool = False,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a local X11 tool, always forcing DISPLAY for the headless server."""
    return subprocess.run(  # noqa: S603
        args,
        check=False,
        text=True,
        input=input_text,
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


def _latest_terminal_log_path() -> Path | None:
    """Return the latest daily MT5 terminal log, ignoring MetaEditor logs."""
    try:
        logs = [
            path
            for path in MT5_LOG_DIR.glob("*.log")
            if TERMINAL_DAILY_LOG_RE.fullmatch(path.name)
        ]
    except OSError as exc:
        log(f"could not list terminal logs at {MT5_LOG_DIR}: {exc}")
        return None
    if not logs:
        return None
    return max(logs, key=lambda path: path.stat().st_mtime)


def _read_terminal_log(path: Path) -> str:
    """Read an MT5 terminal log, decoded as UTF-16."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        msg = f"could not read terminal log {path}: {exc}"
        log(f"FATAL: {msg}")
        raise OSError(msg) from exc
    # MT5 terminal logs are UTF-16-LE (BOM). Decode STRICTLY -- no utf-8 fallback:
    # a decode failure means the log format actually changed, which must surface
    # loudly (the operator fixes the parser) rather than be masked by a degraded
    # read that silently returns the wrong/no login.
    try:
        text = raw.decode("utf-16")
    except UnicodeDecodeError as exc:
        msg = f"MT5 terminal log {path} is not UTF-16 as expected: {exc}"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg) from exc
    return text


def _latest_terminal_log_text() -> str | None:
    """Return the latest MT5 terminal log text, decoded as UTF-16."""
    path = _latest_terminal_log_path()
    return None if path is None else _read_terminal_log(path)


def _terminal_log_cursor() -> LogCursor | None:
    """Capture the current terminal-log position before starting the wizard."""
    path = _latest_terminal_log_path()
    if path is None:
        return None
    return str(path), len(_read_terminal_log(path).splitlines())


def _terminal_log_lines(cursor: LogCursor | None = None) -> list[str]:
    """Return terminal-log lines, optionally only lines written after a cursor."""
    path = _latest_terminal_log_path()
    if path is None:
        return []
    lines = _read_terminal_log(path).splitlines()
    if cursor is None:
        return lines
    cursor_path, cursor_count = cursor
    if str(path) != cursor_path:
        return lines
    return lines[cursor_count:]


def login_from_terminal_log() -> str | None:
    """Read the demo login from the MT5 terminal log (authoritative source).

    In Wine ``/desktop=`` mode the account number is NOT exposed on the X window
    title, so the title scrape returns nothing. The terminal log, however, always
    records ``... new demo account 'NNNN' opened ...`` at creation and
    ``... 'NNNN': authorized ...`` on each login. We scan the most recent log and
    return the LAST login seen (handles a relogin after creation). Returns None if
    the log is absent/unreadable -- never invents a value.
    """
    login: str | None = None
    for line in _terminal_log_lines():
        match = LOG_NEW_ACCOUNT_RE.search(line) or LOG_AUTHORIZED_RE.search(line)
        if match:
            login = match.group(1)
    return login


def authorized_login_from_terminal_log(cursor: LogCursor | None = None) -> str | None:
    """Read the last account that the terminal actively authorized."""
    login: str | None = None
    for line in _terminal_log_lines(cursor):
        line_lower = line.lower()
        if "metatrader 5 x64 build" in line_lower and "started for" in line_lower:
            login = None
            continue
        if "authorization" in line_lower and "failed" in line_lower:
            login = None
            continue
        match = LOG_AUTHORIZED_RE.search(line)
        if match:
            login = match.group(1)
    return login


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
    """Record that no GUI screenshot was persisted because it may contain secrets."""
    log(
        "failure screenshot not captured because the MT5 wizard may display credentials"
    )


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


def _clipboard() -> str | None:
    """Read the X clipboard via xclip; None if empty/unavailable."""
    res = _run(["xclip", "-selection", "clipboard", "-o"], capture=True)
    text = res.stdout.strip()
    return text or None


def _clear_clipboard() -> None:
    """Clear stale clipboard content before clicking MT5's copy link."""
    _run(["xclip", "-selection", "clipboard"], input_text="")


def _valid_password(password: str) -> str | None:
    """Return a password only when it has the expected MT5 token shape."""
    if (
        "\n" in password
        or " " in password
        or not (PW_MIN_LEN <= len(password) <= PW_MAX_LEN)
    ):
        return None
    return password


def _password_from_registration_clipboard(text: str) -> str | None:
    """Extract the master password from MT5's copied registration payload."""
    for line in text.splitlines():
        match = re.match(r"(?i)^\s*password\s*[:\t ]+\s*(\S+)\s*$", line)
        if match:
            return _valid_password(match.group(1))
    return None


def capture_password_from_final_page() -> str | None:
    """Copy the master password from the wizard's result page (no OCR).

    The MetaQuotes result page exposes a "Copy the registration information to
    clipboard" link. Use that exact UI surface, then parse the master password
    from the clipboard text. The raw clipboard is never logged.
    """
    _clear_clipboard()
    _click(COPY_INFO_XY)
    time.sleep(STEP_DELAY)
    clipboard = _clipboard()
    if clipboard is None:
        return None
    password = _password_from_registration_clipboard(clipboard)
    if password is None:
        log(
            "clipboard registration payload did not include a valid master "
            f"password token (len={len(clipboard)})",
        )
        return None
    return password


def persist_credentials(login: str, password: str) -> None:
    """Persist Login+Password+Server to startup.ini for restart-survival.

    The terminal RE-READS startup.ini on every boot, so writing the credentials
    here makes the auto-created demo survive a restart. Fail loud on I/O error
    (the /config volume must be writable); never pretend success. Mirrors the
    [Common]/[Experts] layout generate_mt5_config writes.
    """
    ini = (
        "[Common]\n"
        f"Login={login}\n"
        f"Password={password}\n"
        f"Server={SERVER}\n"
        "KeepPrivate=1\n"
        "NewsEnable=1\n"
        "\n"
        "[Experts]\n"
        "AllowLiveTrading=1\n"
        "AllowDllImport=1\n"
        "Enabled=1\n"
        "Account=0\n"
        "Profile=0\n"
    )
    try:
        STARTUP_INI.parent.mkdir(parents=True, exist_ok=True)
        STARTUP_INI.write_text(ini)
    except OSError as exc:
        msg = f"cannot persist credentials to {STARTUP_INI}: {exc}"
        log(f"FATAL: {msg}")
        raise OSError(msg) from exc
    log(f"persisted credentials to {STARTUP_INI} (survives restart)")


def run_wizard(wid: str, email: str) -> str | None:
    """Drive File -> Open an Account -> MetaQuotes demo; return the password.

    Proven against MT5 build 5973 in Wine virtual-desktop (/desktop=) mode on a
    1024x768 display. Menu navigation uses calibrated clicks because Wine does
    not deliver the File-menu accelerator reliably to the virtual desktop; the
    form is filled by clicking each field at its calibrated coordinate because
    the Tab order skips the date-picker and the phone country combo. Returns the
    MetaQuotes-generated master password captured from the result page (None if
    capture is disabled or the field yielded nothing) so the caller can persist
    it for restart-survival.
    """
    _activate(wid)
    # File -> Open an Account. The keyboard accelerator does not open the menu
    # under Wine /desktop= in the real container, so use calibrated clicks.
    _click(FILE_MENU_XY)
    _click(OPEN_ACCOUNT_MENU_XY)
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
    # Create the account (contacts MetaQuotes). The result page then shows the
    # login + master/investor passwords. Capture the master password BEFORE
    # Finish dismisses the page -- this is the ONLY place it is ever shown.
    _key("alt+n")
    time.sleep(STEP_DELAY * 6)
    password = capture_password_from_final_page() if PERSIST_CREDS else None
    _click(FINISH_XY)
    time.sleep(STEP_DELAY * 3)
    return password


def write_result(login: str, email: str, *, persisted: bool = False) -> None:
    """Persist the provisioned account (login/server/email, no password) as JSON.

    Written only after the terminal has confirmed a live authorized login.
    ``credentials_persisted`` records whether Login+Password were written to
    startup.ini (i.e. whether the demo survives a restart). The password itself
    is NEVER stored here.
    """
    payload = {
        "login": login,
        "server": SERVER,
        "email": email,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "auto_create_demo_account",
        "login_confirmed": True,
        "credentials_persisted": persisted,
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
    log(f"wrote {RESULT_FILE} (server_present={bool(SERVER)})")


def _result_file_login() -> str | None:
    """Read a confirmed login from auto_demo.json, or None when it is stale."""
    try:
        raw_payload = cast("JsonValue", json.loads(RESULT_FILE.read_text()))
    except json.JSONDecodeError as exc:
        msg = f"{RESULT_FILE} is not valid JSON: {exc}"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg) from exc
    except OSError as exc:
        msg = f"cannot read {RESULT_FILE}: {exc}"
        log(f"FATAL: {msg}")
        raise OSError(msg) from exc
    if not isinstance(raw_payload, dict):
        log(f"{RESULT_FILE} is not an object; provisioning will run again")
        return None

    login = raw_payload.get("login")
    login_confirmed = raw_payload.get("login_confirmed")
    if isinstance(login, str) and login and login_confirmed is True:
        return login

    log(f"{RESULT_FILE} does not contain a confirmed login")
    return None


def confirmed_result_login() -> str | None:
    """Return the marker login only when the current terminal confirms it."""
    marker_login = _result_file_login()
    if marker_login is None:
        return None

    active_login = current_login()
    if active_login == marker_login:
        return marker_login

    authorized_login = authorized_login_from_terminal_log()
    if authorized_login == marker_login:
        return marker_login

    log(
        f"{RESULT_FILE} is not authorized by the current terminal session; "
        "provisioning will run again",
    )
    return None


def _wait_for_login(timeout: int) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        login = current_login()
        if login is not None:
            return login
        time.sleep(3)
    return None


def _wait_for_authorized_login(
    timeout: int,
    *,
    cursor: LogCursor | None = None,
) -> str | None:
    """Poll until the terminal confirms a live authorized login."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cursor is None:
            log(
                "ERROR: cannot verify current-run authorization "
                "without terminal log cursor",
            )
            return None
        login = authorized_login_from_terminal_log(cursor)
        if login is not None:
            return login
        time.sleep(3)
    return None


def provision_new_demo(wid: str) -> int:
    """Drive the wizard and persist only a confirmed, restart-surviving account."""
    email = gen_email()
    log("driving Open-an-Account wizard (email generated)")
    log_cursor = _terminal_log_cursor()
    if log_cursor is None:
        log("ERROR: terminal log cursor unavailable; cannot prove current-run login")
        return 1
    try:
        password = run_wizard(wid, email)
    except (subprocess.SubprocessError, OSError) as exc:
        log(f"ERROR: wizard automation failed: {exc}")
        screenshot()
        return 1

    # Prefer the X title (instant when present); in /desktop= mode it is empty, so
    # fall back to the terminal log's explicit "authorized" marker.
    login = _wait_for_authorized_login(LOGIN_WAIT, cursor=log_cursor)
    if login is None:
        log(
            "ERROR: wizard completed without a terminal-authorized login; "
            "not writing auto_demo.json",
        )
        screenshot()
        return 1

    # Persist Login+Password so the demo SURVIVES a restart (terminal re-reads
    # startup.ini each boot). If persistence is enabled, a missing password is a
    # real provisioning failure because restart-survival was requested.
    persisted = False
    if PERSIST_CREDS and password:
        persist_credentials(login, password)
        persisted = True
    elif PERSIST_CREDS:
        log(
            "ERROR: master password not captured from the result page; "
            "not writing auto_demo.json because restart-survival is required",
        )
        screenshot()
        return 1
    write_result(login, email, persisted=persisted)
    log(f"demo ready: server_present={bool(SERVER)} survives_restart={persisted}")
    return 0


def main() -> int:
    """Provision a demo account if needed and return a process exit code."""
    log(f"DISPLAY={DISPLAY} server_present={bool(SERVER)}")

    if not FORCE_CREATE:
        existing = current_login()
        if existing is not None:
            log("terminal already logged in; nothing to do")
            if not RESULT_FILE.exists():
                write_result(existing, os.environ.get("MT5_DEMO_EMAIL", ""))
            return 0
        if RESULT_FILE.exists():
            confirmed_login = confirmed_result_login()
            if confirmed_login is not None:
                log(
                    f"{RESULT_FILE} already matches the authorized terminal session; "
                    "nothing to do",
                )
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

    return provision_new_demo(wid)


if __name__ == "__main__":
    sys.exit(main())
