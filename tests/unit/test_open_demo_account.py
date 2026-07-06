"""Unit tests for open_demo_account.py.

Tests cover the helper functions, log parsing, credential persistence and the
main entrypoint of the headless demo-account provisioning script. GUI actions
are mocked at the process-runner boundary.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

    from metatrader import open_demo_account as oda

# The module under test lives inside the container path; add it to sys.path so
# pytest can import the package directly from the workspace.
_CONTAINER_DIR = Path(__file__).resolve().parents[2] / "docker" / "container"
if str(_CONTAINER_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTAINER_DIR))

if not TYPE_CHECKING:
    oda = importlib.import_module("metatrader.open_demo_account")


@pytest.fixture(autouse=True)
def reset_module_env(tmp_path: Path) -> Generator[None]:
    """Isolate module-level paths and env vars for each test."""
    original_config_dir = oda.CONFIG_DIR
    original_result_file = oda.RESULT_FILE
    original_wineprefix = oda.WINEPREFIX
    original_mt5_log_dir = oda.MT5_LOG_DIR
    original_startup_ini = oda.STARTUP_INI
    original_display = os.environ.get("DISPLAY")
    original_module_display = oda.DISPLAY
    original_force_create = oda.FORCE_CREATE

    oda.CONFIG_DIR = tmp_path
    oda.RESULT_FILE = tmp_path / "auto_demo.json"
    oda.WINEPREFIX = tmp_path / ".wine"
    oda.MT5_LOG_DIR = oda.WINEPREFIX / "drive_c/Program Files/MetaTrader 5/logs"
    oda.STARTUP_INI = oda.WINEPREFIX / "drive_c/MT5Config/startup.ini"
    os.environ["DISPLAY"] = ":99"
    oda.DISPLAY = ":99"

    yield

    oda.CONFIG_DIR = original_config_dir
    oda.RESULT_FILE = original_result_file
    oda.WINEPREFIX = original_wineprefix
    oda.MT5_LOG_DIR = original_mt5_log_dir
    oda.STARTUP_INI = original_startup_ini
    oda.DISPLAY = original_module_display
    oda.FORCE_CREATE = original_force_create
    if original_display is None:
        os.environ.pop("DISPLAY", None)
    else:
        os.environ["DISPLAY"] = original_display


@pytest.fixture
def mock_subprocess_run() -> Generator[MagicMock]:
    """Patch the process runner with a controllable mock."""
    with patch(
        "metatrader.open_demo_account.run_process",
        autospec=True,
    ) as mock:
        yield mock


class TestLog:
    """Tests for the log helper."""

    def test_log_prints_prefixed_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Log emits a prefixed line to stdout."""
        oda.log("hello")
        captured = capsys.readouterr()
        assert captured.out == "[open_demo_account] hello\n"


class TestRun:
    """Tests for run_command and the thin wrappers around process execution."""

    def test_run_forces_display_env(self, mock_subprocess_run: MagicMock) -> None:
        """run_command injects DISPLAY into the process environment."""
        mock_subprocess_run.return_value = MagicMock(spec=subprocess.CompletedProcess)
        oda.run_command(["xdotool", "key", "Escape"])
        _, kwargs = mock_subprocess_run.call_args
        assert kwargs["env"]["DISPLAY"] == ":99"
        assert kwargs["capture"] is False

    def test_xdotool_invokes_tool(self, mock_subprocess_run: MagicMock) -> None:
        """run_xdotool builds an xdotool argument list."""
        mock_subprocess_run.return_value = MagicMock(spec=subprocess.CompletedProcess)
        oda.run_xdotool("search", "foo")
        args, _ = mock_subprocess_run.call_args
        assert args[0] == ["xdotool", "search", "foo"]


