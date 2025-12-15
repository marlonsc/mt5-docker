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

import pytest
import rpyc

from tests.fixtures.docker import DockerContainerConfig, get_test_container_config

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

    Uses RPyC 6.x rpyc.classic.connect() - the modern method for
    connecting to servers running ClassicService.
    Uses a 60 second timeout because Wine/Python RPyC server can be slow.
    """
    rpyc_port = port or _config.rpyc_port
    try:
        conn = rpyc.classic.connect(host, rpyc_port)
        conn._config["sync_request_timeout"] = 60
        _ = conn.modules.sys  # Verify connection works
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
    """Start ISOLATED test container using docker-compose overlay.

    Always starts with a clean container to ensure test isolation.
    Credentials are required to start the container.

    Raises:
        pytest.skip: If MT5 credentials are not configured.
    """
    project_root = _get_project_root()

    # Always clean up any existing container for test isolation
    if is_container_running():
        _logger.info(
            "Cleaning existing test container %s for fresh start",
            _config.container_name,
        )
        subprocess.run(
            ["docker", "rm", "-f", _config.container_name],
            capture_output=True,
            check=False,
        )

    # Clean up test volumes to ensure complete isolation
    test_volumes = ["config_data_mt5docker_test", "downloads_mt5docker_test"]
    for volume in test_volumes:
        _logger.info("Cleaning test volume: %s", volume)
        subprocess.run(
            ["docker", "volume", "rm", volume],
            capture_output=True,
            check=False,
        )

    # Always require credentials for clean test environment
    if not has_mt5_credentials():
        pytest.skip(SKIP_NO_CREDENTIALS)

    # Check compose files exist
    base_compose = project_root / "docker-compose.yaml"
    test_compose = project_root / "tests" / "fixtures" / "docker-compose.yaml"

    if not base_compose.exists():
        pytest.skip(f"docker-compose.yaml not found at {project_root}")

    if not test_compose.exists():
        pytest.skip(f"docker-compose.yaml not found at {test_compose}")

    # Start container with overlay
    _logger.info("Starting test container %s...", _config.container_name)

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
def docker_container():
    """Ensure ISOLATED test container is running (session-scoped).

    Tests that need the container should depend on this fixture.
    Container will be cleaned up after the test session.

    Skips if MT5 credentials are not configured in .env file.
    """
    start_test_container()
    # Yield to allow tests to run
    yield
    # Clean up container after session
    _cleanup_test_container()


def _cleanup_test_container() -> None:
    """Clean up test container and volumes after session."""
    if is_container_running():
        _logger.info("Cleaning up test container %s", _config.container_name)
        subprocess.run(
            ["docker", "rm", "-f", _config.container_name],
            capture_output=True,
            check=False,
        )

    # Clean up test volumes
    test_volumes = ["config_data_mt5docker_test", "downloads_mt5docker_test"]
    for volume in test_volumes:
        _logger.info("Cleaning up test volume: %s", volume)
        subprocess.run(
            ["docker", "volume", "rm", volume],
            capture_output=True,
            check=False,
        )


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
    """Provide RPyC 6.x connection to test container.

    Uses rpyc.classic.connect() which is the modern RPyC 6.x method
    for connecting to servers running ClassicService.
    """
    conn = rpyc.classic.connect("localhost", _config.rpyc_port)
    conn._config["sync_request_timeout"] = _config.rpyc_timeout
    yield conn
    conn.close()


@pytest.fixture
def mt5_module(rpyc_connection):
    """Provide remote MetaTrader5 module via RPyC."""
    return rpyc_connection.modules.MetaTrader5
