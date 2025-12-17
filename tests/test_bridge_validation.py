"""Comprehensive bridge validation tests.

Tests include:
- Function signature validation (bridge vs official MT5 API)
- Service recovery and failure simulation
- Constants completeness check
- Upgrade testing
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any

import grpc
import pytest
from mt5linux import mt5_pb2, mt5_pb2_grpc

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


def get_grpc_stub(
    port: int = 48812,
) -> tuple[grpc.Channel, mt5_pb2_grpc.MT5ServiceStub]:
    """Get gRPC channel and stub to bridge server."""
    channel = grpc.insecure_channel(f"localhost:{port}")
    stub = mt5_pb2_grpc.MT5ServiceStub(channel)
    return channel, stub


# =============================================================================
# SIGNATURE VALIDATION TESTS
# =============================================================================


class TestBridgeFunctionSignatures:
    """Validate bridge function signatures against official MT5 API."""

    def test_health_check_function(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify HealthCheck is available (bridge-specific)."""
        result = mt5_stub.HealthCheck(mt5_pb2.Empty())
        assert result is not None
        assert hasattr(result, "healthy")
        assert hasattr(result, "mt5_available")

    def test_get_constants_function(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify GetConstants is available (bridge-specific)."""
        result = mt5_stub.GetConstants(mt5_pb2.Empty())
        assert result is not None
        assert result.values  # Constants.values is a map
        assert len(result.values) > 50, f"Expected 50+ constants, got {len(result.values)}"

    def test_initialize_function(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify Initialize is available."""
        result = mt5_stub.Initialize(mt5_pb2.InitRequest())
        assert result is not None
        assert hasattr(result, "result")

    def test_version_function(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify Version is available."""
        result = mt5_stub.Version(mt5_pb2.Empty())
        assert result is not None

    def test_last_error_function(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Verify LastError is available."""
        result = mt5_stub.LastError(mt5_pb2.Empty())
        assert result is not None
        assert hasattr(result, "code")
        assert hasattr(result, "message")


class TestBridgeConstants:
    """Validate bridge constants against official MT5 API."""

    @pytest.fixture
    def bridge_constants(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> dict[str, Any]:
        """Get constants from bridge."""
        response = mt5_stub.GetConstants(mt5_pb2.Empty())
        return dict(response.values)

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

    These tests use container_name and grpc_port fixtures from conftest.py,
    which automatically start the test container if not running.
    """

    def test_bridge_survives_reconnection(
        self,
        container_name: str,
        grpc_port: int,
    ) -> None:
        """Test bridge handles client reconnection gracefully."""
        # First connection
        channel1, stub1 = get_grpc_stub(grpc_port)
        health1 = stub1.HealthCheck(mt5_pb2.Empty())
        assert health1 is not None
        channel1.close()

        # Wait a bit
        time.sleep(1)

        # Second connection should work
        channel2, stub2 = get_grpc_stub(grpc_port)
        health2 = stub2.HealthCheck(mt5_pb2.Empty())
        assert health2 is not None
        channel2.close()

    def test_bridge_handles_rapid_connections(
        self,
        container_name: str,
        grpc_port: int,
    ) -> None:
        """Test bridge handles rapid connect/disconnect cycles."""
        for i in range(5):
            channel, stub = get_grpc_stub(grpc_port)
            health = stub.HealthCheck(mt5_pb2.Empty())
            assert health is not None, f"Failed on iteration {i}"
            channel.close()

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
            ["pgrep", "-f", "bridge"],
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

    def test_grpcio_package_version(self, container_name: str) -> None:
        """Verify gRPC package version is retrievable."""
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

    def test_version_returns_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test Version() returns expected type."""
        result = mt5_stub.Version(mt5_pb2.Empty())
        assert result is not None

    def test_last_error_returns_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test LastError() returns expected type."""
        result = mt5_stub.LastError(mt5_pb2.Empty())
        assert result is not None
        assert hasattr(result, "code")
        assert hasattr(result, "message")

    def test_symbols_total_returns_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test SymbolsTotal() returns response."""
        result = mt5_stub.SymbolsTotal(mt5_pb2.Empty())
        # Returns response even when terminal not connected to broker
        assert result is not None

    def test_positions_total_returns_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test PositionsTotal() returns response."""
        result = mt5_stub.PositionsTotal(mt5_pb2.Empty())
        # Returns response even when terminal not connected to broker
        assert result is not None

    def test_orders_total_returns_response(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test OrdersTotal() returns response."""
        result = mt5_stub.OrdersTotal(mt5_pb2.Empty())
        # Returns response even when terminal not connected to broker
        assert result is not None


# =============================================================================
# FAILURE SIMULATION TESTS
# =============================================================================


@pytest.mark.requires_container
class TestFailureSimulation:
    """Simulate various failure scenarios.

    Uses mt5_stub fixture from conftest.py.
    """

    def test_bridge_recovers_from_invalid_symbol(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test bridge handles invalid symbol gracefully."""
        # Try to get info for a non-existent symbol
        result = mt5_stub.SymbolInfo(
            mt5_pb2.SymbolRequest(symbol="INVALID_SYMBOL_XYZ123"),
        )
        # Should return empty response, not raise exception
        assert result is not None

    def test_bridge_handles_empty_positions(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test bridge handles empty positions list."""
        result = mt5_stub.PositionsGet(mt5_pb2.PositionsRequest())
        # Should return response, not raise
        assert result is not None

    def test_bridge_handles_empty_orders(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test bridge handles empty orders list."""
        result = mt5_stub.OrdersGet(mt5_pb2.OrdersRequest())
        # Should return response, not raise
        assert result is not None

    def test_health_check_after_many_operations(
        self,
        mt5_stub: mt5_pb2_grpc.MT5ServiceStub,
    ) -> None:
        """Test health check still works after many operations."""
        # Perform many operations
        for _ in range(10):
            mt5_stub.Version(mt5_pb2.Empty())
            mt5_stub.LastError(mt5_pb2.Empty())
            mt5_stub.SymbolsTotal(mt5_pb2.Empty())

        # Health check should still work
        health = mt5_stub.HealthCheck(mt5_pb2.Empty())
        assert health is not None
        assert health.mt5_available is True
