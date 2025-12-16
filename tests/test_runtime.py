"""Runtime tests - require Docker container to be running.

These tests validate container functionality, services, and MT5 operations.
They require the test container (mt5docker-test) to be running.

Tests will automatically skip if:
- SKIP_DOCKER=1 environment variable is set
- MT5 credentials are not configured in .env

Categories:
- ContainerHealth: Container is running and healthy
- PortExposure: All ports are correctly exposed
- RPyCService: RPyC server functionality
- WinePython: Python environment in Wine
- LinuxPython: Python environment in Linux
- MT5Integration: MetaTrader 5 functionality
- ServiceSupervision: S6-overlay service management
"""

from __future__ import annotations

import re
import subprocess
from typing import Any

import pytest
import rpyc

# =============================================================================
# CONSTANTS
# =============================================================================

# Startup scripts to test in container
CONTAINER_STARTUP_SCRIPTS = [
    "/Metatrader/scripts/00_env.sh",
    "/Metatrader/scripts/05_config_unpack.sh",
    "/Metatrader/scripts/10_prefix_init.sh",
    "/Metatrader/scripts/20_winetricks.sh",
    "/Metatrader/scripts/30_mt5.sh",
    "/Metatrader/scripts/50_copy_bridge.sh",
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def docker_exec(
    container: str,
    command: list[str],
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute command in container."""
    cmd = ["docker", "exec"]
    if user:
        cmd.extend(["-u", user])
    cmd.append(container)
    cmd.extend(command)

    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def wine_python(container: str, code: str) -> subprocess.CompletedProcess[str]:
    """Execute Python code in Wine Python."""
    return docker_exec(container, ["wine", "python", "-c", code], user="abc")


def linux_python(container: str, code: str) -> subprocess.CompletedProcess[str]:
    """Execute Python code in Linux Python."""
    return docker_exec(container, ["python3", "-c", code])


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string to tuple for comparison."""
    # Handle versions like "6.0.2", "1.26.4", "3.12.8"
    parts = re.findall(r"\d+", version_str)
    return tuple(int(p) for p in parts[:3])


# =============================================================================
# CONTAINER HEALTH TESTS
# =============================================================================


class TestContainerHealth:
    """Test container is running and healthy."""

    def test_container_is_running(self, container_name: str) -> None:
        """Verify test container is running."""
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip(), f"Container {container_name} not running"

    def test_container_has_correct_name(self, container_name: str) -> None:
        """Verify container uses isolated test name."""
        assert container_name == "mt5docker-test", "Must use test container name"
        assert container_name != "mt5", "Must not use production container"

    def test_container_healthcheck_passing(self, container_name: str) -> None:
        """Verify container healthcheck is passing."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Health.Status}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        status = result.stdout.strip()
        assert status == "healthy", f"Container health status: {status}"

    def test_container_not_restarting(self, container_name: str) -> None:
        """Verify container is not in restart loop."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.RestartCount}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        restart_count = int(result.stdout.strip())
        assert restart_count < 3, f"Container restarted {restart_count} times"


# =============================================================================
# PORT EXPOSURE TESTS
# =============================================================================


class TestPortExposure:
    """Test all ports are correctly exposed."""

    def test_rpyc_port_exposed(self, container_name: str, rpyc_port: int) -> None:
        """Verify RPyC port is exposed."""
        result = subprocess.run(
            ["docker", "port", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert f"{rpyc_port}" in result.stdout, f"RPyC port {rpyc_port} not exposed"

    def test_vnc_port_exposed(self, container_name: str, vnc_port: int) -> None:
        """Verify VNC port is exposed."""
        result = subprocess.run(
            ["docker", "port", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert f"{vnc_port}" in result.stdout, f"VNC port {vnc_port} not exposed"

    def test_health_port_exposed(self, container_name: str, health_port: int) -> None:
        """Verify health port is exposed."""
        result = subprocess.run(
            ["docker", "port", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert (
            f"{health_port}" in result.stdout
        ), f"Health port {health_port} not exposed"

    def test_ports_are_isolated(
        self, rpyc_port: int, vnc_port: int, health_port: int
    ) -> None:
        """Verify test ports don't conflict with production."""
        # Production ports
        prod_ports = {8001, 3000, 8002}
        test_ports = {rpyc_port, vnc_port, health_port}

        assert (
            not prod_ports & test_ports
        ), "Test ports must not overlap with production"


# =============================================================================
# RPYC SERVICE TESTS
# =============================================================================


class TestRPyCService:
    """Test RPyC service functionality."""

    def test_rpyc_connection_established(
        self, rpyc_connection: rpyc.Connection
    ) -> None:
        """Verify RPyC connection can be established."""
        assert rpyc_connection is not None
        assert hasattr(rpyc_connection, "root")

    def test_rpyc_health_check_returns_healthy(
        self, rpyc_connection: rpyc.Connection
    ) -> None:
        """Verify RPyC health check returns healthy status."""
        root = rpyc_connection.root
        assert root is not None, "RPyC root is None"
        health = root.health_check()

        assert health is not None, "health_check returned None"
        assert health.get("healthy") is True, "Service not healthy"
        assert health.get("mt5_available") is True, "MT5 not available"

    def test_rpyc_get_mt5_returns_module(
        self, rpyc_connection: rpyc.Connection
    ) -> None:
        """Verify get_mt5() returns MT5 module."""
        root = rpyc_connection.root
        assert root is not None, "RPyC root is None"
        mt5 = root.get_mt5()
        assert mt5 is not None, "get_mt5() returned None"

    def test_rpyc_timeout_configured(self, rpyc_connection: rpyc.Connection) -> None:
        """Verify RPyC timeout is properly configured."""
        timeout = rpyc_connection._config.get("sync_request_timeout")
        assert timeout is not None, "Timeout not configured"
        assert isinstance(
            timeout, int | float
        ), f"Invalid timeout type: {type(timeout)}"
        assert timeout >= 60, f"Timeout too short: {timeout}s"


# =============================================================================
# WINE PYTHON TESTS
# =============================================================================


class TestWinePython:
    """Test Python environment in Wine."""

    def test_wine_python_version(self, container_name: str) -> None:
        """Verify Python 3.12.x is installed in Wine."""
        result = docker_exec(
            container_name, ["wine", "python", "--version"], user="abc"
        )

        assert result.returncode == 0, f"Python not found in Wine: {result.stderr}"
        version = result.stdout.strip()
        assert "3.12" in version, f"Expected Python 3.12.x, got {version}"

    def test_wine_rpyc_version(self, container_name: str) -> None:
        """Verify RPyC 6.x is installed in Wine Python."""
        result = wine_python(container_name, "import rpyc; print(rpyc.__version__)")

        assert result.returncode == 0, f"rpyc not installed: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("6."), f"Expected rpyc 6.x, got {version}"

    def test_wine_numpy_version(self, container_name: str) -> None:
        """Verify numpy 1.26.x is installed in Wine Python."""
        result = wine_python(container_name, "import numpy; print(numpy.__version__)")

        assert result.returncode == 0, f"numpy not installed: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("1.26"), f"Expected numpy 1.26.x, got {version}"

    def test_wine_plumbum_version(self, container_name: str) -> None:
        """Verify plumbum >= 1.8.0 is installed in Wine Python."""
        code = "import plumbum; print(plumbum.__version__)"
        result = wine_python(container_name, code)

        assert result.returncode == 0, f"plumbum not installed: {result.stderr}"
        version = result.stdout.strip()
        parsed = parse_version(version)
        assert parsed >= (1, 8, 0), f"Expected plumbum >= 1.8.0, got {version}"

    def test_wine_metatrader5_installed(self, container_name: str) -> None:
        """Verify MetaTrader5 package is installed in Wine Python."""
        result = wine_python(
            container_name, "import MetaTrader5; print(MetaTrader5.__version__)"
        )

        assert result.returncode == 0, f"MetaTrader5 not installed: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("5."), f"Expected MT5 5.x, got {version}"

    def test_wine_structlog_installed(self, container_name: str) -> None:
        """Verify structlog is installed in Wine Python."""
        code = "import structlog; print(structlog.__version__)"
        result = wine_python(container_name, code)

        assert result.returncode == 0, f"structlog not installed: {result.stderr}"


# =============================================================================
# LINUX PYTHON TESTS
# =============================================================================


class TestLinuxPython:
    """Test Python environment in Linux."""

    def test_linux_python_available(self, container_name: str) -> None:
        """Verify Python 3 is available in Linux."""
        result = docker_exec(container_name, ["python3", "--version"])

        assert result.returncode == 0, f"Python3 not found: {result.stderr}"
        assert "Python 3" in result.stdout

    def test_bridge_py_exists_in_container(self, container_name: str) -> None:
        """Verify bridge.py exists at /Metatrader/bridge.py."""
        result = subprocess.run(
            ["docker", "exec", container_name, "test", "-f", "/Metatrader/bridge.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, "bridge.py not found at /Metatrader/bridge.py"

    def test_linux_rpyc_installed(self, container_name: str) -> None:
        """Verify rpyc is installed in Linux Python."""
        result = linux_python(container_name, "import rpyc; print(rpyc.__version__)")

        assert result.returncode == 0, f"rpyc not installed: {result.stderr}"
        assert result.stdout.strip().startswith("6.")

    def test_linux_numpy_installed(self, container_name: str) -> None:
        """Verify numpy is installed in Linux Python."""
        result = linux_python(container_name, "import numpy; print(numpy.__version__)")

        assert result.returncode == 0, f"numpy not installed: {result.stderr}"


# =============================================================================
# MT5 INTEGRATION TESTS
# =============================================================================


class TestMT5Integration:
    """Test MetaTrader 5 integration."""

    def test_mt5_module_accessible(self, mt5_module: Any) -> None:
        """Verify MT5 module is accessible via RPyC."""
        assert mt5_module is not None

    def test_mt5_version_callable(self, mt5_module: Any) -> None:
        """Verify MT5 version() is callable."""
        version = mt5_module.version()
        # May be None if not initialized, but should not raise
        assert version is None or isinstance(version, tuple)

    def test_mt5_last_error_callable(self, mt5_module: Any) -> None:
        """Verify MT5 last_error() is callable."""
        error = mt5_module.last_error()
        assert error is None or isinstance(error, tuple)

    def test_mt5_constants_accessible(self, mt5_module: Any) -> None:
        """Verify MT5 trading constants are accessible."""
        # Order types
        assert hasattr(mt5_module, "ORDER_TYPE_BUY")
        assert hasattr(mt5_module, "ORDER_TYPE_SELL")

        # Timeframes
        assert hasattr(mt5_module, "TIMEFRAME_M1")
        assert hasattr(mt5_module, "TIMEFRAME_H1")
        assert hasattr(mt5_module, "TIMEFRAME_D1")

        # Position types
        assert hasattr(mt5_module, "POSITION_TYPE_BUY")
        assert hasattr(mt5_module, "POSITION_TYPE_SELL")


class TestMT5AutoLogin:
    """Test MT5 auto-login functionality."""

    def test_mt5_initialize_succeeds(self, rpyc_connection: rpyc.Connection) -> None:
        """Verify MT5 initialize() succeeds."""
        root = rpyc_connection.root
        assert root is not None, "RPyC root is None"
        result = root.initialize()
        assert result is True, "MT5 initialize() failed"

    def test_mt5_account_info_available(self, rpyc_connection: rpyc.Connection) -> None:
        """Verify account info is available after login."""
        root = rpyc_connection.root
        assert root is not None, "RPyC root is None"
        root.initialize()
        account = root.account_info()

        assert account is not None, "account_info returned None - login failed"
        assert "login" in account, "Missing login field"
        assert "server" in account, "Missing server field"
        assert "balance" in account, "Missing balance field"
        assert account["login"] > 0, f"Invalid login: {account['login']}"

    def test_mt5_terminal_connected(self, rpyc_connection: rpyc.Connection) -> None:
        """Verify terminal is connected to server."""
        root = rpyc_connection.root
        assert root is not None, "RPyC root is None"
        root.initialize()
        terminal = root.terminal_info()

        assert terminal is not None, "terminal_info returned None"
        assert "connected" in terminal, "Missing connected field"
        assert terminal["connected"] is True, "Terminal not connected"


# =============================================================================
# STARTUP SCRIPT TESTS
# =============================================================================


class TestStartupScripts:
    """Test startup scripts in container."""

    @pytest.mark.parametrize("script", CONTAINER_STARTUP_SCRIPTS)
    def test_startup_script_exists_in_container(
        self, container_name: str, script: str
    ) -> None:
        """Verify startup script exists in container."""
        result = docker_exec(container_name, ["test", "-f", script])
        assert result.returncode == 0, f"Script not found: {script}"

    @pytest.mark.parametrize("script", CONTAINER_STARTUP_SCRIPTS)
    def test_startup_script_is_executable_in_container(
        self, container_name: str, script: str
    ) -> None:
        """Verify startup script is executable in container."""
        result = docker_exec(container_name, ["test", "-x", script])
        assert result.returncode == 0, f"Script not executable: {script}"

    def test_versions_file_exists(self, container_name: str) -> None:
        """Verify .versions file was created."""
        result = docker_exec(container_name, ["cat", "/opt/mt5-staging/.versions"])
        assert result.returncode == 0, ".versions file not found"

    def test_versions_file_has_required_entries(self, container_name: str) -> None:
        """Verify .versions file has all required version entries."""
        result = docker_exec(container_name, ["cat", "/opt/mt5-staging/.versions"])

        required_vars = [
            "PYTHON_VERSION",
            "RPYC_VERSION",
            "PLUMBUM_VERSION",
            "NUMPY_VERSION",
        ]
        for var in required_vars:
            assert var in result.stdout, f".versions missing: {var}"


# =============================================================================
# SERVICE SUPERVISION TESTS
# =============================================================================


class TestServiceSupervision:
    """Test s6-overlay service supervision."""

    def test_s6_services_directory_exists(self, container_name: str) -> None:
        """Verify s6 services directory exists in container."""
        result = docker_exec(container_name, ["test", "-d", "/etc/s6-overlay/s6-rc.d"])
        assert result.returncode == 0, "s6 services directory not found"

    def test_mt5server_service_exists(self, container_name: str) -> None:
        """Verify svc-mt5server service exists."""
        result = docker_exec(
            container_name,
            ["test", "-d", "/etc/s6-overlay/s6-rc.d/svc-mt5server"],
        )
        assert result.returncode == 0, "svc-mt5server service not found"

    def test_mt5server_run_script_executable(self, container_name: str) -> None:
        """Verify mt5server run script is executable."""
        result = docker_exec(
            container_name,
            ["test", "-x", "/etc/s6-overlay/s6-rc.d/svc-mt5server/run"],
        )
        assert result.returncode == 0, "run script not executable"


# =============================================================================
# WINE PREFIX TESTS
# =============================================================================


class TestWinePrefix:
    """Test Wine prefix configuration."""

    def test_wine_prefix_exists(self, container_name: str) -> None:
        """Verify Wine prefix exists at /config/.wine."""
        result = docker_exec(container_name, ["test", "-d", "/config/.wine"])
        assert result.returncode == 0, "Wine prefix not found at /config/.wine"

    def test_wine_prefix_has_drive_c(self, container_name: str) -> None:
        """Verify Wine prefix has drive_c."""
        result = docker_exec(container_name, ["test", "-d", "/config/.wine/drive_c"])
        assert result.returncode == 0, "drive_c not found in Wine prefix"

    def test_wine_python_directory_exists(self, container_name: str) -> None:
        """Verify Python is installed in Wine prefix."""
        result = docker_exec(
            container_name, ["test", "-d", "/config/.wine/drive_c/Python"]
        )
        assert result.returncode == 0, "Python directory not found in Wine prefix"


# =============================================================================
# VOLUME AND PERSISTENCE TESTS
# =============================================================================


class TestVolumePersistence:
    """Test volume and data persistence."""

    def test_config_volume_mounted(self, container_name: str) -> None:
        """Verify /config volume is mounted."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{range .Mounts}}{{.Destination}} {{end}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "/config" in result.stdout, "/config volume not mounted"

    def test_config_directory_writable(self, container_name: str) -> None:
        """Verify /config directory is writable."""
        result = docker_exec(
            container_name,
            ["touch", "/config/.write-test"],
            user="abc",
        )
        assert result.returncode == 0, "/config not writable"

        # Cleanup
        docker_exec(container_name, ["rm", "-f", "/config/.write-test"])


# =============================================================================
# RPYC VERSION COMPATIBILITY TESTS
# =============================================================================


class TestRPyCCompatibility:
    """Test RPyC version compatibility between client and server."""

    def test_local_rpyc_version_matches_container(self, container_name: str) -> None:
        """Verify local RPyC version matches container version."""
        local_version = rpyc.__version__

        result = linux_python(container_name, "import rpyc; print(rpyc.__version__)")
        container_version = result.stdout.strip()

        # Major version must match
        assert local_version.split(".")[0] == container_version.split(".")[0], (
            f"RPyC major version mismatch: "
            f"local={local_version}, container={container_version}"
        )

    def test_wine_rpyc_version_matches_linux(self, container_name: str) -> None:
        """Verify Wine RPyC version matches Linux RPyC version."""
        code = "import rpyc; print(rpyc.__version__)"
        linux_result = linux_python(container_name, code)
        wine_result = wine_python(container_name, code)

        assert linux_result.stdout.strip() == wine_result.stdout.strip(), (
            f"RPyC version mismatch: Linux={linux_result.stdout.strip()}, "
            f"Wine={wine_result.stdout.strip()}"
        )
