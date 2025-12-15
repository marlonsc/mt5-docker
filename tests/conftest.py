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
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.fixtures.docker import DockerContainerConfig, get_test_container_config

if TYPE_CHECKING:
    from collections.abc import Generator

# =============================================================================
# CONFIGURATION - loaded from tests/fixtures/docker.py
# =============================================================================

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
    return bool(_config.mt5_login and _config.mt5_password)


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

    Uses a 60 second timeout because Wine/Python RPyC server can be slow.
    """
    rpyc_port = port or _config.rpyc_port
    try:
        from rpyc.utils.classic import connect

        conn = connect(host, rpyc_port)
        conn._config["sync_request_timeout"] = 60  # Wine Python is slow
        _ = conn.modules
        conn.close()
        return True
    except Exception:
        return False


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
    """Start ISOLATED test container using docker-compose overlay.

    If container is already running, reuse it (no credentials needed).
    If container is not running, credentials are required to start it.

    Raises:
        pytest.skip: If container not running and no credentials configured.
    """
    project_root = _get_project_root()

    # If already running and service ready, reuse (no credentials needed)
    if is_container_running():
        if is_rpyc_service_ready():
            _logger.info(f"Test container {_config.container_name} already running")
            return
        # Running but not responding - restart (needs credentials)
        _logger.warning("Container running but RPyC not responding. Restarting...")
        subprocess.run(
            ["docker", "rm", "-f", _config.container_name],
            capture_output=True,
            check=False,
        )

    # Container not running - need credentials to start it
    if not has_mt5_credentials():
        pytest.skip(SKIP_NO_CREDENTIALS)

    # Check compose files exist
    base_compose = project_root / "docker-compose.yaml"
    test_compose = project_root / "tests" / "fixtures" / "docker-compose.test.yaml"

    if not base_compose.exists():
        pytest.skip(f"docker-compose.yaml not found at {project_root}")

    if not test_compose.exists():
        pytest.skip(f"docker-compose.test.yaml not found at {test_compose}")

    # Start container with overlay
    _logger.info(f"Starting test container {_config.container_name}...")

    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(base_compose),
            "-f",
            str(test_compose),
            "up",
            "-d",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.skip(f"Failed to start container: {result.stderr}")

    # Wait for RPyC service
    _logger.info(f"Waiting for RPyC service on port {_config.rpyc_port}...")

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
        f"Test container {_config.container_name} ready on port {_config.rpyc_port}"
    )


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def docker_container() -> Generator[None]:
    """Ensure ISOLATED test container is running (session-scoped).

    Tests that need the container should depend on this fixture.
    Container remains active after tests for reuse.

    Skips if MT5 credentials are not configured in .env file.
    """
    start_test_container()
    return
    # Container stays running for reuse


# Pytest marker for tests requiring container
requires_container = pytest.mark.usefixtures("docker_container")


@pytest.fixture(scope="session")
def container_config() -> DockerContainerConfig:
    """Provide complete container configuration."""
    return _config


@pytest.fixture(scope="session")
def container_name() -> str:
    """Provide test container name."""
    return _config.container_name


@pytest.fixture(scope="session")
def rpyc_port() -> int:
    """Provide test RPyC port."""
    return _config.rpyc_port


@pytest.fixture(scope="session")
def health_port() -> int:
    """Provide test health port."""
    return _config.health_port


@pytest.fixture(scope="session")
def vnc_port() -> int:
    """Provide test VNC port."""
    return _config.vnc_port


@pytest.fixture(scope="session")
def mt5_credentials() -> dict[str, str | int]:
    """Provide MT5 test credentials from environment.

    Credentials must be configured in .env file.
    See .env.example for setup instructions.
    """
    if not _config.mt5_login or not _config.mt5_password:
        pytest.skip(
            "MT5 credentials not configured. "
            "Copy .env.example to .env and fill in MT5_LOGIN and MT5_PASSWORD."
        )
    return {
        "login": int(_config.mt5_login),
        "password": _config.mt5_password,
        "server": _config.mt5_server,
    }


@pytest.fixture
def rpyc_connection(docker_container: None):
    """Provide RPyC connection to test container."""
    from rpyc.utils.classic import connect

    conn = connect("localhost", _config.rpyc_port)
    conn._config["sync_request_timeout"] = _config.rpyc_timeout
    yield conn
    conn.close()


@pytest.fixture
def mt5_module(rpyc_connection):
    """Provide remote MetaTrader5 module via RPyC."""
    return rpyc_connection.modules.MetaTrader5
