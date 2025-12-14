"""Docker container configuration fixtures.

This module provides configuration for the isolated test container.
All sensitive values are loaded from environment variables.

Configuration priority:
1. Environment variables (set in .env or shell)
2. Default values (for non-sensitive settings only)

Required environment variables (see .env.example):
- MT5_LOGIN: MetaTrader 5 account login
- MT5_PASSWORD: MetaTrader 5 account password
- MT5_SERVER: MT5 server (defaults to MetaQuotes-Demo)
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DockerContainerConfig:
    """Configuration for the test container.

    All sensitive values come from environment variables.
    """

    # Container identification
    container_name: str

    # Network ports (isolated from other test environments)
    rpyc_port: int
    vnc_port: int
    health_port: int

    # Timeouts
    startup_timeout: int
    rpyc_timeout: int

    # MT5 credentials (from environment)
    mt5_login: str | None
    mt5_password: str | None
    mt5_server: str


def get_test_container_config() -> DockerContainerConfig:
    """Get test container configuration from environment.

    Returns:
        DockerContainerConfig with values from environment or defaults.

    Note:
        MT5_LOGIN and MT5_PASSWORD are required for tests that
        need MT5 authentication. Tests will skip if not set.
    """
    return DockerContainerConfig(
        # Container identification
        container_name=os.getenv("MT5_CONTAINER_NAME", "mt5docker-test"),
        # Isolated ports (avoid conflicts with production/other tests)
        rpyc_port=int(os.getenv("MT5_RPYC_PORT", "48812")),
        vnc_port=int(os.getenv("MT5_VNC_PORT", "43000")),
        health_port=int(os.getenv("MT5_HEALTH_PORT", "48002")),
        # Timeouts
        startup_timeout=180,  # seconds to wait for container
        rpyc_timeout=30,  # seconds for RPyC operations
        # MT5 credentials (required for auth tests, loaded from .env)
        mt5_login=os.getenv("MT5_LOGIN"),
        mt5_password=os.getenv("MT5_PASSWORD"),
        mt5_server=os.getenv("MT5_SERVER", "MetaQuotes-Demo"),
    )


# Port allocation documentation
PORT_ALLOCATION = """
Port allocation to avoid conflicts between test environments:

| Environment      | Container Name     | VNC   | RPyC  | Health |
|-----------------|-------------------|-------|-------|--------|
| Production      | mt5               | 3000  | 8001  | 8002   |
| mt5docker tests | mt5docker-test    | 43000 | 48812 | 48002  |
"""
