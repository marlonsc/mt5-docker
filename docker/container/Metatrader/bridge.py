"""gRPC bridge for MetaTrader5 - runs inside Wine.

This module provides the MT5GRPCServicer gRPC server that runs inside Wine
with Windows Python + MetaTrader5 module.

STANDALONE: This file has NO dependencies on other mt5linux modules.
Copy only this file + grpcio + protobuf + generated pb2 files to Wine.

Features:
- gRPC-based service (replaces RPyC)
- Concurrent request handling via ThreadPoolExecutor
- Signal handling (SIGTERM/SIGINT) for clean container stops
- Data materialization (_asdict() for NamedTuples)
- Chunked symbols_get for large datasets (9000+)
- Debug logging for every function call
- NO STUBS - fails if MT5 unavailable
- Complete MT5 API coverage including Market Depth (DOM)
- MT5 constants exposed for client usage
- Secure: no raw module exposure, controlled API surface
- JSON serialization for dict data
- Numpy arrays serialized as bytes

Usage:
    wine python.exe -m mt5linux.bridge --host 0.0.0.0 --port 50051
    wine python.exe bridge.py --host 0.0.0.0 --port 50051 --debug
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
from concurrent import futures
from typing import TYPE_CHECKING

import grpc
import MetaTrader5  # pyright: ignore[reportMissingImports]

from . import mt5_pb2, mt5_pb2_grpc

if TYPE_CHECKING:
    from datetime import datetime
    from types import FrameType, ModuleType

    import numpy as np
    from numpy.typing import NDArray

# Module logger
log = logging.getLogger("mt5bridge")

# Global server reference for signal handler
_server: grpc.Server | None = None


# =============================================================================
# JSON Value Types (for strict typing without Any)
# =============================================================================

# JSON-compatible value types for serialization
JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]


def _json_serialize(data: dict[str, JSONValue]) -> str:
    """Serialize dict to JSON string.

    Args:
        data: Dictionary with JSON-compatible values.

    Returns:
        JSON string representation.

    """
    return json.dumps(data, default=str)


def _json_deserialize(json_str: str) -> dict[str, JSONValue]:
    """Deserialize JSON string to dict.

    Args:
        json_str: JSON string to parse.

    Returns:
        Parsed dictionary.

    """
    result: dict[str, JSONValue] = json.loads(json_str)
    return result


# =============================================================================
# MT5 gRPC Servicer Implementation
# =============================================================================


class MT5GRPCServicer(mt5_pb2_grpc.MT5ServiceServicer):
    """gRPC service implementation for MetaTrader5.

    Implements all RPC methods defined in mt5.proto, handling:
    - Connection lifecycle (initialize, login, shutdown)
    - Account/terminal information
    - Symbol operations
    - Market data (rates, ticks)
    - Trading operations (orders, positions)
    - History queries
    - Market depth (DOM)
    """

    _mt5_module: ModuleType = MetaTrader5
    _mt5_lock: threading.RLock = threading.RLock()

    def __init__(self) -> None:
        """Initialize the MT5 gRPC servicer and connect to MT5 terminal."""
        super().__init__()
        log.info("MT5GRPCServicer initializing...")

        # Auto-initialize connection to MT5 terminal
        if self._mt5_module is not None:
            result = self._mt5_module.initialize()
            if result:
                log.info("MT5 auto-initialize: SUCCESS")
            else:
                error = self._mt5_module.last_error()
                log.warning("MT5 auto-initialize: FAILED - %s", error)
        else:
            log.warning("MT5 module not available for auto-initialize")

        log.info("MT5GRPCServicer initialized")

    # =========================================================================
    # HELPER FUNCTIONS (PRIVATE)
    # =========================================================================

    def _ensure_mt5_loaded(self) -> None:
        """Ensure MT5 module is loaded, raise RuntimeError if not.

        Raises:
            RuntimeError: If MT5 module is not available.

        """
        if self._mt5_module is None:
            msg = "MT5 module not loaded - initialize first"
            raise RuntimeError(msg)

    def _namedtuple_to_dict(
        self,
        obj: object,
        nested_fields: list[str] | None = None,
    ) -> dict[str, JSONValue]:
        """Convert namedtuple to JSON-serializable dict.

        Args:
            obj: Object with _asdict() method (namedtuple-like).
            nested_fields: Field names containing nested namedtuples.

        Returns:
            Dictionary representation.

        """
        if not hasattr(obj, "_asdict"):
            return {}
        data: dict[str, JSONValue] = obj._asdict()
        if nested_fields:
            for field in nested_fields:
                nested = data.get(field)
                if nested is not None and hasattr(nested, "_asdict"):
                    data[field] = nested._asdict()
        return data

    def _numpy_to_proto(
        self,
        arr: NDArray[np.void] | None,
    ) -> mt5_pb2.NumpyArray:
        """Convert numpy array to protobuf NumpyArray message.

        Args:
            arr: Numpy structured array or None.

        Returns:
            NumpyArray protobuf message.

        """
        if arr is None:
            return mt5_pb2.NumpyArray(data=b"", dtype="", shape=[])
        return mt5_pb2.NumpyArray(
            data=arr.tobytes(),
            dtype=str(arr.dtype),
            shape=list(arr.shape),
        )

    def _validate_symbol(self, symbol: str, func_name: str) -> bool:
        """Validate symbol is not empty.

        Args:
            symbol: Symbol to validate.
            func_name: Function name for logging.

        Returns:
            True if valid, False otherwise.

        """
        if not symbol:
            log.debug("%s: empty symbol", func_name)
            return False
        return True

    def _validate_count(self, count: int, func_name: str) -> bool:
        """Validate count is positive.

        Args:
            count: Count to validate.
            func_name: Function name for logging.

        Returns:
            True if valid, False otherwise.

        """
        if count <= 0:
            log.warning("%s: invalid count=%s", func_name, count)
            return False
        return True

    def _validate_date_range(
        self,
        date_from: datetime | int,
        date_to: datetime | int,
        func_name: str,
    ) -> bool:
        """Validate date_from <= date_to.

        Args:
            date_from: Start date (datetime or Unix timestamp).
            date_to: End date (datetime or Unix timestamp).
            func_name: Function name for logging.

        Returns:
            True if valid, False otherwise.

        """
        from_val: float
        to_val: float
        if isinstance(date_from, (int, float)):
            from_val = float(date_from)
        else:
            from_val = date_from.timestamp()
        if isinstance(date_to, (int, float)):
            to_val = float(date_to)
        else:
            to_val = date_to.timestamp()

        if from_val > to_val:
            log.warning(
                "%s: invalid range from=%s > to=%s",
                func_name,
                date_from,
                date_to,
            )
            return False
        return True

    # =========================================================================
    # TERMINAL OPERATIONS
    # =========================================================================

    def HealthCheck(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.HealthStatus:
        """Check MT5 service health status.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            HealthStatus with connection and terminal state.

        """
        log.debug("HealthCheck: called")

        if self._mt5_module is None:
            log.debug("HealthCheck: MT5 module not loaded")
            return mt5_pb2.HealthStatus(
                healthy=False,
                mt5_available=False,
                connected=False,
                trade_allowed=False,
                build=0,
                reason="MT5 module not loaded",
            )

        terminal = self._mt5_module.terminal_info()
        if terminal is None:
            error = self._mt5_module.last_error()
            log.debug("HealthCheck: terminal_info failed: %s", error)
            return mt5_pb2.HealthStatus(
                healthy=False,
                mt5_available=True,
                connected=False,
                trade_allowed=False,
                build=0,
                reason=f"Terminal not connected: {error}",
            )

        log.debug(
            "HealthCheck: connected=%s trade_allowed=%s",
            terminal.connected,
            terminal.trade_allowed,
        )
        return mt5_pb2.HealthStatus(
            healthy=terminal.connected,
            mt5_available=True,
            connected=terminal.connected,
            trade_allowed=terminal.trade_allowed,
            build=terminal.build,
            reason="",
        )

    def Initialize(
        self,
        request: mt5_pb2.InitRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.BoolResponse:
        """Initialize MT5 terminal connection.

        Args:
            request: Initialization parameters (path, login, password, etc.).
            context: gRPC servicer context.

        Returns:
            BoolResponse indicating success or failure.

        """
        self._ensure_mt5_loaded()
        log.debug(
            "Initialize: path=%s login=%s server=%s timeout=%s portable=%s",
            request.path if request.HasField("_path") else None,
            request.login if request.HasField("_login") else None,
            request.server if request.HasField("_server") else None,
            request.timeout if request.HasField("_timeout") else None,
            request.portable,
        )

        kwargs: dict[str, str | int | bool] = {}
        if request.HasField("_path"):
            kwargs["path"] = request.path
        if request.HasField("_login"):
            kwargs["login"] = request.login
        if request.HasField("_password"):
            kwargs["password"] = request.password
        if request.HasField("_server"):
            kwargs["server"] = request.server
        if request.HasField("_timeout"):
            kwargs["timeout"] = request.timeout
        if request.portable:
            kwargs["portable"] = request.portable

        result = self._mt5_module.initialize(**kwargs)
        log.info("Initialize: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def Login(
        self,
        request: mt5_pb2.LoginRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.BoolResponse:
        """Login to MT5 account.

        Args:
            request: Login credentials (login, password, server, timeout).
            context: gRPC servicer context.

        Returns:
            BoolResponse indicating success or failure.

        """
        log.debug(
            "Login: login=%s server=%s timeout=%s",
            request.login,
            request.server,
            request.timeout,
        )
        result = self._mt5_module.login(
            login=request.login,
            password=request.password,
            server=request.server,
            timeout=request.timeout,
        )
        log.info("Login: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def Shutdown(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.Empty:
        """Shutdown MT5 terminal connection.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            Empty response.

        """
        log.debug("Shutdown: called")
        self._mt5_module.shutdown()
        log.info("Shutdown: completed")
        return mt5_pb2.Empty()

    def Version(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.MT5Version:
        """Get MT5 terminal version.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            MT5Version with major, minor, and build information.

        """
        log.debug("Version: called")
        result = self._mt5_module.version()
        log.debug("Version: result=%s", result)
        if result is None:
            return mt5_pb2.MT5Version(major=0, minor=0, build="")
        return mt5_pb2.MT5Version(
            major=result[0],
            minor=result[1],
            build=str(result[2]),
        )

    def LastError(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.ErrorInfo:
        """Get last MT5 error code and description.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            ErrorInfo with error code and message.

        """
        log.debug("LastError: called")
        result = self._mt5_module.last_error()
        log.debug("LastError: result=%s", result)
        return mt5_pb2.ErrorInfo(code=result[0], message=result[1])

    def GetConstants(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.Constants:
        """Get all MT5 constants for client-side usage.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            Constants message with map of constant names to values.

        """
        self._ensure_mt5_loaded()
        log.debug("GetConstants: called")
        mt5 = self._mt5_module
        constants: dict[str, int] = {}

        constant_names = [
            # Timeframes
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
            # Order types
            "ORDER_TYPE_BUY",
            "ORDER_TYPE_SELL",
            "ORDER_TYPE_BUY_LIMIT",
            "ORDER_TYPE_SELL_LIMIT",
            "ORDER_TYPE_BUY_STOP",
            "ORDER_TYPE_SELL_STOP",
            "ORDER_TYPE_BUY_STOP_LIMIT",
            "ORDER_TYPE_SELL_STOP_LIMIT",
            "ORDER_TYPE_CLOSE_BY",
            # Trade actions
            "TRADE_ACTION_DEAL",
            "TRADE_ACTION_PENDING",
            "TRADE_ACTION_SLTP",
            "TRADE_ACTION_MODIFY",
            "TRADE_ACTION_REMOVE",
            "TRADE_ACTION_CLOSE_BY",
            # Order filling modes
            "ORDER_FILLING_FOK",
            "ORDER_FILLING_IOC",
            "ORDER_FILLING_RETURN",
            "ORDER_FILLING_BOC",
            # Order time types
            "ORDER_TIME_GTC",
            "ORDER_TIME_DAY",
            "ORDER_TIME_SPECIFIED",
            "ORDER_TIME_SPECIFIED_DAY",
            # Position types
            "POSITION_TYPE_BUY",
            "POSITION_TYPE_SELL",
            # Deal types
            "DEAL_TYPE_BUY",
            "DEAL_TYPE_SELL",
            "DEAL_TYPE_BALANCE",
            "DEAL_TYPE_CREDIT",
            "DEAL_TYPE_CHARGE",
            "DEAL_TYPE_CORRECTION",
            "DEAL_TYPE_BONUS",
            "DEAL_TYPE_COMMISSION",
            # Copy ticks flags
            "COPY_TICKS_ALL",
            "COPY_TICKS_INFO",
            "COPY_TICKS_TRADE",
            # Book types
            "BOOK_TYPE_SELL",
            "BOOK_TYPE_BUY",
            "BOOK_TYPE_SELL_MARKET",
            "BOOK_TYPE_BUY_MARKET",
            # Trade return codes
            "TRADE_RETCODE_REQUOTE",
            "TRADE_RETCODE_REJECT",
            "TRADE_RETCODE_CANCEL",
            "TRADE_RETCODE_PLACED",
            "TRADE_RETCODE_DONE",
            "TRADE_RETCODE_DONE_PARTIAL",
            "TRADE_RETCODE_ERROR",
            "TRADE_RETCODE_TIMEOUT",
            "TRADE_RETCODE_INVALID",
            "TRADE_RETCODE_INVALID_VOLUME",
            "TRADE_RETCODE_INVALID_PRICE",
            "TRADE_RETCODE_INVALID_STOPS",
            "TRADE_RETCODE_TRADE_DISABLED",
            "TRADE_RETCODE_MARKET_CLOSED",
            "TRADE_RETCODE_NO_MONEY",
            "TRADE_RETCODE_PRICE_CHANGED",
            "TRADE_RETCODE_PRICE_OFF",
            "TRADE_RETCODE_INVALID_EXPIRATION",
            "TRADE_RETCODE_ORDER_CHANGED",
            "TRADE_RETCODE_TOO_MANY_REQUESTS",
        ]

        for name in constant_names:
            if hasattr(mt5, name):
                value = getattr(mt5, name)
                if isinstance(value, int):
                    constants[name] = value

        log.debug("GetConstants: returned %s constants", len(constants))
        return mt5_pb2.Constants(values=constants)

    # =========================================================================
    # ACCOUNT/TERMINAL INFO
    # =========================================================================

    def TerminalInfo(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Get terminal information.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized terminal information.

        """
        self._ensure_mt5_loaded()
        log.debug("TerminalInfo: called")
        result = self._mt5_module.terminal_info()
        if result is None:
            log.debug("TerminalInfo: result=None")
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result)
        log.debug("TerminalInfo: returned terminal info")
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    def AccountInfo(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Get account information.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized account information.

        """
        self._ensure_mt5_loaded()
        log.debug("AccountInfo: called")
        result = self._mt5_module.account_info()
        if result is None:
            log.debug("AccountInfo: result=None")
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result)
        log.debug("AccountInfo: login=%s", data.get("login"))
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    # =========================================================================
    # SYMBOL OPERATIONS
    # =========================================================================

    def SymbolsTotal(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.IntResponse:
        """Get total number of available symbols.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            IntResponse with symbol count.

        """
        log.debug("SymbolsTotal: called")
        result = self._mt5_module.symbols_total()
        log.debug("SymbolsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result else 0)

    def SymbolsGet(
        self,
        request: mt5_pb2.SymbolsRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.SymbolsResponse:
        """Get available symbols with optional group filter.

        Returns chunked JSON for large datasets to prevent memory issues.

        Args:
            request: Optional group filter pattern.
            context: gRPC servicer context.

        Returns:
            SymbolsResponse with total count and JSON chunks.

        """
        group: str | None = None
        if request.HasField("_group"):
            group = request.group
        log.debug("SymbolsGet: group=%s", group)

        if group:
            result = self._mt5_module.symbols_get(group=group)
        else:
            result = self._mt5_module.symbols_get()

        if result is None:
            log.debug("SymbolsGet: result=None")
            return mt5_pb2.SymbolsResponse(total=0, chunks=[])

        items = list(result)
        total = len(items)
        log.debug("SymbolsGet: total=%s symbols", total)

        chunk_size = 500
        chunks: list[str] = []
        for i in range(0, total, chunk_size):
            chunk_items = items[i : i + chunk_size]
            chunk_data = [self._namedtuple_to_dict(s) for s in chunk_items]
            chunks.append(json.dumps(chunk_data, default=str))

        log.debug("SymbolsGet: returned %s chunks", len(chunks))
        return mt5_pb2.SymbolsResponse(total=total, chunks=chunks)

    def SymbolInfo(
        self,
        request: mt5_pb2.SymbolRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Get detailed symbol information.

        Args:
            request: Symbol name to query.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized symbol information.

        """
        self._ensure_mt5_loaded()
        log.debug("SymbolInfo: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "SymbolInfo"):
            return mt5_pb2.DictData(json_data="")
        result = self._mt5_module.symbol_info(request.symbol)
        if result is None:
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result)
        log.debug("SymbolInfo: found symbol")
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    def SymbolInfoTick(
        self,
        request: mt5_pb2.SymbolRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Get current tick data for a symbol.

        Args:
            request: Symbol name to query.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized tick information.

        """
        self._ensure_mt5_loaded()
        log.debug("SymbolInfoTick: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "SymbolInfoTick"):
            return mt5_pb2.DictData(json_data="")
        result = self._mt5_module.symbol_info_tick(request.symbol)
        if result is None:
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result)
        log.debug(
            "SymbolInfoTick: bid=%s ask=%s",
            data.get("bid"),
            data.get("ask"),
        )
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    def SymbolSelect(
        self,
        request: mt5_pb2.SymbolSelectRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.BoolResponse:
        """Select or deselect symbol in Market Watch.

        Args:
            request: Symbol name and enable flag.
            context: gRPC servicer context.

        Returns:
            BoolResponse indicating success or failure.

        """
        log.debug(
            "SymbolSelect: symbol=%s enable=%s",
            request.symbol,
            request.enable,
        )
        if not self._validate_symbol(request.symbol, "SymbolSelect"):
            return mt5_pb2.BoolResponse(result=False)
        result = self._mt5_module.symbol_select(request.symbol, request.enable)
        log.debug("SymbolSelect: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    # =========================================================================
    # MARKET DATA - RATES
    # =========================================================================

    def CopyRatesFrom(
        self,
        request: mt5_pb2.CopyRatesRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.NumpyArray:
        """Copy OHLCV rates from a specific date.

        Args:
            request: Symbol, timeframe, date_from (timestamp), and count.
            context: gRPC servicer context.

        Returns:
            NumpyArray with serialized rate data.

        """
        log.debug(
            "CopyRatesFrom: symbol=%s tf=%s date=%s count=%s",
            request.symbol,
            request.timeframe,
            request.date_from,
            request.count,
        )
        if not self._validate_symbol(request.symbol, "CopyRatesFrom"):
            return self._numpy_to_proto(None)
        if not self._validate_count(request.count, "CopyRatesFrom"):
            return self._numpy_to_proto(None)
        result = self._mt5_module.copy_rates_from(
            request.symbol,
            request.timeframe,
            request.date_from,
            request.count,
        )
        log.debug(
            "CopyRatesFrom: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyRatesFromPos(
        self,
        request: mt5_pb2.CopyRatesPosRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.NumpyArray:
        """Copy OHLCV rates from a bar position.

        Args:
            request: Symbol, timeframe, start_pos, and count.
            context: gRPC servicer context.

        Returns:
            NumpyArray with serialized rate data.

        """
        log.debug(
            "CopyRatesFromPos: symbol=%s tf=%s pos=%s count=%s",
            request.symbol,
            request.timeframe,
            request.start_pos,
            request.count,
        )
        if not self._validate_symbol(request.symbol, "CopyRatesFromPos"):
            return self._numpy_to_proto(None)
        if not self._validate_count(request.count, "CopyRatesFromPos"):
            return self._numpy_to_proto(None)
        result = self._mt5_module.copy_rates_from_pos(
            request.symbol,
            request.timeframe,
            request.start_pos,
            request.count,
        )
        log.debug(
            "CopyRatesFromPos: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyRatesRange(
        self,
        request: mt5_pb2.CopyRatesRangeRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.NumpyArray:
        """Copy OHLCV rates in a date range.

        Args:
            request: Symbol, timeframe, date_from, and date_to (timestamps).
            context: gRPC servicer context.

        Returns:
            NumpyArray with serialized rate data.

        """
        log.debug(
            "CopyRatesRange: symbol=%s tf=%s from=%s to=%s",
            request.symbol,
            request.timeframe,
            request.date_from,
            request.date_to,
        )
        if not self._validate_symbol(request.symbol, "CopyRatesRange"):
            return self._numpy_to_proto(None)
        if not self._validate_date_range(
            request.date_from,
            request.date_to,
            "CopyRatesRange",
        ):
            return self._numpy_to_proto(None)
        result = self._mt5_module.copy_rates_range(
            request.symbol,
            request.timeframe,
            request.date_from,
            request.date_to,
        )
        log.debug(
            "CopyRatesRange: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    # =========================================================================
    # MARKET DATA - TICKS
    # =========================================================================

    def CopyTicksFrom(
        self,
        request: mt5_pb2.CopyTicksRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.NumpyArray:
        """Copy tick data from a specific date.

        Args:
            request: Symbol, date_from (timestamp), count, and flags.
            context: gRPC servicer context.

        Returns:
            NumpyArray with serialized tick data.

        """
        log.debug(
            "CopyTicksFrom: symbol=%s date=%s count=%s flags=%s",
            request.symbol,
            request.date_from,
            request.count,
            request.flags,
        )
        if not self._validate_symbol(request.symbol, "CopyTicksFrom"):
            return self._numpy_to_proto(None)
        if not self._validate_count(request.count, "CopyTicksFrom"):
            return self._numpy_to_proto(None)
        result = self._mt5_module.copy_ticks_from(
            request.symbol,
            request.date_from,
            request.count,
            request.flags,
        )
        log.debug(
            "CopyTicksFrom: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyTicksRange(
        self,
        request: mt5_pb2.CopyTicksRangeRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.NumpyArray:
        """Copy tick data in a date range.

        Args:
            request: Symbol, date_from, date_to (timestamps), and flags.
            context: gRPC servicer context.

        Returns:
            NumpyArray with serialized tick data.

        """
        log.debug(
            "CopyTicksRange: symbol=%s from=%s to=%s flags=%s",
            request.symbol,
            request.date_from,
            request.date_to,
            request.flags,
        )
        if not self._validate_symbol(request.symbol, "CopyTicksRange"):
            return self._numpy_to_proto(None)
        if not self._validate_date_range(
            request.date_from,
            request.date_to,
            "CopyTicksRange",
        ):
            return self._numpy_to_proto(None)
        result = self._mt5_module.copy_ticks_range(
            request.symbol,
            request.date_from,
            request.date_to,
            request.flags,
        )
        log.debug(
            "CopyTicksRange: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    # =========================================================================
    # TRADING OPERATIONS
    # =========================================================================

    def OrderCalcMargin(
        self,
        request: mt5_pb2.MarginRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.FloatResponse:
        """Calculate margin required for an order.

        Args:
            request: Action type, symbol, volume, and price.
            context: gRPC servicer context.

        Returns:
            FloatResponse with margin value or None.

        """
        log.debug(
            "OrderCalcMargin: action=%s symbol=%s vol=%s price=%s",
            request.action,
            request.symbol,
            request.volume,
            request.price,
        )
        result = self._mt5_module.order_calc_margin(
            request.action,
            request.symbol,
            request.volume,
            request.price,
        )
        log.debug("OrderCalcMargin: result=%s", result)
        if result is None:
            return mt5_pb2.FloatResponse()
        return mt5_pb2.FloatResponse(value=float(result))

    def OrderCalcProfit(
        self,
        request: mt5_pb2.ProfitRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.FloatResponse:
        """Calculate potential profit for an order.

        Args:
            request: Action, symbol, volume, price_open, and price_close.
            context: gRPC servicer context.

        Returns:
            FloatResponse with profit value or None.

        """
        log.debug(
            "OrderCalcProfit: action=%s symbol=%s vol=%s open=%s close=%s",
            request.action,
            request.symbol,
            request.volume,
            request.price_open,
            request.price_close,
        )
        result = self._mt5_module.order_calc_profit(
            request.action,
            request.symbol,
            request.volume,
            request.price_open,
            request.price_close,
        )
        log.debug("OrderCalcProfit: result=%s", result)
        if result is None:
            return mt5_pb2.FloatResponse()
        return mt5_pb2.FloatResponse(value=float(result))

    def OrderCheck(
        self,
        request: mt5_pb2.OrderRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Check order validity without sending.

        Args:
            request: JSON-serialized order request dict.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized order check result.

        """
        self._ensure_mt5_loaded()
        log.debug("OrderCheck: request=%s", request.json_request)
        order_dict = _json_deserialize(request.json_request)
        result = self._mt5_module.order_check(order_dict)
        if result is None:
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result, nested_fields=["request"])
        log.debug("OrderCheck: retcode=%s", data.get("retcode"))
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    def OrderSend(
        self,
        request: mt5_pb2.OrderRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictData:
        """Send trading order to MT5.

        Args:
            request: JSON-serialized order request dict.
            context: gRPC servicer context.

        Returns:
            DictData with JSON-serialized order result.

        """
        self._ensure_mt5_loaded()
        log.debug("OrderSend: request=%s", request.json_request)
        order_dict = _json_deserialize(request.json_request)
        result = self._mt5_module.order_send(order_dict)
        if result is None:
            return mt5_pb2.DictData(json_data="")
        data = self._namedtuple_to_dict(result, nested_fields=["request"])
        log.info(
            "OrderSend: retcode=%s order=%s deal=%s",
            data.get("retcode"),
            data.get("order"),
            data.get("deal"),
        )
        return mt5_pb2.DictData(json_data=_json_serialize(data))

    # =========================================================================
    # POSITION OPERATIONS
    # =========================================================================

    def PositionsTotal(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.IntResponse:
        """Get total number of open positions.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            IntResponse with position count.

        """
        log.debug("PositionsTotal: called")
        result = self._mt5_module.positions_total()
        log.debug("PositionsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result else 0)

    def PositionsGet(
        self,
        request: mt5_pb2.PositionsRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictList:
        """Get open positions with optional filters.

        Args:
            request: Optional symbol, group, or ticket filter.
            context: gRPC servicer context.

        Returns:
            DictList with JSON-serialized position data.

        """
        self._ensure_mt5_loaded()
        log.debug(
            "PositionsGet: symbol=%s group=%s ticket=%s",
            request.symbol if request.HasField("_symbol") else None,
            request.group if request.HasField("_group") else None,
            request.ticket if request.HasField("_ticket") else None,
        )
        kwargs: dict[str, str | int] = {}
        if request.HasField("_symbol"):
            kwargs["symbol"] = request.symbol
        if request.HasField("_group"):
            kwargs["group"] = request.group
        if request.HasField("_ticket"):
            kwargs["ticket"] = request.ticket

        if kwargs:
            result = self._mt5_module.positions_get(**kwargs)
        else:
            result = self._mt5_module.positions_get()

        if result is None:
            log.debug("PositionsGet: result=None")
            return mt5_pb2.DictList(json_items=[])

        json_items = [_json_serialize(self._namedtuple_to_dict(p)) for p in result]
        log.debug("PositionsGet: returned %s positions", len(json_items))
        return mt5_pb2.DictList(json_items=json_items)

    # =========================================================================
    # ORDER OPERATIONS
    # =========================================================================

    def OrdersTotal(
        self,
        request: mt5_pb2.Empty,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.IntResponse:
        """Get total number of pending orders.

        Args:
            request: Empty request.
            context: gRPC servicer context.

        Returns:
            IntResponse with order count.

        """
        log.debug("OrdersTotal: called")
        result = self._mt5_module.orders_total()
        log.debug("OrdersTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result else 0)

    def OrdersGet(
        self,
        request: mt5_pb2.OrdersRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictList:
        """Get pending orders with optional filters.

        Args:
            request: Optional symbol, group, or ticket filter.
            context: gRPC servicer context.

        Returns:
            DictList with JSON-serialized order data.

        """
        self._ensure_mt5_loaded()
        log.debug(
            "OrdersGet: symbol=%s group=%s ticket=%s",
            request.symbol if request.HasField("_symbol") else None,
            request.group if request.HasField("_group") else None,
            request.ticket if request.HasField("_ticket") else None,
        )
        kwargs: dict[str, str | int] = {}
        if request.HasField("_symbol"):
            kwargs["symbol"] = request.symbol
        if request.HasField("_group"):
            kwargs["group"] = request.group
        if request.HasField("_ticket"):
            kwargs["ticket"] = request.ticket

        if kwargs:
            result = self._mt5_module.orders_get(**kwargs)
        else:
            result = self._mt5_module.orders_get()

        if result is None:
            log.debug("OrdersGet: result=None")
            return mt5_pb2.DictList(json_items=[])

        json_items = [_json_serialize(self._namedtuple_to_dict(o)) for o in result]
        log.debug("OrdersGet: returned %s orders", len(json_items))
        return mt5_pb2.DictList(json_items=json_items)

    # =========================================================================
    # HISTORY OPERATIONS
    # =========================================================================

    def HistoryOrdersTotal(
        self,
        request: mt5_pb2.HistoryRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.IntResponse:
        """Get total count of historical orders in date range.

        Args:
            request: date_from and date_to timestamps.
            context: gRPC servicer context.

        Returns:
            IntResponse with order count.

        """
        log.debug(
            "HistoryOrdersTotal: from=%s to=%s",
            request.date_from if request.HasField("_date_from") else None,
            request.date_to if request.HasField("_date_to") else None,
        )
        if not request.HasField("_date_from") or not request.HasField(
            "_date_to",
        ):
            return mt5_pb2.IntResponse(value=0)
        result = self._mt5_module.history_orders_total(
            request.date_from,
            request.date_to,
        )
        log.debug("HistoryOrdersTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result else 0)

    def HistoryOrdersGet(
        self,
        request: mt5_pb2.HistoryRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictList:
        """Get historical orders with filters.

        Args:
            request: Optional date range, group, ticket, or position filter.
            context: gRPC servicer context.

        Returns:
            DictList with JSON-serialized historical order data.

        """
        self._ensure_mt5_loaded()
        log.debug(
            "HistoryOrdersGet: from=%s to=%s group=%s ticket=%s pos=%s",
            request.date_from if request.HasField("_date_from") else None,
            request.date_to if request.HasField("_date_to") else None,
            request.group if request.HasField("_group") else None,
            request.ticket if request.HasField("_ticket") else None,
            request.position if request.HasField("_position") else None,
        )

        kwargs: dict[str, str | int] = {}
        if request.HasField("_group"):
            kwargs["group"] = request.group
        if request.HasField("_ticket"):
            kwargs["ticket"] = request.ticket
        if request.HasField("_position"):
            kwargs["position"] = request.position

        if request.HasField("_date_from") and request.HasField("_date_to"):
            result = self._mt5_module.history_orders_get(
                request.date_from,
                request.date_to,
                **kwargs,
            )
        elif kwargs:
            result = self._mt5_module.history_orders_get(**kwargs)
        else:
            result = self._mt5_module.history_orders_get()

        if result is None:
            return mt5_pb2.DictList(json_items=[])

        json_items = [_json_serialize(self._namedtuple_to_dict(o)) for o in result]
        log.debug("HistoryOrdersGet: returned %s orders", len(json_items))
        return mt5_pb2.DictList(json_items=json_items)

    def HistoryDealsTotal(
        self,
        request: mt5_pb2.HistoryRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.IntResponse:
        """Get total count of historical deals in date range.

        Args:
            request: date_from and date_to timestamps.
            context: gRPC servicer context.

        Returns:
            IntResponse with deal count.

        """
        log.debug(
            "HistoryDealsTotal: from=%s to=%s",
            request.date_from if request.HasField("_date_from") else None,
            request.date_to if request.HasField("_date_to") else None,
        )
        if not request.HasField("_date_from") or not request.HasField(
            "_date_to",
        ):
            return mt5_pb2.IntResponse(value=0)
        result = self._mt5_module.history_deals_total(
            request.date_from,
            request.date_to,
        )
        log.debug("HistoryDealsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result else 0)

    def HistoryDealsGet(
        self,
        request: mt5_pb2.HistoryRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictList:
        """Get historical deals with filters.

        Args:
            request: Optional date range, group, ticket, or position filter.
            context: gRPC servicer context.

        Returns:
            DictList with JSON-serialized historical deal data.

        """
        self._ensure_mt5_loaded()
        log.debug(
            "HistoryDealsGet: from=%s to=%s group=%s ticket=%s pos=%s",
            request.date_from if request.HasField("_date_from") else None,
            request.date_to if request.HasField("_date_to") else None,
            request.group if request.HasField("_group") else None,
            request.ticket if request.HasField("_ticket") else None,
            request.position if request.HasField("_position") else None,
        )

        kwargs: dict[str, str | int] = {}
        if request.HasField("_group"):
            kwargs["group"] = request.group
        if request.HasField("_ticket"):
            kwargs["ticket"] = request.ticket
        if request.HasField("_position"):
            kwargs["position"] = request.position

        if request.HasField("_date_from") and request.HasField("_date_to"):
            result = self._mt5_module.history_deals_get(
                request.date_from,
                request.date_to,
                **kwargs,
            )
        elif kwargs:
            result = self._mt5_module.history_deals_get(**kwargs)
        else:
            result = self._mt5_module.history_deals_get()

        if result is None:
            return mt5_pb2.DictList(json_items=[])

        json_items = [_json_serialize(self._namedtuple_to_dict(d)) for d in result]
        log.debug("HistoryDealsGet: returned %s deals", len(json_items))
        return mt5_pb2.DictList(json_items=json_items)

    # =========================================================================
    # MARKET DEPTH (DOM) OPERATIONS
    # =========================================================================

    def MarketBookAdd(
        self,
        request: mt5_pb2.SymbolRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.BoolResponse:
        """Subscribe to market depth (DOM) for a symbol.

        Must be called before MarketBookGet to receive updates.

        Args:
            request: Symbol name to subscribe.
            context: gRPC servicer context.

        Returns:
            BoolResponse indicating success or failure.

        """
        log.debug("MarketBookAdd: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookAdd"):
            return mt5_pb2.BoolResponse(result=False)
        result = self._mt5_module.market_book_add(request.symbol)
        log.debug("MarketBookAdd: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def MarketBookGet(
        self,
        request: mt5_pb2.SymbolRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.DictList:
        """Get market depth (DOM) data for a symbol.

        Requires prior MarketBookAdd call.

        Args:
            request: Symbol name to query.
            context: gRPC servicer context.

        Returns:
            DictList with JSON-serialized book entries.

        """
        self._ensure_mt5_loaded()
        log.debug("MarketBookGet: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookGet"):
            return mt5_pb2.DictList(json_items=[])
        result = self._mt5_module.market_book_get(request.symbol)
        if result is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [_json_serialize(self._namedtuple_to_dict(e)) for e in result]
        log.debug("MarketBookGet: returned %s entries", len(json_items))
        return mt5_pb2.DictList(json_items=json_items)

    def MarketBookRelease(
        self,
        request: mt5_pb2.SymbolRequest,
        context: grpc.ServicerContext,
    ) -> mt5_pb2.BoolResponse:
        """Unsubscribe from market depth (DOM) for a symbol.

        Args:
            request: Symbol name to unsubscribe.
            context: gRPC servicer context.

        Returns:
            BoolResponse indicating success or failure.

        """
        log.debug("MarketBookRelease: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookRelease"):
            return mt5_pb2.BoolResponse(result=False)
        result = self._mt5_module.market_book_release(request.symbol)
        log.debug("MarketBookRelease: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))


# =============================================================================
# SERVER SETUP AND LIFECYCLE
# =============================================================================


def _setup_logging(*, debug: bool = False) -> None:
    """Configure logging for the bridge.

    Args:
        debug: Enable debug-level logging if True.

    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _graceful_shutdown(signum: int, frame: FrameType | None) -> None:
    """Handle shutdown signals for clean container stops.

    Args:
        signum: Signal number received.
        frame: Current stack frame (unused).

    """
    del frame  # Unused parameter
    sig_name = signal.Signals(signum).name
    log.info("Received %s, shutting down gracefully...", sig_name)
    if _server is not None:
        _server.stop(grace=5)
    sys.exit(0)


def serve(
    host: str = "0.0.0.0",
    port: int = 50051,
    max_workers: int = 10,
) -> None:
    """Start the gRPC server.

    Args:
        host: Host address to bind to.
        port: Port number to listen on.
        max_workers: Maximum number of worker threads.

    """
    global _server

    _server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    mt5_pb2_grpc.add_MT5ServiceServicer_to_server(MT5GRPCServicer(), _server)
    server_address = f"{host}:{port}"
    _server.add_insecure_port(server_address)

    log.info("Starting MT5 gRPC server on %s", server_address)
    log.info("Python %s", sys.version)

    _server.start()
    log.info("Server started, waiting for connections...")
    _server.wait_for_termination()


def main(argv: list[str] | None = None) -> int:
    """Run the gRPC bridge server.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for error).

    """
    parser = argparse.ArgumentParser(description="MT5 gRPC Bridge Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=50051,
        help="Port (default: 50051)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Worker threads (default: 10)",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args(argv)

    _setup_logging(debug=args.debug)

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    log.debug("Debug logging enabled")
    log.debug("Workers=%s", args.workers)

    try:
        serve(host=args.host, port=args.port, max_workers=args.workers)
    except KeyboardInterrupt:
        log.info("Server interrupted by user")
    except Exception:
        log.exception("Server error")
        return 1
    finally:
        log.info("Server stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