class TestWindowHelpers:
    """Tests for X11 window discovery helpers."""

    def test_window_title(self, mock_subprocess_run: MagicMock) -> None:
        """window_title returns stripped stdout."""
        mock_subprocess_run.return_value.stdout = "  MetaTrader 5  \n"
        assert oda.window_title("0x1") == "MetaTrader 5"

    def test_find_terminal_window_prefers_title_match(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """find_terminal_window prefers the window whose title contains MetaTrader 5."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="0x1 0x2"),
            MagicMock(stdout="MetaTrader"),
            MagicMock(stdout="MetaTrader 5"),
        ]
        assert oda.find_terminal_window() == "0x2"

    def test_find_terminal_window_falls_back_to_last_id(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """find_terminal_window returns last id when no title match."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="0x1"),
            MagicMock(stdout="Terminal"),
        ]
        assert oda.find_terminal_window() == "0x1"

    def test_find_terminal_window_wine_desktop_fallback(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """find_terminal_window falls back to Wine Desktop window."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=""),
            MagicMock(stdout="0x42"),
        ]
        assert oda.find_terminal_window() == "0x42"

    def test_find_terminal_window_returns_none_when_empty(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """find_terminal_window returns None when no windows are found."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=""),
            MagicMock(stdout=""),
        ]
        assert oda.find_terminal_window() is None

    def test_current_login_from_title(self, mock_subprocess_run: MagicMock) -> None:
        """current_login extracts a 6+ digit account from the window title."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="0x1"),  # find_terminal_window search
            MagicMock(stdout="MetaTrader 5 - 123456"),  # find_terminal_window title
            MagicMock(stdout="MetaTrader 5 - 123456"),  # current_login title
        ]
        assert oda.current_login() == "123456"

    def test_current_login_no_match(self, mock_subprocess_run: MagicMock) -> None:
        """current_login returns None when title has no login."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="0x1"),
            MagicMock(stdout="MetaTrader 5"),
            MagicMock(stdout="MetaTrader 5"),
        ]
        assert oda.current_login() is None

    def test_dismiss_popups_closes_liveupdate(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """_dismiss_popups closes LiveUpdate windows and presses Escape."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="0x10 0 desktop host LiveUpdate Window"),  # wmctrl -l
            MagicMock(stdout=""),  # wmctrl -ic 0x10
            MagicMock(stdout="0x10"),  # xdotool search
            MagicMock(stdout="LiveUpdate Window"),  # window_title 0x10
            MagicMock(stdout=""),  # xdotool key Escape
            MagicMock(stdout=""),  # xdotool key Escape
        ]
        oda.dismiss_popups()
        calls = [c[0][0] for c in mock_subprocess_run.call_args_list]
        assert ["wmctrl", "-ic", "0x10"] in calls
        assert ["xdotool", "key", "--window", "0x10", "Escape"] in calls


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Create the MT5 log directory inside the isolated WINEPREFIX."""
    log_dir = tmp_path / ".wine" / "drive_c/Program Files/MetaTrader 5/logs"
    log_dir.mkdir(parents=True)
    return log_dir


class TestTerminalLog:
    """Tests for terminal log parsing."""

    EXPECTED_TWO_LINES = 2

    def _write_log(self, path: Path, text: str) -> None:
        """Write text as UTF-16-LE with BOM."""
        path.write_bytes(text.encode("utf-16-le"))

    def test_latest_terminal_log_path(self, log_dir: Path) -> None:
        """_latest_terminal_log_path returns the most recent daily log."""
        old_log = log_dir / "20250101.log"
        new_log = log_dir / "20250102.log"
        self._write_log(old_log, "old")
        self._write_log(new_log, "new")
        # Ensure mtime differs.
        old_log.touch()
        time.sleep(0.01)
        new_log.touch()
        assert oda.latest_terminal_log_path() == new_log

    def test_latest_terminal_log_path_empty(self) -> None:
        """_latest_terminal_log_path returns None when no logs exist."""
        assert oda.latest_terminal_log_path() is None

    def test_read_terminal_log_utf16(self, log_dir: Path) -> None:
        """_read_terminal_log decodes a UTF-16 log."""
        log_file = log_dir / "20250101.log"
        self._write_log(log_file, "hello world")
        assert oda.read_terminal_log(log_file) == "hello world"

    def test_read_terminal_log_bad_encoding_raises(self, log_dir: Path) -> None:
        """_read_terminal_log raises RuntimeError for non-UTF-16 logs."""
        log_file = log_dir / "20250101.log"
        log_file.write_bytes(b"not utf16")
        with pytest.raises(RuntimeError, match="not UTF-16"):
            oda.read_terminal_log(log_file)

    def test_terminal_log_cursor(self, log_dir: Path) -> None:
        """_terminal_log_cursor captures path and line count."""
        log_file = log_dir / "20250101.log"
        self._write_log(log_file, "line1\nline2\n")
        cursor = oda.terminal_log_cursor()
        assert cursor is not None
        assert cursor[0] == str(log_file)
        assert cursor[1] == TestTerminalLog.EXPECTED_TWO_LINES

    def test_terminal_log_lines_after_cursor(self, log_dir: Path) -> None:
        """_terminal_log_lines returns only new lines after a cursor."""
        log_file = log_dir / "20250101.log"
        self._write_log(log_file, "line1\nline2\n")
        cursor = oda.terminal_log_cursor()
        self._write_log(log_file, "line1\nline2\nline3\n")
        assert oda.terminal_log_lines(cursor) == ["line3"]

    def test_login_from_terminal_log(self, log_dir: Path) -> None:
        """login_from_terminal_log extracts the last login marker."""
        log_file = log_dir / "20250101.log"
        self._write_log(
            log_file,
            "new demo account '111111' opened\n'222222': authorized on server\n",
        )
        assert oda.login_from_terminal_log() == "222222"

    def test_authorized_login_from_terminal_log_resets_on_restart(
        self,
        log_dir: Path,
    ) -> None:
        """authorized_login_from_terminal_log resets on terminal restart markers."""
        log_file = log_dir / "20250101.log"
        self._write_log(
            log_file,
            "MetaTrader 5 x64 build 1234 started for '111111'\n"
            "'222222': authorized on server\n",
        )
        assert oda.authorized_login_from_terminal_log() == "222222"


class TestClipboardAndPassword:
    """Tests for clipboard parsing and password validation."""

    def test_valid_password_rejects_bad_values(self) -> None:
        """_valid_password enforces length and whitespace constraints."""
        assert oda.valid_password("short") is None
        assert oda.valid_password("has space") is None
        assert oda.valid_password("has\nnewline") is None
        assert oda.valid_password("validpass123") == "validpass123"

    def test_password_from_registration_clipboard(self) -> None:
        """_password_from_registration_clipboard parses the master password."""
        text = "Login: 123456\nPassword: secret123\nInvestor: other"
        assert oda.password_from_registration_clipboard(text) == "secret123"

    def test_password_from_registration_clipboard_invalid(self) -> None:
        """_password_from_registration_clipboard returns None when no valid token."""
        assert oda.password_from_registration_clipboard("no password here") is None

    def test_clipboard_reads_xclip(self, mock_subprocess_run: MagicMock) -> None:
        """_clipboard returns stripped stdout from xclip."""
        mock_subprocess_run.return_value.stdout = "  payload  \n"
        assert oda.clipboard_text() == "payload"

    def test_clipboard_empty_returns_none(self, mock_subprocess_run: MagicMock) -> None:
        """_clipboard returns None for empty output."""
        mock_subprocess_run.return_value.stdout = "   \n"
        assert oda.clipboard_text() is None

    def test_clear_clipboard(self, mock_subprocess_run: MagicMock) -> None:
        """_clear_clipboard pipes an empty string to xclip."""
        oda.clear_clipboard()
        args, kwargs = mock_subprocess_run.call_args
        assert args[0][:3] == ["xclip", "-selection", "clipboard"]
        assert kwargs["input_text"] == ""


class TestCredentials:
    """Tests for credential persistence and result files."""

    def test_persist_credentials_writes_ini(self) -> None:
        """persist_credentials writes the expected startup.ini content."""
        oda.persist_credentials("123456", "secret")
        text = oda.STARTUP_INI.read_text()
        assert "Login=123456" in text
        assert "Password=secret" in text
        assert "Server=MetaQuotes-Demo" in text

    def test_persist_credentials_creates_parent(self) -> None:
        """persist_credentials creates the parent directory when missing."""
        oda.STARTUP_INI.unlink(missing_ok=True)
        oda.persist_credentials("123456", "secret")
        assert oda.STARTUP_INI.exists()

    def test_write_result(self) -> None:
        """write_result persists a JSON result file."""
        oda.write_result("123456", "auto@example.com", persisted=True)
        payload = json.loads(oda.RESULT_FILE.read_text())
        assert payload["login"] == "123456"
        assert payload["email"] == "auto@example.com"
        assert payload["credentials_persisted"] is True
        assert payload["login_confirmed"] is True

    def test_write_result_io_error(self) -> None:
        """write_result raises OSError when the result file cannot be written."""
        oda.RESULT_FILE = oda.CONFIG_DIR / "nonexistent" / "auto_demo.json"
        with pytest.raises(OSError, match="cannot persist"):
            oda.write_result("123456", "auto@example.com")

    def test_result_file_login(self) -> None:
        """_result_file_login returns a confirmed login."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": True})
        )
        assert oda.result_file_login() == "123456"

    def test_result_file_login_unconfirmed(self) -> None:
        """_result_file_login returns None for unconfirmed entries."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": False})
        )
        assert oda.result_file_login() is None

    def test_result_file_login_bad_json(self) -> None:
        """_result_file_login raises RuntimeError for invalid JSON."""
        oda.RESULT_FILE.write_text("not json")
        with pytest.raises(RuntimeError, match="not valid JSON"):
            oda.result_file_login()


