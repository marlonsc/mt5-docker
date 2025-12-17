"""Runtime tests - require Docker container to be running.

These tests validate container functionality, services, and MT5 operations.
They require the test container (mt5docker-test) to be running.

Tests will automatically skip if:
- SKIP_DOCKER=1 environment variable is set
- MT5 credentials are not configured in .env

Categories:
- ContainerHealth: Container is running and healthy
- PortExposure: All ports are correctly exposed
- gRPCService: gRPC server functionality
- WinePython: Python environment in Wine
- LinuxPython: Python environment in Linux
- MT5Integration: MetaTrader 5 functionality
- ServiceSupervision: S6-overlay service management
"""

from __future__ import annotations

import re
import subprocess

import pytest
from mt5linux import mt5_pb2, mt5_pb2_grpc

# =============================================================================
# CONSTANTS
# =============================================================================

# Main scripts to test in container (consolidated structure)
CONTAINER_MAIN_SCRIPTS = [
    "/Metatrader/start.sh",
    "/Metatrader/setup.sh",
    "/Metatrader/health_monitor.sh",
    "/Metatrader/bridge.py",
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

    def test_grpc_port_exposed(self, container_name: str, grpc_port: int) -> None:
        """Verify gRPC port is exposed."""
        result = subprocess.run(
            ["docker", "port", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert f"{grpc_port}" in result.stdout, f"gRPC port {grpc_port} not exposed"

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
        assert f"{health_port}" in result.stdout, (
            f"Health port {health_port} not exposed"
        )

    def test_ports_are_isolated(
        self,
        grpc_port: int,
        vnc_port: int,
        health_port: int,
    ) -> None:
        """Verify test ports don't conflict with production."""
        # Production ports
        prod_ports = {8001, 3000, 8002}
        test_ports = {grpc_port, vnc_port, health_port}

        assert not prod_ports & test_ports, (
            "Test ports must not overlap with production"
        )


# =============================================================================
# GRPC SERVICE TESTS
# =============================================================================


class TestGRPCService:
    """Test gRPC service functionality."""

    def test_grpc_stub_created(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify gRPC stub can be created."""
        assert mt5_stub is not None

    def test_grpc_health_check_returns_valid_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify gRPC health check returns valid status structure.

        Note: Without MT5 credentials configured, the terminal won't be
        connected to a broker, so 'healthy' and 'connected' may be False.
        This test validates the response structure, not broker connectivity.
        """
        health = mt5_stub.HealthCheck(mt5_pb2.Empty())

        # Validate response structure
        assert health is not None, "HealthCheck returned None"
        assert hasattr(health, "healthy"), "Missing 'healthy' field"
        assert hasattr(health, "mt5_available"), "Missing 'mt5_available' field"

        # MT5 module should always be available (loaded at startup)
        assert health.mt5_available is True, "MT5 module not available"

        # If connected to broker, should be healthy
        if health.connected is True:
            assert health.healthy is True, (
                "Connected but not healthy - unexpected"
            )


# =============================================================================
# WINE PYTHON TESTS
# =============================================================================


class TestWinePython:
    """Test Python environment in Wine."""

    def test_wine_python_version(self, container_name: str) -> None:
        """Verify Python 3.12.x is installed in Wine."""
        result = docker_exec(
            container_name,
            ["wine", "python", "--version"],
            user="abc",
        )

        assert result.returncode == 0, f"Python not found in Wine: {result.stderr}"
        version = result.stdout.strip()
        assert "3.12" in version, f"Expected Python 3.12.x, got {version}"

    def test_wine_grpcio_version(self, container_name: str) -> None:
        """Verify gRPC 1.76+ is installed in Wine Python."""
        result = wine_python(container_name, "import grpc; print(grpc.__version__)")

        assert result.returncode == 0, f"grpcio not installed: {result.stderr}"
        version = result.stdout.strip()
        parts = version.split(".")
        assert int(parts[0]) >= 1 and int(parts[1]) >= 76, (
            f"Expected grpcio 1.76+, got {version}"
        )

    def test_wine_numpy_version(self, container_name: str) -> None:
        """Verify numpy 1.26.x is installed in Wine Python."""
        result = wine_python(container_name, "import numpy; print(numpy.__version__)")

        assert result.returncode == 0, f"numpy not installed: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("1.26"), f"Expected numpy 1.26.x, got {version}"

    def test_wine_metatrader5_installed(self, container_name: str) -> None:
        """Verify MetaTrader5 package is installed in Wine Python."""
        result = wine_python(
            container_name,
            "import MetaTrader5; print(MetaTrader5.__version__)",
        )

        assert result.returncode == 0, f"MetaTrader5 not installed: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("5."), f"Expected MT5 5.x, got {version}"


# =============================================================================
# LINUX PYTHON TESTS
# =============================================================================


class TestLinuxPython:
    """Test Python environment in Linux.

    Note: rpyc/numpy are only installed in Wine Python (for the bridge).
    Linux Python is only used for basic scripting, not for MT5 operations.
    """

    def test_linux_python_available(self, container_name: str) -> None:
        """Verify Python 3 is available in Linux."""
        result = docker_exec(container_name, ["python3", "--version"])

        assert result.returncode == 0, f"Python3 not found: {result.stderr}"
        assert "Python 3" in result.stdout


# =============================================================================
# MT5 INTEGRATION TESTS
# =============================================================================


class TestMT5Integration:
    """Test MetaTrader 5 integration."""

    def test_mt5_stub_accessible(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify MT5 stub is accessible via gRPC."""
        assert mt5_stub is not None

    def test_mt5_version_callable(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify MT5 Version() is callable."""
        response = mt5_stub.Version(mt5_pb2.Empty())
        # Response should have version tuple fields
        assert response is not None

    def test_mt5_last_error_callable(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify MT5 LastError() is callable."""
        response = mt5_stub.LastError(mt5_pb2.Empty())
        assert response is not None

    def test_mt5_constants_accessible(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify MT5 trading constants are accessible via GetConstants()."""
        response = mt5_stub.GetConstants(mt5_pb2.Empty())
        assert response is not None, "GetConstants() returned None"
        assert response.constants_json, "constants_json is empty"

        import json

        constants = json.loads(response.constants_json)

        # Order types
        assert "ORDER_TYPE_BUY" in constants, "ORDER_TYPE_BUY missing"
        assert "ORDER_TYPE_SELL" in constants, "ORDER_TYPE_SELL missing"

        # Timeframes
        assert "TIMEFRAME_M1" in constants, "TIMEFRAME_M1 missing"
        assert "TIMEFRAME_H1" in constants, "TIMEFRAME_H1 missing"
        assert "TIMEFRAME_D1" in constants, "TIMEFRAME_D1 missing"

        # Position types
        assert "POSITION_TYPE_BUY" in constants, "POSITION_TYPE_BUY missing"
        assert "POSITION_TYPE_SELL" in constants, "POSITION_TYPE_SELL missing"


class TestMT5AutoLogin:
    """Test MT5 auto-login functionality."""

    def test_mt5_initialize_succeeds(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify MT5 Initialize() succeeds."""
        response = mt5_stub.Initialize(mt5_pb2.InitializeRequest())
        assert response.success is True, "MT5 Initialize() failed"

    def test_mt5_account_info_available(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify account info is available after login."""
        mt5_stub.Initialize(mt5_pb2.InitializeRequest())
        response = mt5_stub.AccountInfo(mt5_pb2.Empty())

        assert response is not None, "AccountInfo returned None - login failed"
        assert response.account_json, "account_json is empty"

        import json

        account = json.loads(response.account_json)
        assert "login" in account, "Missing login field"
        assert "server" in account, "Missing server field"
        assert "balance" in account, "Missing balance field"
        assert account["login"] > 0, f"Invalid login: {account['login']}"

    def test_mt5_terminal_connected(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify terminal is connected to server."""
        mt5_stub.Initialize(mt5_pb2.InitializeRequest())
        response = mt5_stub.TerminalInfo(mt5_pb2.Empty())

        assert response is not None, "TerminalInfo returned None"
        assert response.terminal_json, "terminal_json is empty"

        import json

        terminal = json.loads(response.terminal_json)
        assert "connected" in terminal, "Missing connected field"
        assert terminal["connected"] is True, "Terminal not connected"


# =============================================================================
# STARTUP SCRIPT TESTS
# =============================================================================


class TestStartupScripts:
    """Test main scripts in container (consolidated structure)."""

    @pytest.mark.parametrize("script", CONTAINER_MAIN_SCRIPTS)
    def test_main_script_exists_in_container(
        self,
        container_name: str,
        script: str,
    ) -> None:
        """Verify main script/file exists in container."""
        result = docker_exec(container_name, ["test", "-f", script])
        assert result.returncode == 0, f"File not found: {script}"

    @pytest.mark.parametrize(
        "script",
        [s for s in CONTAINER_MAIN_SCRIPTS if s.endswith(".sh")],
    )
    def test_shell_script_is_executable_in_container(
        self,
        container_name: str,
        script: str,
    ) -> None:
        """Verify shell scripts are executable in container."""
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
            "GRPCIO_VERSION",
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
            container_name,
            ["test", "-d", "/config/.wine/drive_c/Python"],
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
# GRPC VERSION COMPATIBILITY TESTS
# =============================================================================


class TestGRPCCompatibility:
    """Test gRPC version compatibility between client and server.

    Note: grpcio is installed in both Linux Python (for the test client)
    and Wine Python (for the bridge server).
    """

    def test_local_grpc_version_compatible_with_container(
        self,
        container_name: str,
    ) -> None:
        """Verify local gRPC version is compatible with container version."""
        import grpc

        local_version = grpc.__version__

        result = wine_python(container_name, "import grpc; print(grpc.__version__)")
        assert result.returncode == 0, f"grpcio not in Wine: {result.stderr}"
        container_version = result.stdout.strip()

        # Major.minor version should be compatible
        local_parts = local_version.split(".")[:2]
        container_parts = container_version.split(".")[:2]
        assert local_parts[0] == container_parts[0], (
            f"gRPC major version mismatch: "
            f"local={local_version}, container={container_version}"
        )
