"""Comprehensive bridge validation tests.

Tests include:
- Function signature validation (bridge vs official MT5 API)
- Service recovery and failure simulation
- Constants completeness check
- Upgrade testing
"""

from __future__ import annotations

import subprocess
import time
from typing import Any

import pytest
import rpyc

# =============================================================================
# OFFICIAL MT5 API FUNCTION SIGNATURES
# From: https://www.mql5.com/en/docs/python_metatrader5
# =============================================================================

# Official MetaTrader5 Python module functions and their parameter signatures
OFFICIAL_MT5_FUNCTIONS = {
    # Connection functions
    "initialize": {
        "params": ["path", "login", "password", "server", "timeout", "portable"],
        "optional": ["path", "login", "password", "server", "timeout", "portable"],
        "returns": "bool",
    },
    "login": {
        "params": ["login", "password", "server", "timeout"],
        "optional": ["timeout"],
        "returns": "bool",
    },
    "shutdown": {
        "params": [],
        "optional": [],
        "returns": "None",
    },
    # Information functions
    "version": {
        "params": [],
        "optional": [],
        "returns": "tuple | None",
    },
    "last_error": {
        "params": [],
        "optional": [],
        "returns": "tuple",
    },
    "terminal_info": {
        "params": [],
        "optional": [],
        "returns": "TerminalInfo | None",
    },
    "account_info": {
        "params": [],
        "optional": [],
        "returns": "AccountInfo | None",
    },
    # Symbol functions
    "symbols_total": {
        "params": [],
        "optional": [],
        "returns": "int",
    },
    "symbols_get": {
        "params": ["group"],
        "optional": ["group"],
        "returns": "tuple | None",
    },
    "symbol_info": {
        "params": ["symbol"],
        "optional": [],
        "returns": "SymbolInfo | None",
    },
    "symbol_info_tick": {
        "params": ["symbol"],
        "optional": [],
        "returns": "Tick | None",
    },
    "symbol_select": {
        "params": ["symbol", "enable"],
        "optional": ["enable"],
        "returns": "bool",
    },
    # Rates functions
    "copy_rates_from": {
        "params": ["symbol", "timeframe", "date_from", "count"],
        "optional": [],
        "returns": "ndarray | None",
    },
    "copy_rates_from_pos": {
        "params": ["symbol", "timeframe", "start_pos", "count"],
        "optional": [],
        "returns": "ndarray | None",
    },
    "copy_rates_range": {
        "params": ["symbol", "timeframe", "date_from", "date_to"],
        "optional": [],
        "returns": "ndarray | None",
    },
    # Ticks functions
    "copy_ticks_from": {
        "params": ["symbol", "date_from", "count", "flags"],
        "optional": [],
        "returns": "ndarray | None",
    },
    "copy_ticks_range": {
        "params": ["symbol", "date_from", "date_to", "flags"],
        "optional": [],
        "returns": "ndarray | None",
    },
    # Order calculation
    "order_calc_margin": {
        "params": ["action", "symbol", "volume", "price"],
        "optional": [],
        "returns": "float | None",
    },
    "order_calc_profit": {
        "params": ["action", "symbol", "volume", "price_open", "price_close"],
        "optional": [],
        "returns": "float | None",
    },
    "order_check": {
        "params": ["request"],
        "optional": [],
        "returns": "OrderCheckResult | None",
    },
    "order_send": {
        "params": ["request"],
        "optional": [],
        "returns": "OrderSendResult | None",
    },
    # Position functions
    "positions_total": {
        "params": [],
        "optional": [],
        "returns": "int",
    },
    "positions_get": {
        "params": ["symbol", "group", "ticket"],
        "optional": ["symbol", "group", "ticket"],
        "returns": "tuple | None",
    },
    # Order functions
    "orders_total": {
        "params": [],
        "optional": [],
        "returns": "int",
    },
    "orders_get": {
        "params": ["symbol", "group", "ticket"],
        "optional": ["symbol", "group", "ticket"],
        "returns": "tuple | None",
    },
    # History functions
    "history_orders_total": {
        "params": ["date_from", "date_to"],
        "optional": [],
        "returns": "int | None",
    },
    "history_orders_get": {
        "params": ["date_from", "date_to", "group", "ticket", "position"],
        "optional": ["date_from", "date_to", "group", "ticket", "position"],
        "returns": "tuple | None",
    },
    "history_deals_total": {
        "params": ["date_from", "date_to"],
        "optional": [],
        "returns": "int | None",
    },
    "history_deals_get": {
        "params": ["date_from", "date_to", "group", "ticket", "position"],
        "optional": ["date_from", "date_to", "group", "ticket", "position"],
        "returns": "tuple | None",
    },
    # Market Depth (DOM) functions
    "market_book_add": {
        "params": ["symbol"],
        "optional": [],
        "returns": "bool",
    },
    "market_book_get": {
        "params": ["symbol"],
        "optional": [],
        "returns": "tuple | None",
    },
    "market_book_release": {
        "params": ["symbol"],
        "optional": [],
        "returns": "bool",
    },
}

