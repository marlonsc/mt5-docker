"""gRPC bridge for MetaTrader5 - runs inside Wine.

This module provides the MT5Service gRPC server that runs inside Wine
with Windows Python + MetaTrader5 module.

STANDALONE: This file has NO dependencies on other mt5linux modules.
Copy only this file + mt5_pb2.py + mt5_pb2_grpc.py + grpcio to Wine.

Features:
- gRPC server (replaces RPyC for better performance and async support)
- ThreadPoolExecutor for concurrent handling
- Signal handling (SIGTERM/SIGINT) for clean container stops
- Data serialization via JSON for dict types, numpy.tobytes() for arrays
- Chunked symbols_get for large datasets (9000+)
- Debug logging for every function call
- NO STUBS - fails if MT5 unavailable
- Complete MT5 API coverage including Market Depth (DOM)
- MT5 constants exposed for client usage

Usage:
    wine python.exe bridge.py --host 0.0.0.0 --port 8001 --debug
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
from concurrent import futures
from typing import TYPE_CHECKING, Protocol, TypeGuard

import grpc

# Import generated protobuf modules (copied to same directory)
import mt5_pb2
import mt5_pb2_grpc

if TYPE_CHECKING:
    from datetime import datetime
    from types import FrameType, ModuleType

    import numpy as np

# Module logger
log = logging.getLogger("mt5bridge")

# Global server reference for signal handler
_server: grpc.Server | None = None


class NamedTupleLike(Protocol):
    """Protocol for namedtuple-like objects that can be converted to dicts."""

    def _asdict(self) -> dict[str, object]:
        """Convert to dictionary representation."""
        ...


class MT5ServiceServicer(mt5_pb2_grpc.MT5ServiceServicer):
    """gRPC service for MT5."""

    _mt5_module: ModuleType | None = None
    _mt5_lock = threading.RLock()

    def _load_mt5(self) -> None:
        """Load MT5 module on first use."""
        with MT5ServiceServicer._mt5_lock:
            if MT5ServiceServicer._mt5_module is None:
                log.info("Loading MetaTrader5 module...")
                import MetaTrader5  # pyright: ignore[reportMissingImports]

                MT5ServiceServicer._mt5_module = MetaTrader5
                log.info("MetaTrader5 module loaded successfully")

    def _ensure_mt5_loaded(self) -> None:
        """Ensure MT5 module is loaded, raise RuntimeError if not."""
        if MT5ServiceServicer._mt5_module is None:
            self._load_mt5()
        if MT5ServiceServicer._mt5_module is None:
            msg = "MT5 module not loaded"
            raise RuntimeError(msg)

    # =========================================================================
    # HELPER FUNCTIONS (PRIVATE)
    # =========================================================================

    def _is_namedtuple_like(self, obj: object) -> TypeGuard[NamedTupleLike]:
        """Check if object is namedtuple-like (has _asdict method)."""
        return hasattr(obj, "_asdict") and callable(getattr(obj, "_asdict", None))

    def _materialize_single(
        self,
        result: NamedTupleLike | None,
        func_name: str,
        nested_fields: list[str] | None = None,
    ) -> dict[str, object] | None:
        """Convert single namedtuple to dict with optional nested conversion."""
        if result is None:
            log.debug("%s: result=None", func_name)
            return None
        data: dict[str, object] = result._asdict()
        if nested_fields:
            for field in nested_fields:
                if field in data:
                    field_value = data[field]
                    if self._is_namedtuple_like(field_value):
                        data[field] = field_value._asdict()
        return data

    def _materialize_tuple(
        self,
        result: tuple[NamedTupleLike, ...] | None,
        func_name: str,
    ) -> list[dict[str, object]] | None:
        """Convert tuple of namedtuples to list of dicts."""
        if result is None:
            log.debug("%s: result=None", func_name)
            return None
        data = [item._asdict() for item in result]
        log.debug("%s: returned %s items", func_name, len(data))
        return data

    def _validate_symbol(self, symbol: str, func_name: str) -> bool:
        """Validate symbol is not empty."""
        if not symbol:
            log.debug("%s: empty symbol", func_name)
            return False
        return True

    def _validate_count(self, count: int, func_name: str) -> bool:
        """Validate count is positive."""
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
        """Validate date_from <= date_to."""
        from_val = (
            date_from
            if isinstance(date_from, (int, float))
            else int(date_from.timestamp())
        )
        to_val = (
            date_to
            if isinstance(date_to, (int, float))
            else int(date_to.timestamp())
        )

        if from_val > to_val:
            log.warning(
                "%s: invalid range from=%s > to=%s", func_name, date_from, date_to
            )
            return False
        return True

    def _numpy_to_proto(self, arr: np.ndarray | None) -> mt5_pb2.NumpyArray:
        """Convert numpy array to protobuf NumpyArray message."""
        if arr is None:
            return mt5_pb2.NumpyArray(data=b"", dtype="", shape=[])
        return mt5_pb2.NumpyArray(
            data=arr.tobytes(),
            dtype=str(arr.dtype),
            shape=list(arr.shape),
        )

    def _dict_to_json(self, data: dict[str, object] | None) -> str:
        """Convert dict to JSON string, handling special types."""
        if data is None:
            return ""

        def serialize(obj: object) -> object:
            if hasattr(obj, "_asdict"):
                return obj._asdict()
            if hasattr(obj, "tolist"):  # numpy types
                return obj.tolist()  # type: ignore[union-attr]
            return obj

        return json.dumps(data, default=serialize)

    # =========================================================================
    # gRPC SERVICE METHODS
    # =========================================================================

    def HealthCheck(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.HealthStatus:
        """Health check endpoint - verifies actual MT5 connection status."""
        log.debug("HealthCheck: called")

        mt5_loaded = MT5ServiceServicer._mt5_module is not None
        if not mt5_loaded:
            try:
                self._load_mt5()
                mt5_loaded = MT5ServiceServicer._mt5_module is not None
            except Exception as e:
                log.debug("HealthCheck: MT5 load failed: %s", e)
                return mt5_pb2.HealthStatus(
                    healthy=False,
                    mt5_available=False,
                    connected=False,
                    trade_allowed=False,
                    build=0,
                    reason=f"MT5 module load failed: {e}",
                )

        if not mt5_loaded:
            return mt5_pb2.HealthStatus(
                healthy=False,
                mt5_available=False,
                connected=False,
                trade_allowed=False,
                build=0,
                reason="MT5 module not loaded",
            )

        terminal = MT5ServiceServicer._mt5_module.terminal_info()
        if terminal is None:
            error = MT5ServiceServicer._mt5_module.last_error()
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
        self, request: mt5_pb2.InitRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.BoolResponse:
        """Initialize MT5 terminal connection."""
        self._ensure_mt5_loaded()
        log.debug(
            "Initialize: path=%s login=%s server=%s timeout=%s portable=%s",
            request.path if request.HasField("path") else None,
            request.login if request.HasField("login") else None,
            request.server if request.HasField("server") else None,
            request.timeout if request.HasField("timeout") else None,
            request.portable,
        )
        kwargs: dict[str, object] = {}
        if request.HasField("path"):
            kwargs["path"] = request.path
        if request.HasField("login"):
            kwargs["login"] = request.login
        if request.HasField("password"):
            kwargs["password"] = request.password
        if request.HasField("server"):
            kwargs["server"] = request.server
        if request.HasField("timeout"):
            kwargs["timeout"] = request.timeout
        if request.portable:
            kwargs["portable"] = request.portable
        result = MT5ServiceServicer._mt5_module.initialize(**kwargs)
        log.info("initialize: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def Login(
        self, request: mt5_pb2.LoginRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.BoolResponse:
        """Login to MT5 account."""
        self._ensure_mt5_loaded()
        log.debug(
            "Login: login=%s server=%s timeout=%s",
            request.login,
            request.server,
            request.timeout,
        )
        result = MT5ServiceServicer._mt5_module.login(
            login=request.login,
            password=request.password,
            server=request.server,
            timeout=request.timeout,
        )
        log.info("login: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def Shutdown(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.Empty:
        """Shutdown MT5 terminal connection."""
        self._ensure_mt5_loaded()
        log.debug("Shutdown: called")
        MT5ServiceServicer._mt5_module.shutdown()
        log.info("shutdown: completed")
        return mt5_pb2.Empty()

    def Version(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.MT5Version:
        """Get MT5 terminal version."""
        self._ensure_mt5_loaded()
        log.debug("Version: called")
        result = MT5ServiceServicer._mt5_module.version()
        log.debug("Version: result=%s", result)
        if result is None:
            return mt5_pb2.MT5Version(major=0, minor=0, build="")
        return mt5_pb2.MT5Version(
            major=result[0],
            minor=result[1],
            build=str(result[2]),
        )

    def LastError(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.ErrorInfo:
        """Get last error code and description."""
        self._ensure_mt5_loaded()
        log.debug("LastError: called")
        result = MT5ServiceServicer._mt5_module.last_error()
        log.debug("LastError: result=%s", result)
        return mt5_pb2.ErrorInfo(code=result[0], message=result[1])

    def GetConstants(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.Constants:
        """Get all MT5 constants for client-side usage."""
        self._ensure_mt5_loaded()
        log.debug("GetConstants: called")
        mt5 = MT5ServiceServicer._mt5_module
        constants: dict[str, int] = {}

        def _add_constants(names: list[str]) -> None:
            for name in names:
                if hasattr(mt5, name):
                    val = getattr(mt5, name)
                    if isinstance(val, int):
                        constants[name] = val

        # Timeframes
        _add_constants([
            "TIMEFRAME_M1", "TIMEFRAME_M2", "TIMEFRAME_M3", "TIMEFRAME_M4",
            "TIMEFRAME_M5", "TIMEFRAME_M6", "TIMEFRAME_M10", "TIMEFRAME_M12",
            "TIMEFRAME_M15", "TIMEFRAME_M20", "TIMEFRAME_M30", "TIMEFRAME_H1",
            "TIMEFRAME_H2", "TIMEFRAME_H3", "TIMEFRAME_H4", "TIMEFRAME_H6",
            "TIMEFRAME_H8", "TIMEFRAME_H12", "TIMEFRAME_D1", "TIMEFRAME_W1",
            "TIMEFRAME_MN1",
        ])

        # Order types
        _add_constants([
            "ORDER_TYPE_BUY", "ORDER_TYPE_SELL", "ORDER_TYPE_BUY_LIMIT",
            "ORDER_TYPE_SELL_LIMIT", "ORDER_TYPE_BUY_STOP", "ORDER_TYPE_SELL_STOP",
            "ORDER_TYPE_BUY_STOP_LIMIT", "ORDER_TYPE_SELL_STOP_LIMIT",
            "ORDER_TYPE_CLOSE_BY",
        ])

        # Trade actions
        _add_constants([
            "TRADE_ACTION_DEAL", "TRADE_ACTION_PENDING", "TRADE_ACTION_SLTP",
            "TRADE_ACTION_MODIFY", "TRADE_ACTION_REMOVE", "TRADE_ACTION_CLOSE_BY",
        ])

        # Order filling modes
        _add_constants([
            "ORDER_FILLING_FOK", "ORDER_FILLING_IOC", "ORDER_FILLING_RETURN",
            "ORDER_FILLING_BOC",
        ])

        # Order time types
        _add_constants([
            "ORDER_TIME_GTC", "ORDER_TIME_DAY", "ORDER_TIME_SPECIFIED",
            "ORDER_TIME_SPECIFIED_DAY",
        ])

        # Order states
        _add_constants([
            "ORDER_STATE_STARTED", "ORDER_STATE_PLACED", "ORDER_STATE_CANCELED",
            "ORDER_STATE_PARTIAL", "ORDER_STATE_FILLED", "ORDER_STATE_REJECTED",
            "ORDER_STATE_EXPIRED", "ORDER_STATE_REQUEST_ADD",
            "ORDER_STATE_REQUEST_MODIFY", "ORDER_STATE_REQUEST_CANCEL",
        ])

        # Position types
        _add_constants(["POSITION_TYPE_BUY", "POSITION_TYPE_SELL"])

        # Position reasons
        _add_constants([
            "POSITION_REASON_CLIENT", "POSITION_REASON_MOBILE",
            "POSITION_REASON_WEB", "POSITION_REASON_EXPERT",
        ])

        # Deal types
        _add_constants([
            "DEAL_TYPE_BUY", "DEAL_TYPE_SELL", "DEAL_TYPE_BALANCE",
            "DEAL_TYPE_CREDIT", "DEAL_TYPE_CHARGE", "DEAL_TYPE_CORRECTION",
            "DEAL_TYPE_BONUS", "DEAL_TYPE_COMMISSION", "DEAL_TYPE_COMMISSION_DAILY",
            "DEAL_TYPE_COMMISSION_MONTHLY", "DEAL_TYPE_COMMISSION_AGENT_DAILY",
            "DEAL_TYPE_COMMISSION_AGENT_MONTHLY", "DEAL_TYPE_INTEREST",
            "DEAL_TYPE_BUY_CANCELED", "DEAL_TYPE_SELL_CANCELED",
            "DEAL_DIVIDEND", "DEAL_DIVIDEND_FRANKED", "DEAL_TAX",
        ])

        # Deal entry types
        _add_constants([
            "DEAL_ENTRY_IN", "DEAL_ENTRY_OUT", "DEAL_ENTRY_INOUT",
            "DEAL_ENTRY_OUT_BY",
        ])

        # Deal reasons
        _add_constants([
            "DEAL_REASON_CLIENT", "DEAL_REASON_MOBILE", "DEAL_REASON_WEB",
            "DEAL_REASON_EXPERT", "DEAL_REASON_SL", "DEAL_REASON_TP",
            "DEAL_REASON_SO", "DEAL_REASON_ROLLOVER", "DEAL_REASON_VMARGIN",
            "DEAL_REASON_SPLIT",
        ])

        # Copy ticks flags
        _add_constants(["COPY_TICKS_ALL", "COPY_TICKS_INFO", "COPY_TICKS_TRADE"])

        # Book types (Market Depth)
        _add_constants([
            "BOOK_TYPE_SELL", "BOOK_TYPE_BUY",
            "BOOK_TYPE_SELL_MARKET", "BOOK_TYPE_BUY_MARKET",
        ])

        # Symbol trade modes
        _add_constants([
            "SYMBOL_TRADE_MODE_DISABLED", "SYMBOL_TRADE_MODE_LONGONLY",
            "SYMBOL_TRADE_MODE_SHORTONLY", "SYMBOL_TRADE_MODE_CLOSEONLY",
            "SYMBOL_TRADE_MODE_FULL",
        ])

        # Account trade modes
        _add_constants([
            "ACCOUNT_TRADE_MODE_DEMO", "ACCOUNT_TRADE_MODE_CONTEST",
            "ACCOUNT_TRADE_MODE_REAL",
        ])

        # Trade return codes
        _add_constants([
            "TRADE_RETCODE_REQUOTE", "TRADE_RETCODE_REJECT",
            "TRADE_RETCODE_CANCEL", "TRADE_RETCODE_PLACED",
            "TRADE_RETCODE_DONE", "TRADE_RETCODE_DONE_PARTIAL",
            "TRADE_RETCODE_ERROR", "TRADE_RETCODE_TIMEOUT",
            "TRADE_RETCODE_INVALID", "TRADE_RETCODE_INVALID_VOLUME",
            "TRADE_RETCODE_INVALID_PRICE", "TRADE_RETCODE_INVALID_STOPS",
            "TRADE_RETCODE_TRADE_DISABLED", "TRADE_RETCODE_MARKET_CLOSED",
            "TRADE_RETCODE_NO_MONEY", "TRADE_RETCODE_PRICE_CHANGED",
            "TRADE_RETCODE_PRICE_OFF", "TRADE_RETCODE_INVALID_EXPIRATION",
            "TRADE_RETCODE_ORDER_CHANGED", "TRADE_RETCODE_TOO_MANY_REQUESTS",
            "TRADE_RETCODE_NO_CHANGES", "TRADE_RETCODE_LOCKED",
            "TRADE_RETCODE_FROZEN", "TRADE_RETCODE_INVALID_FILL",
            "TRADE_RETCODE_CONNECTION", "TRADE_RETCODE_ONLY_REAL",
            "TRADE_RETCODE_LIMIT_ORDERS", "TRADE_RETCODE_LIMIT_VOLUME",
        ])

        log.debug("GetConstants: returned %s constants", len(constants))
        return mt5_pb2.Constants(values=constants)

    def TerminalInfo(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Get terminal info."""
        self._ensure_mt5_loaded()
        log.debug("TerminalInfo: called")
        result = MT5ServiceServicer._mt5_module.terminal_info()
        data = self._materialize_single(result, "terminal_info")
        json_data = self._dict_to_json(data)
        if data:
            log.debug("TerminalInfo: returned terminal info")
        return mt5_pb2.DictData(json_data=json_data)

    def AccountInfo(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Get account info."""
        self._ensure_mt5_loaded()
        log.debug("AccountInfo: called")
        result = MT5ServiceServicer._mt5_module.account_info()
        data = self._materialize_single(result, "account_info")
        json_data = self._dict_to_json(data)
        if data:
            log.debug("AccountInfo: login=%s", data.get("login"))
        return mt5_pb2.DictData(json_data=json_data)

    def SymbolsTotal(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.IntResponse:
        """Get total number of symbols."""
        self._ensure_mt5_loaded()
        log.debug("SymbolsTotal: called")
        result = MT5ServiceServicer._mt5_module.symbols_total()
        log.debug("SymbolsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result is not None else 0)

    def SymbolsGet(
        self, request: mt5_pb2.SymbolsRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.SymbolsResponse:
        """Get symbols with chunked JSON."""
        self._ensure_mt5_loaded()
        group = request.group if request.HasField("group") else None
        log.debug("SymbolsGet: group=%s", group)

        if group:
            result = MT5ServiceServicer._mt5_module.symbols_get(group=group)
        else:
            result = MT5ServiceServicer._mt5_module.symbols_get()

        if result is None:
            log.debug("SymbolsGet: result=None")
            return mt5_pb2.SymbolsResponse(total=0, chunks=[])

        items = list(result)
        total = len(items)
        log.debug("SymbolsGet: total=%s symbols", total)

        chunk_size = 500
        chunks = []
        for i in range(0, total, chunk_size):
            chunk_items = [s._asdict() for s in items[i : i + chunk_size]]
            chunks.append(json.dumps(chunk_items, default=str))

        log.debug("SymbolsGet: returned %s chunks", len(chunks))
        return mt5_pb2.SymbolsResponse(total=total, chunks=chunks)

    def SymbolInfo(
        self, request: mt5_pb2.SymbolRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Get symbol info."""
        self._ensure_mt5_loaded()
        log.debug("SymbolInfo: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "SymbolInfo"):
            return mt5_pb2.DictData(json_data="")
        result = MT5ServiceServicer._mt5_module.symbol_info(request.symbol)
        data = self._materialize_single(result, "symbol_info")
        json_data = self._dict_to_json(data)
        if data:
            log.debug("SymbolInfo: found symbol")
        return mt5_pb2.DictData(json_data=json_data)

    def SymbolInfoTick(
        self, request: mt5_pb2.SymbolRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Get symbol tick."""
        self._ensure_mt5_loaded()
        log.debug("SymbolInfoTick: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "SymbolInfoTick"):
            return mt5_pb2.DictData(json_data="")
        result = MT5ServiceServicer._mt5_module.symbol_info_tick(request.symbol)
        data = self._materialize_single(result, "symbol_info_tick")
        json_data = self._dict_to_json(data)
        if data:
            log.debug("SymbolInfoTick: bid=%s ask=%s", data.get("bid"), data.get("ask"))
        return mt5_pb2.DictData(json_data=json_data)

    def SymbolSelect(
        self, request: mt5_pb2.SymbolSelectRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.BoolResponse:
        """Select/deselect symbol in Market Watch."""
        self._ensure_mt5_loaded()
        log.debug("SymbolSelect: symbol=%s enable=%s", request.symbol, request.enable)
        if not self._validate_symbol(request.symbol, "SymbolSelect"):
            return mt5_pb2.BoolResponse(result=False)
        result = MT5ServiceServicer._mt5_module.symbol_select(
            request.symbol, request.enable
        )
        log.debug("SymbolSelect: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def CopyRatesFrom(
        self, request: mt5_pb2.CopyRatesRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.NumpyArray:
        """Copy rates from specified date."""
        self._ensure_mt5_loaded()
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
        result = MT5ServiceServicer._mt5_module.copy_rates_from(
            request.symbol, request.timeframe, request.date_from, request.count
        )
        log.debug(
            "CopyRatesFrom: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyRatesFromPos(
        self, request: mt5_pb2.CopyRatesPosRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.NumpyArray:
        """Copy rates from position."""
        self._ensure_mt5_loaded()
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
        result = MT5ServiceServicer._mt5_module.copy_rates_from_pos(
            request.symbol, request.timeframe, request.start_pos, request.count
        )
        log.debug(
            "CopyRatesFromPos: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyRatesRange(
        self, request: mt5_pb2.CopyRatesRangeRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.NumpyArray:
        """Copy rates in date range."""
        self._ensure_mt5_loaded()
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
            request.date_from, request.date_to, "CopyRatesRange"
        ):
            return self._numpy_to_proto(None)
        result = MT5ServiceServicer._mt5_module.copy_rates_range(
            request.symbol, request.timeframe, request.date_from, request.date_to
        )
        log.debug(
            "CopyRatesRange: returned %s bars",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyTicksFrom(
        self, request: mt5_pb2.CopyTicksRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.NumpyArray:
        """Copy ticks from specified date."""
        self._ensure_mt5_loaded()
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
        result = MT5ServiceServicer._mt5_module.copy_ticks_from(
            request.symbol, request.date_from, request.count, request.flags
        )
        log.debug(
            "CopyTicksFrom: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def CopyTicksRange(
        self, request: mt5_pb2.CopyTicksRangeRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.NumpyArray:
        """Copy ticks in date range."""
        self._ensure_mt5_loaded()
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
            request.date_from, request.date_to, "CopyTicksRange"
        ):
            return self._numpy_to_proto(None)
        result = MT5ServiceServicer._mt5_module.copy_ticks_range(
            request.symbol, request.date_from, request.date_to, request.flags
        )
        log.debug(
            "CopyTicksRange: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return self._numpy_to_proto(result)

    def OrderCalcMargin(
        self, request: mt5_pb2.MarginRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.FloatResponse:
        """Calculate order margin."""
        self._ensure_mt5_loaded()
        log.debug(
            "OrderCalcMargin: action=%s symbol=%s vol=%s price=%s",
            request.action,
            request.symbol,
            request.volume,
            request.price,
        )
        result = MT5ServiceServicer._mt5_module.order_calc_margin(
            request.action, request.symbol, request.volume, request.price
        )
        log.debug("OrderCalcMargin: result=%s", result)
        if result is None:
            return mt5_pb2.FloatResponse()
        return mt5_pb2.FloatResponse(value=result)

    def OrderCalcProfit(
        self, request: mt5_pb2.ProfitRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.FloatResponse:
        """Calculate order profit."""
        self._ensure_mt5_loaded()
        log.debug(
            "OrderCalcProfit: action=%s symbol=%s vol=%s open=%s close=%s",
            request.action,
            request.symbol,
            request.volume,
            request.price_open,
            request.price_close,
        )
        result = MT5ServiceServicer._mt5_module.order_calc_profit(
            request.action,
            request.symbol,
            request.volume,
            request.price_open,
            request.price_close,
        )
        log.debug("OrderCalcProfit: result=%s", result)
        if result is None:
            return mt5_pb2.FloatResponse()
        return mt5_pb2.FloatResponse(value=result)

    def OrderCheck(
        self, request: mt5_pb2.OrderRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Check order."""
        self._ensure_mt5_loaded()
        log.debug("OrderCheck: request=%s", request.json_request)
        order_dict = json.loads(request.json_request)
        result = MT5ServiceServicer._mt5_module.order_check(order_dict)
        data = self._materialize_single(result, "order_check", nested_fields=["request"])
        json_data = self._dict_to_json(data)
        if data:
            log.debug("OrderCheck: retcode=%s", data.get("retcode"))
        return mt5_pb2.DictData(json_data=json_data)

    def OrderSend(
        self, request: mt5_pb2.OrderRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictData:
        """Send order."""
        self._ensure_mt5_loaded()
        log.debug("OrderSend: request=%s", request.json_request)
        order_dict = json.loads(request.json_request)
        result = MT5ServiceServicer._mt5_module.order_send(order_dict)
        data = self._materialize_single(result, "order_send", nested_fields=["request"])
        json_data = self._dict_to_json(data)
        if data:
            log.info(
                "OrderSend: retcode=%s order=%s deal=%s",
                data.get("retcode"),
                data.get("order"),
                data.get("deal"),
            )
        return mt5_pb2.DictData(json_data=json_data)

    def PositionsTotal(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.IntResponse:
        """Get total number of open positions."""
        self._ensure_mt5_loaded()
        log.debug("PositionsTotal: called")
        result = MT5ServiceServicer._mt5_module.positions_total()
        log.debug("PositionsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result is not None else 0)

    def PositionsGet(
        self, request: mt5_pb2.PositionsRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictList:
        """Get positions."""
        self._ensure_mt5_loaded()
        symbol = request.symbol if request.HasField("symbol") else None
        group = request.group if request.HasField("group") else None
        ticket = request.ticket if request.HasField("ticket") else None
        log.debug("PositionsGet: symbol=%s group=%s ticket=%s", symbol, group, ticket)

        kwargs: dict[str, object] = {}
        if symbol:
            kwargs["symbol"] = symbol
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket

        if kwargs:
            result = MT5ServiceServicer._mt5_module.positions_get(**kwargs)
        else:
            result = MT5ServiceServicer._mt5_module.positions_get()

        items = self._materialize_tuple(result, "positions_get")
        if items is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [json.dumps(item, default=str) for item in items]
        return mt5_pb2.DictList(json_items=json_items)

    def OrdersTotal(
        self, request: mt5_pb2.Empty, context: grpc.ServicerContext
    ) -> mt5_pb2.IntResponse:
        """Get total number of pending orders."""
        self._ensure_mt5_loaded()
        log.debug("OrdersTotal: called")
        result = MT5ServiceServicer._mt5_module.orders_total()
        log.debug("OrdersTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result is not None else 0)

    def OrdersGet(
        self, request: mt5_pb2.OrdersRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictList:
        """Get pending orders."""
        self._ensure_mt5_loaded()
        symbol = request.symbol if request.HasField("symbol") else None
        group = request.group if request.HasField("group") else None
        ticket = request.ticket if request.HasField("ticket") else None
        log.debug("OrdersGet: symbol=%s group=%s ticket=%s", symbol, group, ticket)

        kwargs: dict[str, object] = {}
        if symbol:
            kwargs["symbol"] = symbol
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket

        if kwargs:
            result = MT5ServiceServicer._mt5_module.orders_get(**kwargs)
        else:
            result = MT5ServiceServicer._mt5_module.orders_get()

        items = self._materialize_tuple(result, "orders_get")
        if items is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [json.dumps(item, default=str) for item in items]
        return mt5_pb2.DictList(json_items=json_items)

    def HistoryOrdersTotal(
        self, request: mt5_pb2.HistoryRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.IntResponse:
        """Get total history orders count."""
        self._ensure_mt5_loaded()
        date_from = request.date_from if request.HasField("date_from") else 0
        date_to = request.date_to if request.HasField("date_to") else 0
        log.debug("HistoryOrdersTotal: from=%s to=%s", date_from, date_to)
        result = MT5ServiceServicer._mt5_module.history_orders_total(date_from, date_to)
        log.debug("HistoryOrdersTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result is not None else 0)

    def HistoryOrdersGet(
        self, request: mt5_pb2.HistoryRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictList:
        """Get history orders."""
        self._ensure_mt5_loaded()
        date_from = request.date_from if request.HasField("date_from") else None
        date_to = request.date_to if request.HasField("date_to") else None
        group = request.group if request.HasField("group") else None
        ticket = request.ticket if request.HasField("ticket") else None
        position = request.position if request.HasField("position") else None
        log.debug(
            "HistoryOrdersGet: from=%s to=%s group=%s ticket=%s pos=%s",
            date_from,
            date_to,
            group,
            ticket,
            position,
        )

        kwargs: dict[str, object] = {}
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if position:
            kwargs["position"] = position

        if date_from is not None and date_to is not None:
            result = MT5ServiceServicer._mt5_module.history_orders_get(
                date_from, date_to, **kwargs
            )
        elif kwargs:
            result = MT5ServiceServicer._mt5_module.history_orders_get(**kwargs)
        else:
            result = MT5ServiceServicer._mt5_module.history_orders_get()

        items = self._materialize_tuple(result, "history_orders_get")
        if items is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [json.dumps(item, default=str) for item in items]
        return mt5_pb2.DictList(json_items=json_items)

    def HistoryDealsTotal(
        self, request: mt5_pb2.HistoryRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.IntResponse:
        """Get total history deals count."""
        self._ensure_mt5_loaded()
        date_from = request.date_from if request.HasField("date_from") else 0
        date_to = request.date_to if request.HasField("date_to") else 0
        log.debug("HistoryDealsTotal: from=%s to=%s", date_from, date_to)
        result = MT5ServiceServicer._mt5_module.history_deals_total(date_from, date_to)
        log.debug("HistoryDealsTotal: result=%s", result)
        return mt5_pb2.IntResponse(value=int(result) if result is not None else 0)

    def HistoryDealsGet(
        self, request: mt5_pb2.HistoryRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictList:
        """Get history deals."""
        self._ensure_mt5_loaded()
        date_from = request.date_from if request.HasField("date_from") else None
        date_to = request.date_to if request.HasField("date_to") else None
        group = request.group if request.HasField("group") else None
        ticket = request.ticket if request.HasField("ticket") else None
        position = request.position if request.HasField("position") else None
        log.debug(
            "HistoryDealsGet: from=%s to=%s group=%s ticket=%s pos=%s",
            date_from,
            date_to,
            group,
            ticket,
            position,
        )

        kwargs: dict[str, object] = {}
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if position:
            kwargs["position"] = position

        if date_from is not None and date_to is not None:
            result = MT5ServiceServicer._mt5_module.history_deals_get(
                date_from, date_to, **kwargs
            )
        elif kwargs:
            result = MT5ServiceServicer._mt5_module.history_deals_get(**kwargs)
        else:
            result = MT5ServiceServicer._mt5_module.history_deals_get()

        items = self._materialize_tuple(result, "history_deals_get")
        if items is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [json.dumps(item, default=str) for item in items]
        return mt5_pb2.DictList(json_items=json_items)

    # =========================================================================
    # MARKET DEPTH (DOM) FUNCTIONS
    # =========================================================================

    def MarketBookAdd(
        self, request: mt5_pb2.SymbolRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.BoolResponse:
        """Subscribe to Market Depth (DOM) for a symbol."""
        self._ensure_mt5_loaded()
        log.debug("MarketBookAdd: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookAdd"):
            return mt5_pb2.BoolResponse(result=False)
        result = MT5ServiceServicer._mt5_module.market_book_add(request.symbol)
        log.debug("MarketBookAdd: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))

    def MarketBookGet(
        self, request: mt5_pb2.SymbolRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.DictList:
        """Get Market Depth (DOM) entries for a symbol."""
        self._ensure_mt5_loaded()
        log.debug("MarketBookGet: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookGet"):
            return mt5_pb2.DictList(json_items=[])
        result = MT5ServiceServicer._mt5_module.market_book_get(request.symbol)
        items = self._materialize_tuple(result, "market_book_get")
        if items is None:
            return mt5_pb2.DictList(json_items=[])
        json_items = [json.dumps(item, default=str) for item in items]
        return mt5_pb2.DictList(json_items=json_items)

    def MarketBookRelease(
        self, request: mt5_pb2.SymbolRequest, context: grpc.ServicerContext
    ) -> mt5_pb2.BoolResponse:
        """Unsubscribe from Market Depth (DOM) for a symbol."""
        self._ensure_mt5_loaded()
        log.debug("MarketBookRelease: symbol=%s", request.symbol)
        if not self._validate_symbol(request.symbol, "MarketBookRelease"):
            return mt5_pb2.BoolResponse(result=False)
        result = MT5ServiceServicer._mt5_module.market_book_release(request.symbol)
        log.debug("MarketBookRelease: result=%s", result)
        return mt5_pb2.BoolResponse(result=bool(result))


def _setup_logging(*, debug: bool = False) -> None:
    """Configure logging for the bridge."""
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
    logging.basicConfig(level=level, handlers=[handler])


def _graceful_shutdown(signum: int, frame: FrameType | None) -> None:
    """Handle shutdown signals for clean container stops."""
    sig_name = signal.Signals(signum).name
    log.info("Received %s, shutting down gracefully...", sig_name)
    if _server is not None:
        _server.stop(grace=5)
    sys.exit(0)


def main(argv: list[str] | None = None) -> int:
    """Run the gRPC bridge server."""
    global _server

    parser = argparse.ArgumentParser(description="MT5 gRPC Bridge Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind"
    )
    parser.add_argument("-p", "--port", type=int, default=8001, help="Port")
    parser.add_argument("--threads", type=int, default=10, help="Worker threads")
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args(argv)

    _setup_logging(debug=args.debug)

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    log.info("Starting MT5 gRPC Service on %s:%s", args.host, args.port)
    log.info("Python %s", sys.version)
    log.debug("Debug logging enabled")
    log.debug("Threads=%s", args.threads)

    _server = grpc.server(futures.ThreadPoolExecutor(max_workers=args.threads))
    mt5_pb2_grpc.add_MT5ServiceServicer_to_server(MT5ServiceServicer(), _server)
    _server.add_insecure_port(f"{args.host}:{args.port}")

    try:
        _server.start()
        log.info("Server started, waiting for connections...")
        _server.wait_for_termination()
    except KeyboardInterrupt:
        log.info("Server interrupted by user")
    except Exception:
        log.exception("Server error")
        return 1
    finally:
        if _server is not None:
            _server.stop(grace=0)
        log.info("Server stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
