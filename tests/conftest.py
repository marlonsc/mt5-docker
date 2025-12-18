"""Pytest fixtures for mt5docker container tests.

This module provides fixtures that automatically start and validate
the ISOLATED test container (mt5docker-test on port 48812).

The container is completely isolated from:
- Production (mt5, port 8001)
- tests.(neptor-mt5-test, port 18812)
- mt5linux tests (mt5linux-test, port 28812)

Configuration is loaded from environment variables via .env file.
See .env.example for setup instructions.

Test Categories:
- Config tests: Run without container (just verify configuration values)
- Container tests: Require running container (skip if no credentials)
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import grpc
import pytest
from dotenv import load_dotenv
from mt5linux import mt5_pb2, mt5_pb2_grpc

from tests.constants import TestConstants as c  # noqa: N813

__all__: list[str] = ["c"]

if TYPE_CHECKING:
    from collections.abc import Generator

# =============================================================================
# TIMING INSTRUMENTATION
# =============================================================================

_timing_start: float = 0.0
_current_phase: str = ""


def _log(message: str, *, phase: bool = False) -> None:
    """Log message to stderr (always visible in pytest)."""
    import sys

    elapsed = time.time() - _timing_start
    if phase:
        sys.stderr.write(f"\n{'=' * 60}\n")
        sys.stderr.write(f"[{elapsed:5.1f}s] PHASE: {message}\n")
        sys.stderr.write(f"{'=' * 60}\n")
    else:
        sys.stderr.write(f"[{elapsed:5.1f}s] {message}\n")
    sys.stderr.flush()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class DockerContainerConfig:
    """Configuration for the test container."""

    container_name: str
    grpc_port: int  # Port for gRPC bridge
    vnc_port: int
    health_port: int
    startup_timeout: int
    grpc_timeout: int
    login: str | None
    password: str | None
    server: str


def get_test_container_config() -> DockerContainerConfig:
    """Get test container configuration from environment."""
    return DockerContainerConfig(
        container_name=os.environ.get("MT5_CONTAINER_NAME", "mt5docker-test"),
        grpc_port=int(os.environ.get("MT5_GRPC_PORT", c.MT5.GRPC_PORT)),
        vnc_port=int(os.environ.get("MT5_VNC_PORT", c.MT5.VNC_PORT)),
        health_port=int(
            os.environ.get("MT5_HEALTH_PORT", c.MT5.HEALTH_PORT)
        ),
        startup_timeout=int(
            os.environ.get("MT5_STARTUP_TIMEOUT", c.MT5.STARTUP_TIMEOUT)
        ),
        grpc_timeout=int(os.environ.get("MT5_GRPC_TIMEOUT", c.MT5.TIMEOUT)),
        login=os.environ.get("MT5_LOGIN"),
        password=os.environ.get("MT5_PASSWORD"),
        server=os.environ.get("MT5_SERVER", "MetaQuotes-Demo"),
    )


_config = get_test_container_config()
_logger = logging.getLogger(__name__)

# Skip message moved to TestConstants class


def has_mt5_credentials() -> bool:
    """Check if MT5 credentials are configured."""
    return bool(_config.login and _config.password)


# =============================================================================
# CONTAINER LIFECYCLE
# =============================================================================


def _get_project_root() -> Path:
    """Get mt5docker project root."""
    return Path(__file__).parent.parent


def is_container_running(name: str | None = None) -> bool:
    """Check if container is running."""
    container_name = name or _config.container_name
    _log(f"Checking if container '{container_name}' is running...")
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    running = bool(result.stdout.strip())
    _log(f"Container running: {running}")
    return running


def is_grpc_service_ready(
    host: str = "localhost",
    port: int | None = None,
    timeout: float = 10.0,
) -> bool:
    """Check if gRPC service is ready (actual handshake, not just port)."""
    grpc_port = port or _config.grpc_port
    _log(f"gRPC check: {host}:{grpc_port} (timeout={timeout:.1f}s)...")
    try:
        channel = grpc.insecure_channel(f"{host}:{grpc_port}")
        stub = mt5_pb2_grpc.MT5ServiceStub(channel)
        response = stub.HealthCheck(mt5_pb2.Empty(), timeout=timeout)
        channel.close()
        _log(
            f"gRPC check: healthy={response.healthy}, "
            f"mt5_available={response.mt5_available}"
        )
        # Service is ready if MT5 module is available (even if not broker-connected)
        return response.mt5_available
    except grpc.RpcError as e:
        _log(f"gRPC check: FAILED - {type(e).__name__}")
        return False


def wait_for_grpc_service(
    host: str = "localhost",
    port: int | None = None,
    timeout: int | None = None,
) -> bool:
    """Wait for gRPC service to become ready using progressive backoff."""
    grpc_port = port or _config.grpc_port
    wait_timeout = timeout or _config.startup_timeout

    _log(f"WAIT FOR GRPC: max {wait_timeout}s, port {grpc_port}", phase=True)

    start = time.time()
    min_interval = 0.5
    max_interval = 5.0
    current_interval = min_interval
    startup_health_timeout = c.STARTUP_HEALTH_TIMEOUT

    attempt = 0
    while time.time() - start < wait_timeout:
        attempt += 1
        remaining = wait_timeout - (time.time() - start)

        _log(f"Attempt {attempt}: checking gRPC (remaining: {remaining:.0f}s)...")

        if is_grpc_service_ready(host, grpc_port, timeout=startup_health_timeout):
            elapsed = time.time() - start
            _log(f"SUCCESS: gRPC ready after {elapsed:.1f}s ({attempt} attempts)")
            return True

        _log(f"Not ready. Waiting {current_interval:.1f}s before retry...")
        time.sleep(current_interval)
        current_interval = min(current_interval * 1.5, max_interval)

    elapsed = time.time() - start
    _log(f"TIMEOUT: gRPC not ready after {elapsed:.1f}s ({attempt} attempts)")
    return False


def start_test_container() -> None:
    """Start test container if not already running."""
    global _timing_start  # noqa: PLW0603
    _timing_start = time.time()

    _log("CONTAINER VALIDATION START", phase=True)
    _log(f"Container: {_config.container_name}")
    _log(f"gRPC port: {_config.grpc_port}")
    _log(f"Startup timeout: {_config.startup_timeout}s")

    project_root = _get_project_root()

    # PHASE 1: Check if container is running
    _log("PHASE 1: Check container status", phase=True)
    if is_container_running():
        _log(f"Container '{_config.container_name}' is running - will reuse")

        # PHASE 2: Fast-path gRPC check (2s timeout)
        _log("PHASE 2: Fast-path gRPC check (2s timeout)", phase=True)
        if is_grpc_service_ready(timeout=c.FAST_PATH_TIMEOUT):
            _log("FAST-PATH SUCCESS: gRPC already ready!")
            _log(f"Total validation time: {time.time() - _timing_start:.1f}s")
            return

        # PHASE 3: Wait for gRPC with progressive backoff
        _log("PHASE 3: Wait for gRPC (service not immediately ready)", phase=True)
        if not wait_for_grpc_service():
            _log("WARNING: gRPC not ready after full wait")
        _log(f"Total validation time: {time.time() - _timing_start:.1f}s")
        return

    # Container not running - need to start it
    _log("Container NOT running - need to start")

    # Check credentials
    _log("PHASE 2: Check credentials", phase=True)
    if not has_mt5_credentials():
        _log("SKIP: No MT5 credentials configured")
        pytest.skip(c.SKIP_NO_CREDENTIALS)

    # Check compose file
    docker_dir = project_root / "docker"
    compose_file = docker_dir / "compose.yaml"
    if not compose_file.exists():
        _log(f"SKIP: compose.yaml not found at {docker_dir}")
        pytest.skip(f"compose.yaml not found at {docker_dir}")

    # Build environment
    test_env = os.environ.copy()
    test_env.update(
        {
            "MT5_CONTAINER_NAME": _config.container_name,
            "MT5_GRPC_PORT": str(_config.grpc_port),
            "MT5_VNC_PORT": str(_config.vnc_port),
            "MT5_HEALTH_PORT": str(_config.health_port),
            "MT5_VOLUME_NAME": f"{_config.container_name}-data",
            "MT5_NETWORK_NAME": f"{_config.container_name}-network",
        },
    )

    # Start container
    _log("PHASE 3: Start container with docker-compose", phase=True)
    _log("Running: docker compose up -d...")

    result = subprocess.run(
        ["docker", "compose", "--project-name", "mt5docker-test", "up", "-d"],
        cwd=docker_dir,
        capture_output=True,
        text=True,
        check=False,
        env=test_env,
    )

    if result.returncode != 0:
        _log(f"FAILED: docker compose error: {result.stderr}")
        pytest.skip(f"Failed to start container: {result.stderr}")

    _log("Container started, now waiting for gRPC...")

    # Wait for gRPC
    _log("PHASE 4: Wait for gRPC service", phase=True)

    if not wait_for_grpc_service():
        logs = subprocess.run(
            ["docker", "logs", _config.container_name, "--tail", str(c.LOG_TAIL_LINES)],
            capture_output=True,
            text=True,
            check=False,
        )
        log_output = (
            logs.stdout[-c.MAX_LOG_LENGTH :]
            if logs.stdout
            else logs.stderr[-c.MAX_LOG_LENGTH :]
        )
        pytest.skip(
            f"gRPC service not ready after {_config.startup_timeout}s.\n"
            f"Logs: {log_output}",
        )

    _logger.info(
        "Test container %s ready on port %s",
        _config.container_name,
        _config.grpc_port,
    )


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def docker_container() -> None:
    """Ensure test container is running (session-scoped).

    This fixture is NOT autouse - only tests that need the container
    will trigger container startup via dependent fixtures.

    Starts container if not already running.
    Reuses existing container if healthy.
    Does NOT clean up after tests - container stays running for reuse.

    Skips if:
    - SKIP_DOCKER=1 environment variable is set
    - MT5 credentials are not configured in .env file
    """
    if os.getenv("SKIP_DOCKER", "0") == "1":
        _logger.info("SKIP_DOCKER=1 - Docker container tests will be skipped")
        pytest.skip("Docker tests skipped via SKIP_DOCKER=1")

    start_test_container()


@pytest.fixture(scope="session")
def container_name(docker_container: None) -> str:  # noqa: ARG001
    """Provide test container name (requires container)."""
    return _config.container_name


@pytest.fixture(scope="session")
def grpc_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test gRPC port (requires container)."""
    return _config.grpc_port


@pytest.fixture(scope="session")
def health_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test health port (requires container)."""
    return _config.health_port


@pytest.fixture(scope="session")
def vnc_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test VNC port (requires container)."""
    return _config.vnc_port


@pytest.fixture
def grpc_channel(
    docker_container: None,  # noqa: ARG001
) -> Generator[grpc.Channel]:
    """Provide gRPC channel to test container."""
    channel = grpc.insecure_channel(f"localhost:{_config.grpc_port}")
    yield channel
    channel.close()


@pytest.fixture
def mt5_stub(grpc_channel: grpc.Channel) -> mt5_pb2_grpc.MT5ServiceStub:
    """Provide MT5Service stub via gRPC."""
    return mt5_pb2_grpc.MT5ServiceStub(grpc_channel)


@pytest.fixture
def mt5_service(grpc_channel: grpc.Channel) -> mt5_pb2_grpc.MT5ServiceStub:
    """Provide MT5Service stub via gRPC (alias for mt5_stub)."""
    return mt5_pb2_grpc.MT5ServiceStub(grpc_channel)