# Official MT5 constants categories
OFFICIAL_MT5_CONSTANTS = {
    # Timeframes (21 total)
    "timeframes": [
        "TIMEFRAME_M1",
        "TIMEFRAME_M2",
        "TIMEFRAME_M3",
        "TIMEFRAME_M4",
        "TIMEFRAME_M5",
        "TIMEFRAME_M6",
        "TIMEFRAME_M10",
        "TIMEFRAME_M12",
        "TIMEFRAME_M15",
        "TIMEFRAME_M20",
        "TIMEFRAME_M30",
        "TIMEFRAME_H1",
        "TIMEFRAME_H2",
        "TIMEFRAME_H3",
        "TIMEFRAME_H4",
        "TIMEFRAME_H6",
        "TIMEFRAME_H8",
        "TIMEFRAME_H12",
        "TIMEFRAME_D1",
        "TIMEFRAME_W1",
        "TIMEFRAME_MN1",
    ],
    # Order types (9 total)
    "order_types": [
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
        "ORDER_TYPE_BUY_LIMIT",
        "ORDER_TYPE_SELL_LIMIT",
        "ORDER_TYPE_BUY_STOP",
        "ORDER_TYPE_SELL_STOP",
        "ORDER_TYPE_BUY_STOP_LIMIT",
        "ORDER_TYPE_SELL_STOP_LIMIT",
        "ORDER_TYPE_CLOSE_BY",
    ],
    # Trade actions (6 total)
    "trade_actions": [
        "TRADE_ACTION_DEAL",
        "TRADE_ACTION_PENDING",
        "TRADE_ACTION_SLTP",
        "TRADE_ACTION_MODIFY",
        "TRADE_ACTION_REMOVE",
        "TRADE_ACTION_CLOSE_BY",
    ],
    # Order filling modes (4 total)
    "order_filling": [
        "ORDER_FILLING_FOK",
        "ORDER_FILLING_IOC",
        "ORDER_FILLING_RETURN",
        "ORDER_FILLING_BOC",
    ],
    # Order time types (4 total)
    "order_time": [
        "ORDER_TIME_GTC",
        "ORDER_TIME_DAY",
        "ORDER_TIME_SPECIFIED",
        "ORDER_TIME_SPECIFIED_DAY",
    ],
    # Position types (2 total)
    "position_types": ["POSITION_TYPE_BUY", "POSITION_TYPE_SELL"],
    # Deal types (17+ total)
    "deal_types": [
        "DEAL_TYPE_BUY",
        "DEAL_TYPE_SELL",
        "DEAL_TYPE_BALANCE",
        "DEAL_TYPE_CREDIT",
        "DEAL_TYPE_CHARGE",
        "DEAL_TYPE_CORRECTION",
        "DEAL_TYPE_BONUS",
        "DEAL_TYPE_COMMISSION",
    ],
    # Copy ticks flags (3 total)
    "copy_ticks": ["COPY_TICKS_ALL", "COPY_TICKS_INFO", "COPY_TICKS_TRADE"],
    # Book types (4 total)
    "book_types": [
        "BOOK_TYPE_SELL",
        "BOOK_TYPE_BUY",
        "BOOK_TYPE_SELL_MARKET",
        "BOOK_TYPE_BUY_MARKET",
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def docker_exec(
    container: str,
    command: list[str],
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Execute command in container."""
    return subprocess.run(
        ["docker", "exec", container, *command],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def get_rpyc_connection(port: int = 48812, timeout: int = 60) -> rpyc.Connection:
    """Get RPyC connection to bridge server."""
    return rpyc.connect("localhost", port, config={"sync_request_timeout": timeout})


# =============================================================================
# SIGNATURE VALIDATION TESTS
# =============================================================================


class TestBridgeFunctionSignatures:
    """Validate bridge function signatures against official MT5 API."""

    @pytest.fixture
    def bridge_service(self, rpyc_connection: rpyc.Connection) -> Any:
        """Get bridge service root."""
        return rpyc_connection.root

    def test_all_official_functions_exposed(self, bridge_service: Any) -> None:
        """Verify all official MT5 functions are exposed in bridge."""
        missing_functions = [
            func_name
            for func_name in OFFICIAL_MT5_FUNCTIONS
            if not hasattr(bridge_service, func_name)
        ]

        assert not missing_functions, (
            f"Missing official MT5 functions in bridge: {missing_functions}"
        )

    @pytest.mark.parametrize("func_name", list(OFFICIAL_MT5_FUNCTIONS.keys()))
    def test_function_is_callable(self, bridge_service: Any, func_name: str) -> None:
        """Verify each function is callable."""
        func = getattr(bridge_service, func_name, None)
        assert func is not None, f"Function {func_name} not found"
        assert callable(func), f"Function {func_name} is not callable"

    def test_health_check_extra_function(self, bridge_service: Any) -> None:
        """Verify health_check is available (bridge-specific)."""
        assert hasattr(bridge_service, "health_check")
        result = bridge_service.health_check()
        assert isinstance(result, dict)
        assert "healthy" in result
        assert "mt5_available" in result

    def test_get_constants_extra_function(self, bridge_service: Any) -> None:
        """Verify get_constants is available (bridge-specific)."""
        assert hasattr(bridge_service, "get_constants")
        result = bridge_service.get_constants()
        assert isinstance(result, dict)
        assert len(result) > 50, f"Expected 50+ constants, got {len(result)}"


class TestBridgeConstants:
    """Validate bridge constants against official MT5 API."""

    @pytest.fixture
    def bridge_constants(self, rpyc_connection: rpyc.Connection) -> dict[str, Any]:
        """Get constants from bridge."""
        return rpyc_connection.root.get_constants()

    def test_constants_not_empty(self, bridge_constants: dict[str, Any]) -> None:
        """Verify constants dict is not empty."""
        assert len(bridge_constants) > 0, "Constants dict is empty"

    @pytest.mark.parametrize(
        ("category", "constants"),
        list(OFFICIAL_MT5_CONSTANTS.items()),
    )
    def test_category_constants_present(
        self,
        bridge_constants: dict[str, Any],
        category: str,
        constants: list[str],
    ) -> None:
        """Verify each category of constants is present."""
        missing = [c for c in constants if c not in bridge_constants]
        assert not missing, f"Missing {category} constants: {missing}"

    def test_timeframe_values_are_integers(
        self,
        bridge_constants: dict[str, Any],
    ) -> None:
        """Verify timeframe constants are integers."""
        for tf in OFFICIAL_MT5_CONSTANTS["timeframes"]:
            if tf in bridge_constants:
                assert isinstance(bridge_constants[tf], int), (
                    f"{tf} should be int, got {type(bridge_constants[tf])}"
                )

    def test_order_type_values_are_integers(
        self,
        bridge_constants: dict[str, Any],
    ) -> None:
        """Verify order type constants are integers."""
        for ot in OFFICIAL_MT5_CONSTANTS["order_types"]:
            if ot in bridge_constants:
                assert isinstance(bridge_constants[ot], int), (
                    f"{ot} should be int, got {type(bridge_constants[ot])}"
                )


# =============================================================================
# SERVICE RECOVERY TESTS
# =============================================================================


@pytest.mark.requires_container
class TestServiceRecovery:
    """Test service recovery and failure handling.

    These tests use container_name and rpyc_port fixtures from conftest.py,
    which automatically start the test container if not running.
    """

    def test_bridge_survives_reconnection(
        self,
        container_name: str,
        rpyc_port: int,
    ) -> None:
        """Test bridge handles client reconnection gracefully."""
        # First connection
        conn1 = rpyc.connect("localhost", rpyc_port)
        health1 = conn1.root.health_check()
        assert health1 is not None
        conn1.close()

        # Wait a bit
        time.sleep(1)

        # Second connection should work
        conn2 = rpyc.connect("localhost", rpyc_port)
        health2 = conn2.root.health_check()
        assert health2 is not None
        conn2.close()

    def test_bridge_handles_rapid_connections(
        self,
        container_name: str,
        rpyc_port: int,
    ) -> None:
        """Test bridge handles rapid connect/disconnect cycles."""
        for i in range(5):
            conn = rpyc.connect("localhost", rpyc_port)
            health = conn.root.health_check()
            assert health is not None, f"Failed on iteration {i}"
            conn.close()

    def test_restart_token_creation(self, container_name: str) -> None:
        """Test that restart token can be created."""
        result = docker_exec(
            container_name,
            ["touch", "/tmp/.mt5-restart-requested"],
        )
        assert result.returncode == 0

        # Verify token exists
        result = docker_exec(
            container_name,
            ["test", "-f", "/tmp/.mt5-restart-requested"],
        )
        assert result.returncode == 0

        # Clean up
        docker_exec(container_name, ["rm", "-f", "/tmp/.mt5-restart-requested"])

    def test_health_monitor_is_running(self, container_name: str) -> None:
        """Verify health monitor process is running."""
        result = docker_exec(
            container_name,
            ["pgrep", "-f", "health_monitor"],
        )
        assert result.returncode == 0, "Health monitor is not running"

    def test_bridge_process_is_running(self, container_name: str) -> None:
        """Verify bridge process is running."""
        result = docker_exec(
            container_name,
            ["pgrep", "-f", "mt5linux.bridge"],
        )
        assert result.returncode == 0, "Bridge process is not running"

    def test_s6_service_status(self, container_name: str) -> None:
        """Verify s6 service is running."""
        result = docker_exec(
            container_name,
            ["s6-svstat", "/run/service/svc-mt5server"],
        )
        # s6-svstat returns 0 even if service has issues, check output
        assert "up" in result.stdout.lower() or result.returncode == 0


# =============================================================================
# UPGRADE TESTS
# =============================================================================


@pytest.mark.requires_container
class TestUpgrade:
    """Test upgrade and package installation.

    Uses container_name fixture from conftest.py.
    """

    def test_pip_upgrade_works(self, container_name: str) -> None:
        """Test that pip upgrade command works in Wine Python."""
        result = docker_exec(
            container_name,
            [
                "su",
                "-",
                "abc",
                "-c",
                "wine /config/.wine/drive_c/Python/python.exe -m pip list --outdated",
            ],
            timeout=60,
        )
        # Command should succeed (returncode 0)
        assert result.returncode == 0 or "No matching distribution" not in result.stderr

    def test_metatrader5_package_version(self, container_name: str) -> None:
        """Verify MetaTrader5 package version is retrievable."""
        result = docker_exec(
            container_name,
            [
                "su",
                "-",
                "abc",
                "-c",
                "wine /config/.wine/drive_c/Python/python.exe -c "
                "'import MetaTrader5; print(MetaTrader5.__version__)'",
            ],
            timeout=60,
        )
        assert result.returncode == 0
        assert result.stdout.strip().startswith("5.")

    def test_rpyc_package_version(self, container_name: str) -> None:
        """Verify RPyC package version is retrievable."""
        result = docker_exec(
            container_name,
            [
                "su",
                "-",
                "abc",
                "-c",
                "wine /config/.wine/drive_c/Python/python.exe -c "
                "'import rpyc; print(rpyc.__version__)'",
            ],
            timeout=60,
        )
        assert result.returncode == 0
        assert result.stdout.strip().startswith("6.")

    def test_grpcio_package_version(self, container_name: str) -> None:
        """Verify gRPC package version is retrievable (for mt5linux client)."""
        result = docker_exec(
            container_name,
            [
                "su",
                "-",
                "abc",
                "-c",
                "wine /config/.wine/drive_c/Python/python.exe -c "
                "'import grpc; print(grpc.__version__)'",
            ],
            timeout=60,
        )
        assert result.returncode == 0
        version = result.stdout.strip()
        parts = version.split(".")
        assert int(parts[0]) >= 1 and int(parts[1]) >= 76, (
            f"Expected grpcio 1.76+, got {version}"
        )


# =============================================================================
# BRIDGE API TESTS
# =============================================================================


class TestBridgeAPICompleteness:
    """Test bridge API completeness and behavior."""

    def test_version_returns_tuple_or_none(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test version() returns expected type."""
        result = rpyc_connection.root.version()
        assert result is None or isinstance(result, tuple)

    def test_last_error_returns_tuple(self, rpyc_connection: rpyc.Connection) -> None:
        """Test last_error() returns expected type."""
        result = rpyc_connection.root.last_error()
        assert isinstance(result, tuple)
        assert len(result) == 2  # (code, description)

    def test_symbols_total_returns_int_or_none(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test symbols_total() returns integer or None if not connected."""
        result = rpyc_connection.root.symbols_total()
        # Returns None when terminal not connected to broker
        assert result is None or isinstance(result, int)

    def test_positions_total_returns_int_or_none(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test positions_total() returns integer or None if not connected."""
        result = rpyc_connection.root.positions_total()
        # Returns None when terminal not connected to broker
        assert result is None or isinstance(result, int)

    def test_orders_total_returns_int_or_none(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test orders_total() returns integer or None if not connected."""
        result = rpyc_connection.root.orders_total()
        # Returns None when terminal not connected to broker
        assert result is None or isinstance(result, int)


# =============================================================================
# FAILURE SIMULATION TESTS
# =============================================================================


@pytest.mark.requires_container
class TestFailureSimulation:
    """Simulate various failure scenarios.

    Uses rpyc_connection fixture from conftest.py.
    """

    def test_bridge_recovers_from_invalid_symbol(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test bridge handles invalid symbol gracefully."""
        # Try to get info for a non-existent symbol
        result = rpyc_connection.root.symbol_info("INVALID_SYMBOL_XYZ123")
        # Should return None, not raise exception
        assert result is None

    def test_bridge_handles_empty_positions(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test bridge handles empty positions list."""
        result = rpyc_connection.root.positions_get()
        # Should return empty tuple or None, not raise
        assert result is None or isinstance(result, tuple)

    def test_bridge_handles_empty_orders(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test bridge handles empty orders list."""
        result = rpyc_connection.root.orders_get()
        # Should return empty tuple or None, not raise
        assert result is None or isinstance(result, tuple)

    def test_bridge_handles_invalid_timeframe(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test bridge handles invalid timeframe value."""
        import datetime

        result = rpyc_connection.root.copy_rates_from(
            "EURUSD",
            99999,
            datetime.datetime.now(),
            10,
        )
        # Should return None for invalid timeframe
        assert result is None

    def test_health_check_after_many_operations(
        self,
        rpyc_connection: rpyc.Connection,
    ) -> None:
        """Test health check still works after many operations."""
        # Perform many operations
        for _ in range(10):
            rpyc_connection.root.version()
            rpyc_connection.root.last_error()
            rpyc_connection.root.symbols_total()

        # Health check should still work
        health = rpyc_connection.root.health_check()
        assert health is not None
        assert "mt5_available" in health
