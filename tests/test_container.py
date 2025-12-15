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
        # MetaTrader5 module should be accessible
        mt5 = rpyc_connection.modules.MetaTrader5
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

    def test_numpy_array_transfer(self, rpyc_connection) -> None:
        """Test numpy array data transfer using modern RPyC 6.x pattern.

        RPyC 6.x blocks __array__ access for security.
        Use tolist() on remote to transfer data without rpyc.classic.
        """
        np = rpyc_connection.modules.numpy
        remote_array = np.array([1, 2, 3])
        # Modern RPyC 6.x: Convert to list on remote side, then transfer
        local_list = remote_array.tolist()
        assert local_list == [1, 2, 3]

    def test_rpyc_connection_timeout_config(self, rpyc_connection) -> None:
        """Verify RPyC connection timeout is properly configured."""
        timeout = rpyc_connection._config.get("sync_request_timeout")  # noqa: SLF001
        assert timeout is not None
        assert timeout >= 60, f"Timeout should be >= 60s, got {timeout}"

    def test_python_version_in_wine(self, container_name: str) -> None:
        """Verify Python 3.12+ is installed in Wine.

        Note: Fresh installs get Python 3.13.11 from Dockerfile.
        Existing volumes may have Python 3.12.x from previous builds.
        Both are supported for RPyC 6.x operations.
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
        # Accept 3.12+ (existing volumes) or 3.13+ (fresh installs)
        assert "3.12" in version_str or "3.13" in version_str, (
            f"Expected Python 3.12.x or 3.13.x, got {version_str}"
        )

    def test_pydantic_in_wine(self, container_name: str) -> None:
        """Verify Pydantic 2 is installed in Wine Python."""
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
                "import pydantic; print(pydantic.__version__)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"Pydantic not installed in Wine: {result.stderr}"
        )
        version = result.stdout.strip()
        assert version.startswith("2."), f"Expected Pydantic 2.x, got {version}"