class TestMainFlow:
    """Tests for main() orchestration."""

    def test_main_already_logged_in_writes_result(self) -> None:
        """Main exits 0 and writes result when terminal is already logged in."""
        with (
            patch.object(oda, "current_login", return_value="123456"),
            patch.object(oda, "write_result") as write_mock,
        ):
            assert oda.main() == 0
            write_mock.assert_called_once()

    def test_main_confirmed_result_no_action(self) -> None:
        """Main exits 0 when result file already matches authorized session."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": True})
        )
        with (
            patch.object(oda, "current_login", return_value=None),
            patch.object(oda, "confirmed_result_login", return_value="123456"),
        ):
            assert oda.main() == 0

    def test_main_waits_for_terminal_and_provisions(self) -> None:
        """Main provisions a new demo when no existing login is found."""
        oda.FORCE_CREATE = True
        with (
            patch.object(oda, "wait_for_terminal", return_value="0x1"),
            patch.object(oda, "provision_new_demo", return_value=0),
            patch.object(oda, "dismiss_popups"),
            patch.object(oda, "find_terminal_window", return_value="0x1"),
        ):
            assert oda.main() == 0
        oda.FORCE_CREATE = False

    def test_main_terminal_not_found(self) -> None:
        """Main exits 1 when terminal window never appears."""
        oda.FORCE_CREATE = True
        with (
            patch.object(oda, "wait_for_terminal", return_value=None),
            patch.object(oda, "screenshot"),
        ):
            assert oda.main() == 1
        oda.FORCE_CREATE = False


class TestProvisionNewDemo:
    """Tests for provision_new_demo."""

    def test_provision_new_demo_success(self, log_dir: Path) -> None:
        """provision_new_demo succeeds and persists credentials."""
        log_file = log_dir / "20250101.log"
        log_file.write_bytes("".encode("utf-16-le"))
        with (
            patch.object(oda, "run_wizard", return_value="secret"),
            patch.object(
                oda,
                "wait_for_authorized_login",
                return_value="123456",
            ),
            patch.object(oda, "persist_credentials") as persist_mock,
            patch.object(oda, "write_result") as write_mock,
        ):
            assert oda.provision_new_demo("0x1") == 0
            persist_mock.assert_called_once_with("123456", "secret")
            write_mock.assert_called_once()

    def test_provision_new_demo_missing_password(self, log_dir: Path) -> None:
        """provision_new_demo fails when persistence requires a password."""
        log_file = log_dir / "20250101.log"
        log_file.write_bytes("".encode("utf-16-le"))
        oda.PERSIST_CREDS = True
        with (
            patch.object(oda, "run_wizard", return_value=None),
            patch.object(
                oda,
                "wait_for_authorized_login",
                return_value="123456",
            ),
            patch.object(oda, "screenshot"),
        ):
            assert oda.provision_new_demo("0x1") == 1
        oda.PERSIST_CREDS = True  # default value remains True

    def test_provision_new_demo_no_log_cursor(self) -> None:
        """provision_new_demo fails when terminal log cursor is unavailable."""
        with patch.object(oda, "terminal_log_cursor", return_value=None):
            assert oda.provision_new_demo("0x1") == 1


class TestWizardHelpers:
    """Tests for the small GUI automation helpers."""

    def test_screenshot_logs_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Screenshot logs that no screenshot is captured."""
        oda.screenshot()
        captured = capsys.readouterr()
        assert "not captured" in captured.out

    def test_activate(self, mock_subprocess_run: MagicMock) -> None:
        """_activate calls xdotool windowactivate and sleeps."""
        with patch.object(oda.time, "sleep"):
            oda.activate_window("0x1")
        args, _ = mock_subprocess_run.call_args
        assert args[0] == ["xdotool", "windowactivate", "--sync", "0x1"]

    def test_key(self, mock_subprocess_run: MagicMock) -> None:
        """_key sends keys to the focused window."""
        with patch.object(oda.time, "sleep"):
            oda.send_keys("Return")
        args, _ = mock_subprocess_run.call_args
        assert args[0] == ["xdotool", "key", "Return"]

    def test_type(self, mock_subprocess_run: MagicMock) -> None:
        """_type types text with a delay."""
        with patch.object(oda.time, "sleep"):
            oda.type_text("hello")
        args, _ = mock_subprocess_run.call_args
        assert args[0] == ["xdotool", "type", "--delay", "80", "hello"]

    def test_click(self, mock_subprocess_run: MagicMock) -> None:
        """_click moves the mouse and clicks at the given coordinate."""
        with patch.object(oda.time, "sleep"):
            oda.click_at((100, 200))
        args, _ = mock_subprocess_run.call_args
        assert args[0] == ["xdotool", "mousemove", "100", "200", "click", "1"]


