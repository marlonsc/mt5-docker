"""Pytest fixtures for mt5docker container tests.

This module provides fixtures that automatically start and validate
the ISOLATED test container (mt5docker-test on port 48812).

The container is completely isolated from:
- Production (mt5, port 8001)
- neptor tests (neptor-mt5-test, port 18812)
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
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import rpyc
from dotenv import load_dotenv

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
    rpyc_port: int
    vnc_port: int
    health_port: int
    startup_timeout: int
    rpyc_timeout: int
    login: str | None
    password: str | None
    server: str


def get_test_container_config() -> DockerContainerConfig:
    """Get test container configuration from environment."""
    return DockerContainerConfig(
        container_name=os.environ.get("MT5_CONTAINER_NAME", "mt5docker-test"),
        rpyc_port=int(os.environ.get("MT5_RPYC_PORT", "48812")),
        vnc_port=int(os.environ.get("MT5_VNC_PORT", "43000")),
        health_port=int(os.environ.get("MT5_HEALTH_PORT", "48002")),
        startup_timeout=int(os.environ.get("MT5_STARTUP_TIMEOUT", "180")),
        rpyc_timeout=int(os.environ.get("MT5_RPYC_TIMEOUT", "60")),
        login=os.environ.get("MT5_LOGIN"),
        password=os.environ.get("MT5_PASSWORD"),
        server=os.environ.get("MT5_SERVER", "MetaQuotes-Demo"),
    )


_config = get_test_container_config()
_logger = logging.getLogger(__name__)

# Skip message for tests requiring credentials
SKIP_NO_CREDENTIALS = (
    "MT5 credentials not configured. "
    "To run container tests, create .env file with MT5_LOGIN and MT5_PASSWORD. "
    "See .env.example for details."
)


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
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def is_rpyc_service_ready(host: str = "localhost", port: int | None = None) -> bool:
    """Check if RPyC service is ready (actual handshake, not just port).

    Uses rpyc.connect() for our custom MT5Service.
    Uses a 60 second timeout because Wine/Python RPyC server can be slow.
    """
    rpyc_port = port or _config.rpyc_port
    try:
        conn = rpyc.connect(host, rpyc_port, config={"sync_request_timeout": 60})
        # Verify connection works by calling health_check
        _ = conn.root.health_check()
        conn.close()
    except (OSError, ConnectionError, TimeoutError, EOFError):
        return False
    else:
        return True


def wait_for_rpyc_service(
    host: str = "localhost",
    port: int | None = None,
    timeout: int | None = None,
) -> bool:
    """Wait for RPyC service to become ready."""
    rpyc_port = port or _config.rpyc_port
    wait_timeout = timeout or _config.startup_timeout
    start = time.time()
    check_interval = 3

    while time.time() - start < wait_timeout:
        if is_rpyc_service_ready(host, rpyc_port):
            return True
        time.sleep(check_interval)

    return False


def start_test_container() -> None:
    """Start test container if not already running.

    Uses the main docker-compose.yaml with environment variables
    to configure container name, ports, and volumes.

    Reuses existing container if already running.

    Raises
    ------
    pytest.skip
        If MT5 credentials are not configured.

    """
    project_root = _get_project_root()

    # Check if container is already running - reuse it
    if is_container_running():
        _logger.info(
            "Container %s already running, reusing",
            _config.container_name,
        )
        # Wait for RPyC to be ready if not already
        if not is_rpyc_service_ready():
            _logger.info("Waiting for RPyC service...")
            wait_for_rpyc_service()
        return

    # Require credentials to start new container
    if not has_mt5_credentials():
        pytest.skip(SKIP_NO_CREDENTIALS)

    # Check compose file exists (compose.yaml is in docker/ subdirectory)
    docker_dir = project_root / "docker"
    compose_file = docker_dir / "compose.yaml"
    if not compose_file.exists():
        pytest.skip(f"compose.yaml not found at {docker_dir}")

    # Build environment with test-specific values
    # These override the defaults in compose.yaml
    test_env = os.environ.copy()
    test_env.update(
        {
            "MT5_CONTAINER_NAME": _config.container_name,
            "MT5_RPYC_PORT": str(_config.rpyc_port),
            "MT5_VNC_PORT": str(_config.vnc_port),
            "MT5_HEALTH_PORT": str(_config.health_port),
            "MT5_VOLUME_NAME": f"{_config.container_name}-data",
            "MT5_NETWORK_NAME": f"{_config.container_name}-network",
        }
    )

    # Start container with test environment
    # Use --project-name to isolate from production container
    _logger.info("Starting test container %s...", _config.container_name)

    result = subprocess.run(
        ["docker", "compose", "--project-name", "mt5docker-test", "up", "-d"],
        cwd=docker_dir,
        capture_output=True,
        text=True,
        check=False,
        env=test_env,
    )

    if result.returncode != 0:
        pytest.skip(f"Failed to start container: {result.stderr}")

    # Wait for RPyC service
    _logger.info("Waiting for RPyC service on port %s...", _config.rpyc_port)

    if not wait_for_rpyc_service():
        logs = subprocess.run(
            ["docker", "logs", _config.container_name, "--tail", "50"],
            capture_output=True,
            text=True,
            check=False,
        )
        pytest.skip(
            f"RPyC service not ready after {_config.startup_timeout}s.\n"
            f"Logs: {logs.stdout[-500:] if logs.stdout else logs.stderr[-500:]}"
        )

    _logger.info(
        "Test container %s ready on port %s",
        _config.container_name,
        _config.rpyc_port,
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
def rpyc_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test RPyC port (requires container)."""
    return _config.rpyc_port


@pytest.fixture(scope="session")
def health_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test health port (requires container)."""
    return _config.health_port


@pytest.fixture(scope="session")
def vnc_port(docker_container: None) -> int:  # noqa: ARG001
    """Provide test VNC port (requires container)."""
    return _config.vnc_port


@pytest.fixture
def rpyc_connection(
    docker_container: None,  # noqa: ARG001
) -> Generator[rpyc.Connection, None, None]:
    """Provide RPyC connection to test container.

    Uses rpyc.connect() for our custom MT5Service.
    """
    conn = rpyc.connect(
        "localhost",
        _config.rpyc_port,
        config={"sync_request_timeout": _config.rpyc_timeout},
    )
    yield conn
    conn.close()


@pytest.fixture
def mt5_service(rpyc_connection: rpyc.Connection) -> Any:
    """Provide MT5Service root object via RPyC."""
    root = rpyc_connection.root
    assert root is not None, "RPyC root is None"
    return root


@pytest.fixture
def mt5_module(rpyc_connection: rpyc.Connection) -> Any:
    """Provide MT5 service root via RPyC.

    Note: get_mt5() was removed for security (exposed raw module).
    The root service directly exposes all MT5 functions like version(),
    last_error(), copy_rates(), etc.
    """
    root = rpyc_connection.root
    assert root is not None, "RPyC root is None"
    return root
