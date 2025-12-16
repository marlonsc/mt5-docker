"""Docker container configuration fixtures.

This module provides configuration for the isolated test container.
All values are loaded from environment variables via dotenv.

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
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / ".env")


@dataclass
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

    # Timeouts (Wine/Python RPyC can be slow)
    startup_timeout: int
    rpyc_timeout: int

    # MT5 credentials (from environment)
    login: str | None
    password: str | None
    server: str


def get_test_container_config() -> DockerContainerConfig:
    """Get test container configuration from environment.

    Returns:
        DockerContainerConfig with values from environment or defaults.

    Note:
        MT5_LOGIN and MT5_PASSWORD are required for tests that
        need MT5 authentication. Tests will skip if not set.

    """
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
