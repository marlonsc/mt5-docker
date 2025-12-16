"""RPyC bridge for MetaTrader5 - runs inside Wine.

This module provides the MT5Service RPyC server that runs inside Wine
with Windows Python + MetaTrader5 module.

STANDALONE: This file has NO dependencies on other mt5linux modules.
Copy only this file + rpyc to Wine for a working MT5 bridge.

Features:
- Modern rpyc.Service (NOT deprecated SlaveService/ClassicService)
- ThreadPoolServer for concurrent handling
- Signal handling (SIGTERM/SIGINT) for clean container stops
- Data materialization (_asdict() for NamedTuples)
- Chunked symbols_get for large datasets (9000+)
- Debug logging for every function call
- NO STUBS - fails if MT5 unavailable
- Complete MT5 API coverage including Market Depth (DOM)
- MT5 constants exposed for client usage
- Secure: no raw module exposure, controlled API surface

Usage:
    wine python.exe -m mt5linux.bridge --host 0.0.0.0 --port 8001
    wine python.exe bridge.py --host 0.0.0.0 --port 8001 --debug
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from types import FrameType
from typing import Any

import rpyc
from rpyc.utils.server import ThreadPoolServer

# Module logger
log = logging.getLogger("mt5bridge")

# Global server reference for signal handler
_server: ThreadPoolServer | None = None


class MT5Service(rpyc.Service):
    """Modern RPyC service for MT5. NO STUBS."""

    _mt5_module: Any = None
    _mt5_lock = threading.RLock()

    def on_connect(self, conn: rpyc.Connection) -> None:  # noqa: ARG002
        """Handle new client connection."""
        log.debug("on_connect: new client connected")
        with MT5Service._mt5_lock:
            if MT5Service._mt5_module is None:
                log.info("Loading MetaTrader5 module...")
                import MetaTrader5  # pyright: ignore[reportMissingImports]

                MT5Service._mt5_module = MetaTrader5
                log.info("MetaTrader5 module loaded successfully")

    def on_disconnect(self, conn: rpyc.Connection) -> None:  # noqa: ARG002
        """Handle client disconnection."""
        log.debug("on_disconnect: client disconnected")

    def _ensure_mt5_loaded(self) -> None:
        """Ensure MT5 module is loaded, raise RuntimeError if not."""
        if MT5Service._mt5_module is None:
            raise RuntimeError("MT5 module not loaded - connect first")

    def exposed_health_check(self) -> dict[str, Any]:
        """Health check endpoint - verifies actual MT5 connection status."""
        log.debug("exposed_health_check: called")

        mt5_loaded = MT5Service._mt5_module is not None
        if not mt5_loaded:
            log.debug("exposed_health_check: MT5 module not loaded")
            return {
                "healthy": False,
                "mt5_available": False,
                "reason": "MT5 module not loaded",
            }

        # Check actual terminal connection
        terminal = MT5Service._mt5_module.terminal_info()
        if terminal is None:
            error = MT5Service._mt5_module.last_error()
            log.debug("exposed_health_check: terminal_info failed: %s", error)
            return {
                "healthy": False,
                "mt5_available": True,
                "connected": False,
                "reason": f"Terminal not connected: {error}",
            }

        log.debug(
            "exposed_health_check: connected=%s trade_allowed=%s",
            terminal.connected,
            terminal.trade_allowed,
        )
        return {
            "healthy": terminal.connected,
            "mt5_available": True,
            "connected": terminal.connected,
            "trade_allowed": terminal.trade_allowed,
            "build": terminal.build,
        }

    def exposed_initialize(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int | None = None,
        portable: bool = False,
    ) -> bool:
        """Initialize MT5 terminal connection."""
        self._ensure_mt5_loaded()
        log.debug(
            "exposed_initialize: path=%s login=%s server=%s timeout=%s portable=%s",
            path,
            login,
            server,
            timeout,
            portable,
        )
        kwargs: dict[str, Any] = {}
        if path is not None:
            kwargs["path"] = path
        if login is not None:
            kwargs["login"] = login
        if password is not None:
            kwargs["password"] = password
        if server is not None:
            kwargs["server"] = server
        if timeout is not None:
            kwargs["timeout"] = timeout
        if portable:
            kwargs["portable"] = portable
        result = MT5Service._mt5_module.initialize(**kwargs)
        log.info("initialize: result=%s", result)
        return result

    def exposed_login(
        self, login: int, password: str, server: str, timeout: int = 60000
    ) -> bool:
        """Login to MT5 account."""
        log.debug(
            "exposed_login: login=%s server=%s timeout=%s", login, server, timeout
        )
        result = MT5Service._mt5_module.login(
            login=login, password=password, server=server, timeout=timeout
        )
        log.info("login: result=%s", result)
        return result

    def exposed_shutdown(self) -> None:
        """Shutdown MT5 terminal connection."""
        log.debug("exposed_shutdown: called")
        result = MT5Service._mt5_module.shutdown()
        log.info("shutdown: completed")
        return result

    def exposed_version(self) -> tuple[int, int, str] | None:
        """Get MT5 terminal version."""
        log.debug("exposed_version: called")
        result = MT5Service._mt5_module.version()
        log.debug("exposed_version: result=%s", result)
        return result

    def exposed_last_error(self) -> tuple[int, str]:
        """Get last error code and description."""
        log.debug("exposed_last_error: called")
        result = MT5Service._mt5_module.last_error()
        log.debug("exposed_last_error: result=%s", result)
        return result

    def exposed_terminal_info(self) -> Any:
        """Get terminal info with data materialization."""
        log.debug("exposed_terminal_info: called")
        result = MT5Service._mt5_module.terminal_info()
        if result is None:
            log.debug("exposed_terminal_info: result=None")
            return None
        data = result._asdict()
        log.debug("exposed_terminal_info: returned terminal info")
        return data

    def exposed_account_info(self) -> Any:
        """Get account info with data materialization."""
        log.debug("exposed_account_info: called")
        result = MT5Service._mt5_module.account_info()
        if result is None:
            log.debug("exposed_account_info: result=None")
            return None
        data = result._asdict()
        log.debug("exposed_account_info: login=%s", data.get("login"))
        return data

    def exposed_symbols_total(self) -> int:
        """Get total number of symbols."""
        log.debug("exposed_symbols_total: called")
        result = MT5Service._mt5_module.symbols_total()
        log.debug("exposed_symbols_total: result=%s", result)
        return result

    def exposed_symbols_get(self, group: str | None = None) -> Any:
        """Get symbols with chunked streaming to prevent IPC timeout."""
        log.debug("exposed_symbols_get: group=%s", group)
        if group:
            result = MT5Service._mt5_module.symbols_get(group=group)
        else:
            result = MT5Service._mt5_module.symbols_get()

        if result is None:
            log.debug("exposed_symbols_get: result=None")
            return None

        items = list(result)
        total = len(items)
        log.debug("exposed_symbols_get: total=%s symbols", total)

        chunk_size = 500
        if total <= chunk_size:
            return {"total": total, "chunks": [tuple(s._asdict() for s in items)]}

        chunks = []
        for i in range(0, total, chunk_size):
            chunk = tuple(s._asdict() for s in items[i : i + chunk_size])
            chunks.append(chunk)
        log.debug("exposed_symbols_get: returned %s chunks", len(chunks))
        return {"total": total, "chunks": chunks}

    def exposed_symbol_info(self, symbol: str) -> Any:
        """Get symbol info with data materialization."""
        log.debug("exposed_symbol_info: symbol=%s", symbol)
        result = MT5Service._mt5_module.symbol_info(symbol)
        if result is None:
            log.debug("exposed_symbol_info: result=None")
            return None
        log.debug("exposed_symbol_info: found symbol")
        return result._asdict()

    def exposed_symbol_info_tick(self, symbol: str) -> Any:
        """Get symbol tick with data materialization."""
        log.debug("exposed_symbol_info_tick: symbol=%s", symbol)
        result = MT5Service._mt5_module.symbol_info_tick(symbol)
        if result is None:
            log.debug("exposed_symbol_info_tick: result=None")
            return None
        log.debug("exposed_symbol_info_tick: bid=%s ask=%s", result.bid, result.ask)
        return result._asdict()

    def exposed_symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select/deselect symbol in Market Watch."""
        log.debug("exposed_symbol_select: symbol=%s enable=%s", symbol, enable)
        result = MT5Service._mt5_module.symbol_select(symbol, enable)
        log.debug("exposed_symbol_select: result=%s", result)
        return result

    def exposed_copy_rates_from(
        self, symbol: str, timeframe: int, date_from: Any, count: int
    ) -> Any:
        """Copy rates from specified date."""
        log.debug(
            "exposed_copy_rates_from: symbol=%s tf=%s date=%s count=%s",
            symbol,
            timeframe,
            date_from,
            count,
        )
        result = MT5Service._mt5_module.copy_rates_from(
            symbol, timeframe, date_from, count
        )
        log.debug(
            "exposed_copy_rates_from: returned %s bars",
            len(result) if result is not None else 0,
        )
        return result

    def exposed_copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> Any:
        """Copy rates from position."""
        log.debug(
            "exposed_copy_rates_from_pos: symbol=%s tf=%s pos=%s count=%s",
            symbol,
            timeframe,
            start_pos,
            count,
        )
        result = MT5Service._mt5_module.copy_rates_from_pos(
            symbol, timeframe, start_pos, count
        )
        log.debug(
            "exposed_copy_rates_from_pos: returned %s bars",
            len(result) if result is not None else 0,
        )
        return result

    def exposed_copy_rates_range(
        self, symbol: str, timeframe: int, date_from: Any, date_to: Any
    ) -> Any:
        """Copy rates in date range."""
        log.debug(
            "exposed_copy_rates_range: symbol=%s tf=%s from=%s to=%s",
            symbol,
            timeframe,
            date_from,
            date_to,
        )
        result = MT5Service._mt5_module.copy_rates_range(
            symbol, timeframe, date_from, date_to
        )
        log.debug(
            "exposed_copy_rates_range: returned %s bars",
            len(result) if result is not None else 0,
        )
        return result

    def exposed_copy_ticks_from(
        self, symbol: str, date_from: Any, count: int, flags: int
    ) -> Any:
        """Copy ticks from specified date."""
        log.debug(
            "exposed_copy_ticks_from: symbol=%s date=%s count=%s flags=%s",
            symbol,
            date_from,
            count,
            flags,
        )
        result = MT5Service._mt5_module.copy_ticks_from(
            symbol, date_from, count, flags
        )
        log.debug(
            "exposed_copy_ticks_from: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return result

    def exposed_copy_ticks_range(
        self, symbol: str, date_from: Any, date_to: Any, flags: int
    ) -> Any:
        """Copy ticks in date range."""
        log.debug(
            "exposed_copy_ticks_range: symbol=%s from=%s to=%s flags=%s",
            symbol,
            date_from,
            date_to,
            flags,
        )
        result = MT5Service._mt5_module.copy_ticks_range(
            symbol, date_from, date_to, flags
        )
        log.debug(
            "exposed_copy_ticks_range: returned %s ticks",
            len(result) if result is not None else 0,
        )
        return result

    def exposed_order_calc_margin(
        self, action: int, symbol: str, volume: float, price: float
    ) -> float | None:
        """Calculate order margin."""
        log.debug(
            "exposed_order_calc_margin: action=%s symbol=%s vol=%s price=%s",
            action,
            symbol,
            volume,
            price,
        )
        result = MT5Service._mt5_module.order_calc_margin(
            action, symbol, volume, price
        )
        log.debug("exposed_order_calc_margin: result=%s", result)
        return result

    def exposed_order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | None:
        """Calculate order profit."""
        log.debug(
            "exposed_order_calc_profit: action=%s symbol=%s vol=%s open=%s close=%s",
            action,
            symbol,
            volume,
            price_open,
            price_close,
        )
        result = MT5Service._mt5_module.order_calc_profit(
            action, symbol, volume, price_open, price_close
        )
        log.debug("exposed_order_calc_profit: result=%s", result)
        return result

    def exposed_order_check(self, request: dict[str, Any]) -> Any:
        """Check order with data materialization."""
        self._ensure_mt5_loaded()
        log.debug("exposed_order_check: request=%s", request)
        local_request = dict(request)
        result = MT5Service._mt5_module.order_check(local_request)
        if result is None:
            log.debug("exposed_order_check: result=None")
            return None
        data = result._asdict()
        log.debug("exposed_order_check: retcode=%s", data.get("retcode"))
        return data

    def exposed_order_send(self, request: dict[str, Any]) -> Any:
        """Send order with data materialization."""
        self._ensure_mt5_loaded()
        log.debug("exposed_order_send: request=%s", request)
        local_request = dict(request)
        result = MT5Service._mt5_module.order_send(local_request)
        if result is None:
            log.debug("exposed_order_send: result=None")
            return None
        data = result._asdict()
        log.info(
            "order_send: retcode=%s order=%s deal=%s",
            data.get("retcode"),
            data.get("order"),
            data.get("deal"),
        )
        return data

    def exposed_positions_total(self) -> int:
        """Get total number of open positions."""
        log.debug("exposed_positions_total: called")
        result = MT5Service._mt5_module.positions_total()
        log.debug("exposed_positions_total: result=%s", result)
        return result

    def exposed_positions_get(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
    ) -> Any:
        """Get positions with data materialization."""
        log.debug(
            "exposed_positions_get: symbol=%s group=%s ticket=%s", symbol, group, ticket
        )
        kwargs: dict[str, Any] = {}
        if symbol:
            kwargs["symbol"] = symbol
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if kwargs:
            result = MT5Service._mt5_module.positions_get(**kwargs)
        else:
            result = MT5Service._mt5_module.positions_get()
        if result is None:
            log.debug("exposed_positions_get: result=None")
            return None
        data = tuple(p._asdict() for p in result)
        log.debug("exposed_positions_get: returned %s positions", len(data))
        return data

    def exposed_orders_total(self) -> int:
        """Get total number of pending orders."""
        log.debug("exposed_orders_total: called")
        result = MT5Service._mt5_module.orders_total()
        log.debug("exposed_orders_total: result=%s", result)
        return result

    def exposed_orders_get(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
    ) -> Any:
        """Get pending orders with data materialization."""
        log.debug(
            "exposed_orders_get: symbol=%s group=%s ticket=%s", symbol, group, ticket
        )
        kwargs: dict[str, Any] = {}
        if symbol:
            kwargs["symbol"] = symbol
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if kwargs:
            result = MT5Service._mt5_module.orders_get(**kwargs)
        else:
            result = MT5Service._mt5_module.orders_get()
        if result is None:
            log.debug("exposed_orders_get: result=None")
            return None
        data = tuple(o._asdict() for o in result)
        log.debug("exposed_orders_get: returned %s orders", len(data))
        return data

    def exposed_history_orders_total(self, date_from: Any, date_to: Any) -> int | None:
        """Get total history orders count."""
        log.debug("exposed_history_orders_total: from=%s to=%s", date_from, date_to)
        result = MT5Service._mt5_module.history_orders_total(date_from, date_to)
        log.debug("exposed_history_orders_total: result=%s", result)
        return result

    def exposed_history_orders_get(
        self,
        date_from: Any = None,
        date_to: Any = None,
        group: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> Any:
        """Get history orders with data materialization."""
        log.debug(
            "exposed_history_orders_get: from=%s to=%s group=%s ticket=%s pos=%s",
            date_from,
            date_to,
            group,
            ticket,
            position,
        )
        kwargs: dict[str, Any] = {}
        if date_from:
            kwargs["date_from"] = date_from
        if date_to:
            kwargs["date_to"] = date_to
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if position:
            kwargs["position"] = position
        if kwargs:
            result = MT5Service._mt5_module.history_orders_get(**kwargs)
        else:
            result = MT5Service._mt5_module.history_orders_get()
        if result is None:
            log.debug("exposed_history_orders_get: result=None")
            return None
        data = tuple(o._asdict() for o in result)
        log.debug("exposed_history_orders_get: returned %s orders", len(data))
        return data

    def exposed_history_deals_total(self, date_from: Any, date_to: Any) -> int | None:
        """Get total history deals count."""
        log.debug("exposed_history_deals_total: from=%s to=%s", date_from, date_to)
        result = MT5Service._mt5_module.history_deals_total(date_from, date_to)
        log.debug("exposed_history_deals_total: result=%s", result)
        return result

    def exposed_history_deals_get(
        self,
        date_from: Any = None,
        date_to: Any = None,
        group: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> Any:
        """Get history deals with data materialization."""
        log.debug(
            "exposed_history_deals_get: from=%s to=%s group=%s ticket=%s pos=%s",
            date_from,
            date_to,
            group,
            ticket,
            position,
        )
        kwargs: dict[str, Any] = {}
        if date_from:
            kwargs["date_from"] = date_from
        if date_to:
            kwargs["date_to"] = date_to
        if group:
            kwargs["group"] = group
        if ticket:
            kwargs["ticket"] = ticket
        if position:
            kwargs["position"] = position
        if kwargs:
            result = MT5Service._mt5_module.history_deals_get(**kwargs)
        else:
            result = MT5Service._mt5_module.history_deals_get()
        if result is None:
            log.debug("exposed_history_deals_get: result=None")
            return None
        data = tuple(d._asdict() for d in result)
        log.debug("exposed_history_deals_get: returned %s deals", len(data))
        return data

    # =========================================================================
    # MARKET DEPTH (DOM) FUNCTIONS
    # =========================================================================

    def exposed_market_book_add(self, symbol: str) -> bool:
        """Subscribe to Market Depth (DOM) for a symbol."""
        log.debug("exposed_market_book_add: symbol=%s", symbol)
        result = MT5Service._mt5_module.market_book_add(symbol)
        log.debug("exposed_market_book_add: result=%s", result)
        return result

    def exposed_market_book_get(self, symbol: str) -> Any:
        """Get Market Depth (DOM) entries for a symbol."""
        log.debug("exposed_market_book_get: symbol=%s", symbol)
        result = MT5Service._mt5_module.market_book_get(symbol)
        if result is None:
            log.debug("exposed_market_book_get: result=None")
            return None
        # Each entry is a BookInfo named tuple
        data = tuple(entry._asdict() for entry in result)
        log.debug("exposed_market_book_get: returned %s entries", len(data))
        return data

    def exposed_market_book_release(self, symbol: str) -> bool:
        """Unsubscribe from Market Depth (DOM) for a symbol."""
        log.debug("exposed_market_book_release: symbol=%s", symbol)
        result = MT5Service._mt5_module.market_book_release(symbol)
        log.debug("exposed_market_book_release: result=%s", result)
        return result

    # =========================================================================
    # CONSTANTS AND ENUMS
    # =========================================================================

    def exposed_get_constants(self) -> dict[str, Any]:
        """Get all MT5 constants for client-side usage.

        Returns dict with all timeframes, order types, trade actions,
        symbol properties, account modes, deal entries/reasons, etc.
        """
        self._ensure_mt5_loaded()
        log.debug("exposed_get_constants: called")
        mt5 = MT5Service._mt5_module
        constants: dict[str, Any] = {}

        # Helper to add constants from list
        def _add_constants(names: list[str]) -> None:
            for name in names:
                if hasattr(mt5, name):
                    constants[name] = getattr(mt5, name)

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

        # Symbol calculation modes
        _add_constants([
            "SYMBOL_CALC_MODE_FOREX", "SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE",
            "SYMBOL_CALC_MODE_FUTURES", "SYMBOL_CALC_MODE_CFD",
            "SYMBOL_CALC_MODE_CFDINDEX", "SYMBOL_CALC_MODE_CFDLEVERAGE",
            "SYMBOL_CALC_MODE_EXCH_STOCKS", "SYMBOL_CALC_MODE_EXCH_FUTURES",
            "SYMBOL_CALC_MODE_EXCH_FUTURES_FORTS", "SYMBOL_CALC_MODE_EXCH_BONDS",
            "SYMBOL_CALC_MODE_EXCH_STOCKS_MOEX", "SYMBOL_CALC_MODE_EXCH_BONDS_MOEX",
            "SYMBOL_CALC_MODE_SERV_COLLATERAL",
        ])

        # Symbol swap modes
        _add_constants([
            "SYMBOL_SWAP_MODE_DISABLED", "SYMBOL_SWAP_MODE_POINTS",
            "SYMBOL_SWAP_MODE_CURRENCY_SYMBOL", "SYMBOL_SWAP_MODE_CURRENCY_MARGIN",
            "SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT", "SYMBOL_SWAP_MODE_INTEREST_CURRENT",
            "SYMBOL_SWAP_MODE_INTEREST_OPEN", "SYMBOL_SWAP_MODE_REOPEN_CURRENT",
            "SYMBOL_SWAP_MODE_REOPEN_BID",
        ])

        # Account trade modes
        _add_constants([
            "ACCOUNT_TRADE_MODE_DEMO", "ACCOUNT_TRADE_MODE_CONTEST",
            "ACCOUNT_TRADE_MODE_REAL",
        ])

        # Account stopout modes
        _add_constants([
            "ACCOUNT_STOPOUT_MODE_PERCENT", "ACCOUNT_STOPOUT_MODE_MONEY",
        ])

        # Account margin modes
        _add_constants([
            "ACCOUNT_MARGIN_MODE_RETAIL_NETTING",
            "ACCOUNT_MARGIN_MODE_EXCHANGE",
            "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING",
        ])

        # Trade return codes - complete list
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
            "TRADE_RETCODE_NO_CHANGES", "TRADE_RETCODE_SERVER_DISABLES_AT",
            "TRADE_RETCODE_CLIENT_DISABLES_AT", "TRADE_RETCODE_LOCKED",
            "TRADE_RETCODE_FROZEN", "TRADE_RETCODE_INVALID_FILL",
            "TRADE_RETCODE_CONNECTION", "TRADE_RETCODE_ONLY_REAL",
            "TRADE_RETCODE_LIMIT_ORDERS", "TRADE_RETCODE_LIMIT_VOLUME",
            "TRADE_RETCODE_INVALID_ORDER", "TRADE_RETCODE_POSITION_CLOSED",
            "TRADE_RETCODE_INVALID_CLOSE_VOLUME", "TRADE_RETCODE_CLOSE_ORDER_EXIST",
            "TRADE_RETCODE_LIMIT_POSITIONS", "TRADE_RETCODE_REJECT_CANCEL",
            "TRADE_RETCODE_LONG_ONLY", "TRADE_RETCODE_SHORT_ONLY",
            "TRADE_RETCODE_CLOSE_ONLY", "TRADE_RETCODE_FIFO_CLOSE",
            "TRADE_RETCODE_HEDGE_PROHIBITED",
        ])

        log.debug("exposed_get_constants: returned %s constants", len(constants))
        return constants


def _setup_logging(debug: bool = False) -> None:
    """Configure logging for the bridge."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _graceful_shutdown(signum: int, frame: FrameType | None) -> None:  # noqa: ARG001
    """Handle shutdown signals for clean container stops."""
    sig_name = signal.Signals(signum).name
    log.info("Received %s, shutting down gracefully...", sig_name)
    if _server is not None:
        _server.close()
    sys.exit(0)


def main() -> int:
    """Run the RPyC bridge server."""
    global _server  # noqa: PLW0603

    parser = argparse.ArgumentParser(description="MT5 RPyC Bridge Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind"  # noqa: S104
    )
    parser.add_argument("-p", "--port", type=int, default=8001, help="Port")
    parser.add_argument("--threads", type=int, default=10, help="Worker threads")
    parser.add_argument("--timeout", type=int, default=300, help="Request timeout")
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    _setup_logging(debug=args.debug)

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    log.info("Starting MT5Service on %s:%s", args.host, args.port)
    log.info("Python %s", sys.version)
    log.debug("Debug logging enabled")
    log.debug("Threads=%s, Timeout=%s", args.threads, args.timeout)

    _server = ThreadPoolServer(
        MT5Service,
        hostname=args.host,
        port=args.port,
        reuse_addr=True,
        nbThreads=args.threads,
        protocol_config={
            "allow_public_attrs": True,
            "allow_pickle": True,
            "sync_request_timeout": args.timeout,
        },
    )

    try:
        log.info("Server started, waiting for connections...")
        _server.start()
    except KeyboardInterrupt:
        log.info("Server interrupted by user")
    except Exception:
        log.exception("Server error")
        return 1
    finally:
        if _server is not None:
            _server.close()
        log.info("Server stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
