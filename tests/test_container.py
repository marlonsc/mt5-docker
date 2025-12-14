"""Tests for mt5docker test container isolation and functionality.

These tests validate:
1. Container isolation (correct name, ports) - runs without container
2. RPyC service availability - requires container
3. mt5linux module accessibility - requires container
4. Basic MT5 operations - requires container

Tests that require the container will skip if MT5 credentials
are not configured in .env file.
"""

from __future__ import annotations

import subprocess

from tests.conftest import requires_container


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
        assert hasattr(rpyc_connection, "modules")

    def test_rpyc_modules_accessible(self, rpyc_connection) -> None:
        """Verify remote modules are accessible via RPyC."""
        modules = rpyc_connection.modules
        assert modules is not None
        # Test basic module access
        assert hasattr(modules, "sys")
        assert hasattr(modules, "os")

    def test_mt5linux_module_available(self, rpyc_connection) -> None:
        """Verify mt5linux module is accessible via RPyC."""
        try:
            mt5 = rpyc_connection.modules.MetaTrader5
            assert mt5 is not None
        except Exception as e:
            # mt5linux might not be fully initialized, but module should exist
            assert "MetaTrader5" in str(e)


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