class TestCapturePassword:
    """Tests for capture_password_from_final_page."""

    def test_capture_password_success(self, mock_subprocess_run: MagicMock) -> None:
        """capture_password_from_final_page returns the parsed password."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=""),  # clear clipboard
            MagicMock(stdout=""),  # click copy-info link
            MagicMock(stdout="Password: captured123\n"),  # clipboard read
        ]
        assert oda.capture_password_from_final_page() == "captured123"

    def test_capture_password_invalid_payload(
        self,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """capture_password_from_final_page returns None for invalid payload."""
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=""),  # clear clipboard
            MagicMock(stdout=""),  # click copy-info link
            MagicMock(stdout="no password\n"),
        ]
        assert oda.capture_password_from_final_page() is None


class TestGenEmail:
    """Tests for gen_email."""

    def test_gen_email_format(self) -> None:
        """gen_email returns an auto+UUID email."""
        email = oda.gen_email()
        assert email.startswith("auto+")
        assert email.endswith("@example.com")


class TestWaitForTerminal:
    """Tests for wait_for_terminal."""

    def test_wait_for_terminal_finds_window(self) -> None:
        """wait_for_terminal returns the window id when found."""
        with (
            patch.object(oda, "find_terminal_window", side_effect=[None, "0x1"]),
            patch.object(oda.time, "sleep"),
        ):
            assert oda.wait_for_terminal(10) == "0x1"

    def test_wait_for_terminal_timeout(self) -> None:
        """wait_for_terminal returns None on timeout."""
        with (
            patch.object(oda, "find_terminal_window", return_value=None),
            patch.object(oda.time, "sleep"),
        ):
            assert oda.wait_for_terminal(0) is None


class TestConfirmedResultLogin:
    """Tests for confirmed_result_login."""

    def test_confirmed_result_login_matches_title(self) -> None:
        """confirmed_result_login succeeds when title matches result file."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": True})
        )
        with patch.object(oda, "current_login", return_value="123456"):
            assert oda.confirmed_result_login() == "123456"

    def test_confirmed_result_login_matches_log(self) -> None:
        """confirmed_result_login succeeds when terminal log authorizes login."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": True})
        )
        with (
            patch.object(oda, "current_login", return_value=None),
            patch.object(
                oda,
                "authorized_login_from_terminal_log",
                return_value="123456",
            ),
        ):
            assert oda.confirmed_result_login() == "123456"

    def test_confirmed_result_login_mismatch(self) -> None:
        """confirmed_result_login returns None when no active session matches."""
        oda.RESULT_FILE.write_text(
            json.dumps({"login": "123456", "login_confirmed": True})
        )
        with (
            patch.object(oda, "current_login", return_value="999999"),
            patch.object(
                oda,
                "authorized_login_from_terminal_log",
                return_value=None,
            ),
        ):
            assert oda.confirmed_result_login() is None


class TestWaitForLogin:
    """Tests for login polling helpers."""

    def test_wait_for_login_finds_login(self) -> None:
        """_wait_for_login returns login when it appears."""
        with (
            patch.object(oda, "current_login", side_effect=[None, "123456"]),
            patch.object(oda.time, "sleep"),
        ):
            assert oda.wait_for_login(10) == "123456"

    def test_wait_for_login_timeout(self) -> None:
        """_wait_for_login returns None on timeout."""
        with (
            patch.object(oda, "current_login", return_value=None),
            patch.object(oda.time, "sleep"),
        ):
            assert oda.wait_for_login(0) is None

    def test_wait_for_authorized_login_no_cursor(self) -> None:
        """_wait_for_authorized_login errors when cursor is missing."""
        assert oda.wait_for_authorized_login(10, cursor=None) is None

    def test_wait_for_authorized_login_finds(self) -> None:
        """_wait_for_authorized_login returns authorized login."""
        with (
            patch.object(
                oda,
                "authorized_login_from_terminal_log",
                side_effect=[None, "123456"],
            ),
            patch.object(oda.time, "sleep"),
        ):
            assert oda.wait_for_authorized_login(10, cursor=("path", 0)) == "123456"
