"""Docker container configuration fixtures.

This module provides configuration for the isolated test container.
All sensitive values are loaded from environment variables via Pydantic 2.

Configuration priority:
1. Environment variables (set in .env or shell)
2. Default values (for non-sensitive settings only)

Required environment variables (see .env.example):
- MT5_LOGIN: MetaTrader 5 account login
- MT5_PASSWORD: MetaTrader 5 account password
- MT5_SERVER: MT5 server (defaults to MetaQuotes-Demo)
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DockerContainerConfig(BaseSettings):
    """Configuration for the test container using Pydantic 2 BaseSettings.

    All sensitive values come from environment variables.
    Environment variables use MT5_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="MT5_",
        case_sensitive=False,
        extra="ignore",
    )

    # Container identification
    container_name: str = Field(default="mt5docker-test")

    # Network ports (isolated from other test environments)
    rpyc_port: int = Field(default=48812)
    vnc_port: int = Field(default=43000)
    health_port: int = Field(default=48002)

    # Timeouts (Wine/Python RPyC can be slow)
    startup_timeout: int = Field(default=180)  # seconds to wait for container
    rpyc_timeout: int = Field(default=60)  # seconds for RPyC operations

    # MT5 credentials (from environment)
    mt5_login: str | None = Field(default=None, alias="LOGIN")
    mt5_password: str | None = Field(default=None, alias="PASSWORD")
    mt5_server: str = Field(default="MetaQuotes-Demo", alias="SERVER")


def get_test_container_config() -> DockerContainerConfig:
    """Get test container configuration from environment.

    Returns:
        DockerContainerConfig with values from environment or defaults.

    Note:
        MT5_LOGIN and MT5_PASSWORD are required for tests that
        need MT5 authentication. Tests will skip if not set.
    """
    return DockerContainerConfig()


# Port allocation documentation
PORT_ALLOCATION = """
Port allocation to avoid conflicts between test environments:

| Environment      | Container Name     | VNC   | RPyC  | Health |
|-----------------|-------------------|-------|-------|--------|
| Production      | mt5               | 3000  | 8001  | 8002   |
| mt5docker tests | mt5docker-test    | 43000 | 48812 | 48002  |
"""
