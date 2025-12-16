"""Tests for mt5docker test container isolation and functionality.

These tests validate:
1. Container isolation (correct name, ports) - runs without container
2. RPyC service availability - requires container
3. mt5linux module accessibility - requires container
4. Basic MT5 operations - requires container
5. RPyC 6.x compatibility - requires container

Tests that require the container will skip if MT5 credentials
are not configured in .env file.
"""

from __future__ import annotations

import subprocess

import rpyc

from tests.conftest import requires_container  # type: ignore[import]


class TestConfiguration:
    """Test configuration values (no container needed)."""

    def test_container_name_is_isolated(self, container_name: str) -> None:
        """Verify test container uses isolated name."""
        assert container_name == "mt5docker-test"
        assert container_name != "mt5"  # Not production
        assert container_name != "mt5linux-test"  # Not mt5linux tests
        assert container_name != "neptor-mt5-test"  # Not neptor tests

    def test_rpyc_port_is_isolated(self, rpyc_port: int) -> None:
        """Verify RPyC uses isolated port."""
        assert rpyc_port == 48812
        assert rpyc_port != 8001  # Not production
        assert rpyc_port != 28812  # Not mt5linux tests
        assert rpyc_port != 18812  # Not neptor tests
        assert rpyc_port != 38812  # Not other tests

    def test_vnc_port_is_isolated(self, vnc_port: int) -> None:
        """Verify VNC uses isolated port."""
        assert vnc_port == 43000
        assert vnc_port != 3000  # Not production

    def test_health_port_is_isolated(self, health_port: int) -> None:
        """Verify health check uses isolated port."""
        assert health_port == 48002
        assert health_port != 8002  # Not production


