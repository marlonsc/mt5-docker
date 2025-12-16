from datetime import datetime

# Terminal functions
def initialize(
    path: str | None = None,
    login: int | None = None,
    password: str | None = None,
    server: str | None = None,
    timeout: int | None = None,
    portable: bool = False,
) -> bool: ...
def login(login: int, password: str, server: str, timeout: int = 60000) -> bool: ...
def shutdown() -> None: ...
def version() -> tuple[int, int, str] | None: ...
def last_error() -> tuple[int, str]: ...
def terminal_info() -> TerminalInfo: ...
def account_info() -> AccountInfo: ...

# Symbol functions
def symbols_total() -> int: ...
def symbols_get(group: str | None = None) -> tuple[SymbolInfo, ...]: ...
def symbol_info(symbol: str) -> SymbolInfo | None: ...
def symbol_info_tick(symbol: str) -> Tick | None: ...
def symbol_select(symbol: str, enable: bool = True) -> bool: ...

# Market data functions
def copy_rates_from(
    symbol: str,
    timeframe: int,
    date_from: datetime | int,
    count: int,
) -> tuple[tuple[int, float, float, float, float, int, int, int], ...]: ...
def copy_rates_from_pos(
    symbol: str,
    timeframe: int,
    start_pos: int,
    count: int,
) -> tuple[tuple[int, float, float, float, float, int, int, int], ...]: ...
def copy_rates_range(
    symbol: str,
    timeframe: int,
    date_from: datetime | int,
    date_to: datetime | int,
) -> tuple[tuple[int, float, float, float, float, int, int, int], ...]: ...
def copy_ticks_from(
    symbol: str,
    date_from: datetime | int,
    count: int,
    flags: int,
) -> tuple[Tick, ...]: ...
def copy_ticks_range(
    symbol: str,
    date_from: datetime | int,
    date_to: datetime | int,
    flags: int,
) -> tuple[Tick, ...]: ...

# Trading functions
def order_calc_margin(
    action: int, symbol: str, volume: float, price: float
) -> float | None: ...
def order_calc_profit(
    action: int,
    symbol: str,
    volume: float,
    price_open: float,
    price_close: float,
) -> float | None: ...
def order_check(request: dict[str, int | float | str]) -> OrderCheckResult: ...
def order_send(request: dict[str, int | float | str]) -> OrderSendResult: ...

# Position functions
def positions_total() -> int: ...
def positions_get(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
) -> tuple[TradePosition, ...]: ...

# Order functions
def orders_total() -> int: ...
def orders_get(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
) -> tuple[TradeOrder, ...]: ...

# History functions
def history_orders_total(
    date_from: datetime | int, date_to: datetime | int
) -> int | None: ...
def history_orders_get(
    date_from: datetime | int | None = None,
    date_to: datetime | int | None = None,
    group: str | None = None,
    ticket: int | None = None,
    position: int | None = None,
) -> tuple[TradeOrder, ...]: ...
def history_deals_total(
    date_from: datetime | int, date_to: datetime | int
) -> int | None: ...
def history_deals_get(
    date_from: datetime | int | None = None,
    date_to: datetime | int | None = None,
    group: str | None = None,
    ticket: int | None = None,
    position: int | None = None,
) -> tuple[TradeDeal, ...]: ...

# Data classes (namedtuples)
class TerminalInfo:
    community_account: bool
    community_connection: bool
    connected: bool
    dlls_allowed: bool
    trade_allowed: bool
    tradeapi_disabled: bool
    email_enabled: bool
    ftp_enabled: bool
    notifications_enabled: bool
    mqid: bool
    build: int
    maxbars: int
    codepage: int
    ping_last: int
    community_balance: float
    retransmission: float
    company: str
    name: str
    language: str
    path: str
    data_path: str
    commondata_path: str

class AccountInfo:
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    fifo_close: bool
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    assets: float
    liabilities: float
    commission_blocked: float
    name: str
    server: str
    currency: str
    company: str

class SymbolInfo:
    custom: bool
    chart_mode: int
    select: bool
    visible: bool
    session_deals: int
    session_buy_orders: int
    session_sell_orders: int
    volume: int
    volumehigh: int
    volumelow: int
    time: int
    digits: int
    spread: int
    spread_float: bool
    ticks_bookdepth: int
    trade_calc_mode: int
    trade_mode: int
    start_time: int
    expiration_time: int
    trade_stops_level: int
    trade_freeze_level: int
    trade_exemode: int
    swap_mode: int
    swap_rollover3days: int
    margin_hedged_use_leg: bool
    expiration_mode: int
    filling_mode: int
    order_mode: int
    order_gtc_mode: int
    option_mode: int
    option_right: int
    bid: float
    bidhigh: float
    bidlow: float
    ask: float
    askhigh: float
    asklow: float
    last: float
    lasthigh: float
    lastlow: float
    volume_real: float
    volumehigh_real: float
    volumelow_real: float
    option_strike: float
    point: float
    trade_tick_value: float
    trade_tick_value_profit: float
    trade_tick_value_loss: float
    trade_tick_size: float
    trade_contract_size: float
    trade_accrued_interest: float
    trade_face_value: float
    trade_liquidity_rate: float
    volume_min: float
    volume_max: float
    volume_step: float
    volume_limit: float
    swap_long: float
    swap_short: float
    margin_initial: float
    margin_maintenance: float
    session_volume: float
    session_turnover: float
    session_interest: float
    session_buy_orders_volume: float
    session_sell_orders_volume: float
    session_open: float
    session_close: float
    session_aw: float
    session_price_settlement: float
    session_price_limit_min: float
    session_price_limit_max: float
    margin_hedged: float
    price_change: float
    price_volatility: float
    price_theoretical: float
    price_greeks_delta: float
    price_greeks_theta: float
    price_greeks_gamma: float
    price_greeks_vega: float
    price_greeks_rho: float
    price_greeks_omega: float
    price_sensitivity: float
    basis: str
    category: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    bank: str
    description: str
    exchange: str
    formula: str
    isin: str
    name: str
    page: str
    path: str

class Tick:
    time: int
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int
    volume_real: float

class TradePosition:
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str

class TradeOrder:
    ticket: int
    time_setup: int
    time_setup_msc: int
    time_done: int
    time_done_msc: int
    time_expiration: int
    type: int
    type_time: int
    type_filling: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str

class TradeDeal:
    ticket: int
    order: int
    time: int
    time_msc: int
    type: int
    entry: int
    magic: int
    position_id: int
    reason: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    symbol: str
    comment: str
    external_id: str

class OrderCheckResult:
    retcode: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    comment: str
    request: dict[str, int | float | str]

class OrderSendResult:
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request_id: int
    retcode_external: int
    request: dict[str, int | float | str]
