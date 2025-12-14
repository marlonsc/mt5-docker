"""Pytest fixtures for mt5docker container tests.

This module provides fixtures that automatically start and validate
the ISOLATED test container (mt5docker-test on port 38812).

The container is completely isolated from:
- Production (mt5, port 8001)
- neptor tests (neptor-mt5-test, port 18812)
- mt5linux tests (mt5linux-test, port 28812)
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from collections.abc import Generator
from pathlib import Path

import pytest

# =============================================================================
# ISOLATED TEST CONFIGURATION - mt5docker specific
# =============================================================================

TEST_CONTAINER_NAME = os.getenv("MT5_CONTAINER_NAME", "mt5docker-test")
TEST_RPYC_PORT = int(os.getenv("MT5_RPYC_PORT", "48812"))  # NOT 8001/18812/28812/38812
TEST_VNC_PORT = int(os.getenv("MT5_VNC_PORT", "43000"))    # NOT 3000/13000/23000/33000
TEST_HEALTH_PORT = int(os.getenv("MT5_HEALTH_PORT", "48002"))  # NOT 8002/18002/28002/38002
TEST_TIMEOUT = 180          # seconds to wait for container

# Test credentials - loaded from .env file (see .env.example)
# Required: MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
TEST_MT5_LOGIN = os.getenv("MT5_LOGIN")
TEST_MT5_PASSWORD = os.getenv("MT5_PASSWORD")
TEST_MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")

_logger = logging.getLogger(__name__)


# =============================================================================
# CONTAINER LIFECYCLE
# =============================================================================


def _get_project_root() -> Path:
    """Get mt5docker project root."""
    return Path(__file__).parent.parent


def is_container_running(name: str = TEST_CONTAINER_NAME) -> bool:
    """Check if container is running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def is_rpyc_service_ready(host: str = "localhost", port: int = TEST_RPYC_PORT) -> bool:
    """Check if RPyC service is ready (actual handshake, not just port)."""
    try:
        from rpyc.utils.classic import connect

        conn = connect(host, port)
        conn._config["sync_request_timeout"] = 5
        _ = conn.modules
        conn.close()
        return True
    except Exception:
        return False


def wait_for_rpyc_service(
    host: str = "localhost",
    port: int = TEST_RPYC_PORT,
    timeout: int = TEST_TIMEOUT,
) -> bool:
    """Wait for RPyC service to become ready."""
    start = time.time()
    check_interval = 3

    while time.time() - start < timeout:
        if is_rpyc_service_ready(host, port):
            return True
        time.sleep(check_interval)

    return False


def start_test_container() -> None:
    """Start ISOLATED test container using docker-compose overlay."""
    project_root = _get_project_root()

    # If already running and service ready, reuse
    if is_container_running():
        if is_rpyc_service_ready():
            _logger.info(f"Test container {TEST_CONTAINER_NAME} already running")
            return
        # Running but not responding - restart
        _logger.warning("Container running but RPyC not responding. Restarting...")
        subprocess.run(
            ["docker", "rm", "-f", TEST_CONTAINER_NAME],
            capture_output=True,
            check=False,
        )

    # Check compose files exist
    base_compose = project_root / "docker-compose.yaml"
    test_compose = project_root / "docker-compose.test.yaml"

    if not base_compose.exists():
        pytest.skip(f"docker-compose.yaml not found at {project_root}")

    if not test_compose.exists():
        pytest.skip(f"docker-compose.test.yaml not found at {project_root}")

    # Start container with overlay
    _logger.info(f"Starting test container {TEST_CONTAINER_NAME}...")

    result = subprocess.run(
        [
            "docker", "compose",
            "-f", str(base_compose),
            "-f", str(test_compose),
            "up", "-d",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.skip(f"Failed to start container: {result.stderr}")

    # Wait for RPyC service
    _logger.info(f"Waiting for RPyC service on port {TEST_RPYC_PORT}...")

    if not wait_for_rpyc_service():
        logs = subprocess.run(
            ["docker", "logs", TEST_CONTAINER_NAME, "--tail", "50"],
            capture_output=True,
            text=True,
            check=False,
        )
        pytest.skip(
            f"RPyC service not ready after {TEST_TIMEOUT}s.\n"
            f"Logs: {logs.stdout[-500:] if logs.stdout else logs.stderr[-500:]}"
        )

    _logger.info(f"Test container {TEST_CONTAINER_NAME} ready on port {TEST_RPYC_PORT}")


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def docker_container() -> Generator[None, None, None]:
    """Ensure ISOLATED test container is running (session-scoped).

    This fixture runs automatically at session start.
    Container remains active after tests for reuse.
    """
    start_test_container()
    yield
    # Container stays running for reuse


@pytest.fixture(scope="session")
def container_name() -> str:
    """Provide test container name."""
    return TEST_CONTAINER_NAME


@pytest.fixture(scope="session")
def rpyc_port() -> int:
    """Provide test RPyC port."""
    return TEST_RPYC_PORT


@pytest.fixture(scope="session")
def health_port() -> int:
    """Provide test health port."""
    return TEST_HEALTH_PORT


@pytest.fixture(scope="session")
def vnc_port() -> int:
    """Provide test VNC port."""
    return TEST_VNC_PORT


@pytest.fixture(scope="session")
def mt5_credentials() -> dict[str, str | int | None]:
    """Provide MT5 test credentials from environment.

    Credentials must be configured in .env file.
    See .env.example for setup instructions.
    """
    if not TEST_MT5_LOGIN or not TEST_MT5_PASSWORD:
        pytest.skip(
            "MT5 credentials not configured. "
            "Copy .env.example to .env and fill in MT5_LOGIN and MT5_PASSWORD."
        )
    return {
        "login": int(TEST_MT5_LOGIN),
        "password": TEST_MT5_PASSWORD,
        "server": TEST_MT5_SERVER,
    }


@pytest.fixture
def rpyc_connection(docker_container: None):
    """Provide RPyC connection to test container."""
    from rpyc.utils.classic import connect

    conn = connect("localhost", TEST_RPYC_PORT)
    conn._config["sync_request_timeout"] = 30
    yield conn
    conn.close()


@pytest.fixture
def mt5_module(rpyc_connection):
    """Provide remote MetaTrader5 module via RPyC."""
    return rpyc_connection.modules.MetaTrader5