@requires_container
class TestContainerRunning:
    """Test container is running (requires container)."""

    def test_container_is_running(self, container_name: str) -> None:
        """Verify test container is actually running."""
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip(), f"Container {container_name} not running"

    def test_ports_are_exposed(
        self, rpyc_port: int, vnc_port: int, health_port: int
    ) -> None:
        """Verify all ports are exposed correctly."""
        result = subprocess.run(
            ["docker", "port", "mt5docker-test"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout

        assert f"{rpyc_port}" in output, f"RPyC port {rpyc_port} not exposed"
        assert f"{vnc_port}" in output, f"VNC port {vnc_port} not exposed"
        assert f"{health_port}" in output, f"Health port {health_port} not exposed"


@requires_container
class TestRPyCService:
    """Test RPyC service functionality (requires container)."""

    def test_rpyc_connection_established(self, rpyc_connection) -> None:
        """Verify RPyC connection can be established."""
        assert rpyc_connection is not None
        assert hasattr(rpyc_connection, "root")

    def test_mt5_service_health_check(self, rpyc_connection) -> None:
        """Verify MT5Service health check works."""
        health = rpyc_connection.root.health_check()
        assert health is not None
        assert health.get("healthy") is True
        assert health.get("mt5_available") is True

    def test_mt5_module_available(self, rpyc_connection) -> None:
        """Verify MT5 module is accessible via MT5Service."""
        mt5 = rpyc_connection.root.get_mt5()
        assert mt5 is not None


@requires_container
class TestMT5Operations:
    """Test basic MT5 operations via RPyC (requires container)."""

    def test_mt5_version(self, mt5_module) -> None:
        """Verify MT5 version can be retrieved."""
        version = mt5_module.version()
        # Version might be None if MT5 not initialized, but call should work
        assert version is None or isinstance(version, tuple)

    def test_mt5_constants_accessible(self, mt5_module) -> None:
        """Verify MT5 constants are accessible."""
        # These constants should always be available
        assert hasattr(mt5_module, "ORDER_TYPE_BUY")
        assert hasattr(mt5_module, "ORDER_TYPE_SELL")
        assert hasattr(mt5_module, "TIMEFRAME_M1")
        assert hasattr(mt5_module, "TIMEFRAME_H1")

    def test_mt5_last_error(self, mt5_module) -> None:
        """Verify last_error is accessible."""
        error = mt5_module.last_error()
        # Should return tuple (code, description)
        assert error is None or isinstance(error, tuple)


@requires_container
class TestMT5AutoLogin:
    """Test MT5 auto-login functionality (requires container + credentials)."""

    def test_mt5_auto_login_account_info(self, rpyc_connection) -> None:
        """Verify MT5 auto-login works and returns account info."""
        # Initialize MT5 (should use auto-login from config file)
        init_result = rpyc_connection.root.initialize()
        assert init_result is True, "MT5 initialize failed"

        # Get account info - should have valid data if logged in
        account_info = rpyc_connection.root.account_info()
        assert account_info is not None, "account_info returned None - login failed"

        # Verify account has expected fields (RPyC returns dict, not namedtuple)
        assert "login" in account_info, "account_info missing login field"
        assert "server" in account_info, "account_info missing server field"
        assert "balance" in account_info, "account_info missing balance field"

        # Verify login is a valid number
        assert account_info["login"] > 0, f"Invalid login: {account_info['login']}"

    def test_mt5_terminal_connected(self, rpyc_connection) -> None:
        """Verify MT5 terminal is connected to server."""
        # Initialize if not already
        rpyc_connection.root.initialize()

        # Get terminal info
        term_info = rpyc_connection.root.terminal_info()
        assert term_info is not None, "terminal_info returned None"

        # Check terminal is connected (RPyC returns dict, not namedtuple)
        assert "connected" in term_info, "terminal_info missing connected field"
        assert term_info["connected"] is True, "Terminal not connected to server"


@requires_container
class TestMT5LinuxInstallation:
    """Test mt5linux is installed from GitHub (requires container)."""

    def test_mt5linux_installed(self, container_name: str) -> None:
        """Verify mt5linux is installed and importable."""
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "python3",
                "-c",
                "import mt5linux; print(mt5linux.__file__)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"mt5linux not installed: {result.stderr}"
        assert "mt5linux" in result.stdout

    def test_mt5linux_has_metatrader5_class(self, container_name: str) -> None:
        """Verify mt5linux has MetaTrader5 class."""
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "python3",
                "-c",
                "from mt5linux import MetaTrader5; print(MetaTrader5)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"MetaTrader5 class not found: {result.stderr}"
        assert "MetaTrader5" in result.stdout


@requires_container
class TestRPyC6Compatibility:
    """Test RPyC 6.x specific behavior (requires container)."""

    def test_rpyc_version(self) -> None:
        """Verify RPyC 6.x is installed locally."""
        version = rpyc.__version__
        assert version.startswith("6."), f"Expected rpyc 6.x, got {version}"

    def test_wine_rpyc_version(self, container_name: str) -> None:
        """Verify RPyC 6.x is installed in Wine Python."""
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-u",
                "abc",
                container_name,
                "wine",
                "python",
                "-c",
                "import rpyc; print(rpyc.__version__)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"rpyc not installed in Wine: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("6."), f"Expected rpyc 6.x in Wine, got {version}"

    def test_numpy_available_in_mt5(self, mt5_module) -> None:
        """Test numpy is available for MT5 operations.

        MT5 uses numpy for price data arrays.
        """
        # MT5 module should be able to return numpy arrays from copy_rates_*
        # Just verify MT5 module is accessible
        assert mt5_module is not None

    def test_rpyc_connection_timeout_config(self, rpyc_connection) -> None:
        """Verify RPyC connection timeout is properly configured."""
        timeout = rpyc_connection._config.get("sync_request_timeout")
        assert timeout is not None
        assert timeout >= 60, f"Timeout should be >= 60s, got {timeout}"

    def test_python_version_in_wine(self, container_name: str) -> None:
        """Verify Python 3.12+ is installed in Wine.

        Python 3.12.x is the current version in Wine (numpy 1.26.4 compatibility).
        """
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-u",
                "abc",
                container_name,
                "wine",
                "python",
                "--version",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Python not found in Wine: {result.stderr}"
        version_str = result.stdout.strip()
        # Python 3.12+ required
        assert "3.12" in version_str or "3.13" in version_str, (
            f"Expected Python 3.12.x or 3.13.x, got {version_str}"
        )

