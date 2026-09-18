"""Typed runtime boundary for generated MT5 bridge modules."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Protocol, cast

import grpc

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type ProtoValue = JSONValue | bytes


class EmptyMessage(Protocol):
    """Empty protobuf message."""


class BoolResponseMessage(Protocol):
    result: bool


class IntResponseMessage(Protocol):
    value: int


class FloatResponseMessage(Protocol):
    value: float

    def HasField(self, name: str) -> bool: ...


class ErrorInfoMessage(Protocol):
    code: int
    message: str


class MT5VersionMessage(Protocol):
    major: int
    minor: int
    build: str


class ConstantsMessage(Protocol):
    values: dict[str, int]


class ParameterInfoMessage(Protocol):
    name: str
    type_hint: str
    kind: str
    has_default: bool
    default_value: str


class MethodInfoMessage(Protocol):
    name: str
    parameters: list[ParameterInfoMessage]
    return_type: str
    is_callable: bool


class MethodsResponseMessage(Protocol):
    methods: list[MethodInfoMessage]
    total: int


class FieldInfoMessage(Protocol):
    name: str
    type_hint: str
    index: int


class ModelInfoMessage(Protocol):
    name: str
    fields: list[FieldInfoMessage]
    is_namedtuple: bool


class ModelsResponseMessage(Protocol):
    models: list[ModelInfoMessage]
    total: int


class DictDataMessage(Protocol):
    json_data: str


class DictListMessage(Protocol):
    json_items: list[str]


class NumpyArrayMessage(Protocol):
    data: bytes
    dtype: str
    shape: list[int]


class SymbolsResponseMessage(Protocol):
    total: int
    chunks: list[str]


class HealthStatusMessage(Protocol):
    healthy: bool
    mt5_available: bool
    connected: bool
    trade_allowed: bool
    build: int
    reason: str


class InitRequestMessage(Protocol):
    path: str
    login: int
    password: str
    server: str
    timeout: int
    portable: bool

    def HasField(self, name: str) -> bool: ...


class LoginRequestMessage(Protocol):
    login: int
    password: str
    server: str
    timeout: int


class SymbolRequestMessage(Protocol):
    symbol: str


class SymbolsRequestMessage(Protocol):
    group: str

    def HasField(self, name: str) -> bool: ...


class SymbolSelectRequestMessage(Protocol):
    symbol: str
    enable: bool


class CopyRatesRequestMessage(Protocol):
    symbol: str
    timeframe: int
    date_from: int
    count: int


class CopyRatesPosRequestMessage(Protocol):
    symbol: str
    timeframe: int
    start_pos: int
    count: int


class CopyRatesRangeRequestMessage(Protocol):
    symbol: str
    timeframe: int
    date_from: int
    date_to: int


class CopyTicksRequestMessage(Protocol):
    symbol: str
    date_from: int
    count: int
    flags: int


class CopyTicksRangeRequestMessage(Protocol):
    symbol: str
    date_from: int
    date_to: int
    flags: int


class OrderRequestMessage(Protocol):
    json_request: str


class PositionsRequestMessage(Protocol):
    symbol: str
    group: str
    ticket: int

    def HasField(self, name: str) -> bool: ...


class OrdersRequestMessage(Protocol):
    symbol: str
    group: str
    ticket: int

    def HasField(self, name: str) -> bool: ...


class HistoryRequestMessage(Protocol):
    date_from: int
    date_to: int
    group: str
    ticket: int
    position: int

    def HasField(self, name: str) -> bool: ...


class MarginRequestMessage(Protocol):
    action: int
    symbol: str
    volume: float
    price: float


class ProfitRequestMessage(Protocol):
    action: int
    symbol: str
    volume: float
    price_open: float
    price_close: float


class ProvisionedAccountMessage(Protocol):
    login: int
    server: str
    email: str
    created_at: str
    login_confirmed: bool
    credentials_persisted: bool
    connected: bool
    source: str


class CreateDemoRequestMessage(Protocol):
    server: str
    email: str
    phone: str
    first_name: str
    last_name: str
    dob_year: str


class _EmptyFactory(Protocol):
    def __call__(self) -> EmptyMessage: ...


class _BoolResponseFactory(Protocol):
    def __call__(self, result: bool = False) -> BoolResponseMessage: ...


class _IntResponseFactory(Protocol):
    def __call__(self, value: int = 0) -> IntResponseMessage: ...


class _FloatResponseFactory(Protocol):
    def __call__(self, value: float = 0.0) -> FloatResponseMessage: ...


class _ErrorInfoFactory(Protocol):
    def __call__(self, code: int = 0, message: str = "") -> ErrorInfoMessage: ...


class _MT5VersionFactory(Protocol):
    def __call__(
        self, major: int = 0, minor: int = 0, build: str = ""
    ) -> MT5VersionMessage: ...


class _ConstantsFactory(Protocol):
    def __call__(self, values: dict[str, int]) -> ConstantsMessage: ...


class _ParameterInfoFactory(Protocol):
    def __call__(
        self,
        name: str = "",
        type_hint: str = "",
        kind: str = "",
        has_default: bool = False,
        default_value: str = "",
    ) -> ParameterInfoMessage: ...


class _MethodInfoFactory(Protocol):
    def __call__(
        self,
        name: str = "",
        parameters: list[ParameterInfoMessage] | None = None,
        return_type: str = "",
        is_callable: bool = False,
    ) -> MethodInfoMessage: ...


class _MethodsResponseFactory(Protocol):
    def __call__(
        self, methods: list[MethodInfoMessage] | None = None, total: int = 0
    ) -> MethodsResponseMessage: ...


class _FieldInfoFactory(Protocol):
    def __call__(
        self, name: str = "", type_hint: str = "", index: int = 0
    ) -> FieldInfoMessage: ...


class _ModelInfoFactory(Protocol):
    def __call__(
        self,
        name: str = "",
        fields: list[FieldInfoMessage] | None = None,
        is_namedtuple: bool = False,
    ) -> ModelInfoMessage: ...


class _ModelsResponseFactory(Protocol):
    def __call__(
        self, models: list[ModelInfoMessage] | None = None, total: int = 0
    ) -> ModelsResponseMessage: ...


class _DictDataFactory(Protocol):
    def __call__(self, json_data: str = "") -> DictDataMessage: ...


class _DictListFactory(Protocol):
    def __call__(self, json_items: list[str] | None = None) -> DictListMessage: ...


class _NumpyArrayFactory(Protocol):
    def __call__(
        self,
        data: bytes = b"",
        dtype: str = "",
        shape: list[int] | None = None,
    ) -> NumpyArrayMessage: ...


class _SymbolsResponseFactory(Protocol):
    def __call__(
        self, total: int = 0, chunks: list[str] | None = None
    ) -> SymbolsResponseMessage: ...


class _HealthStatusFactory(Protocol):
    def __call__(
        self,
        *,
        healthy: bool = False,
        mt5_available: bool = False,
        connected: bool = False,
        trade_allowed: bool = False,
        build: int = 0,
        reason: str = "",
    ) -> HealthStatusMessage: ...


class _InitRequestFactory(Protocol):
    def __call__(
        self,
        *,
        path: str = "",
        login: int = 0,
        password: str = "",
        server: str = "",
        timeout: int = 0,
        portable: bool = False,
    ) -> InitRequestMessage: ...


class _LoginRequestFactory(Protocol):
    def __call__(
        self,
        login: int = 0,
        password: str = "",
        server: str = "",
        timeout: int = 0,
    ) -> LoginRequestMessage: ...


class _SymbolRequestFactory(Protocol):
    def __call__(self, symbol: str = "") -> SymbolRequestMessage: ...


class _SymbolsRequestFactory(Protocol):
    def __call__(self, group: str = "") -> SymbolsRequestMessage: ...


class _SymbolSelectRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", enable: bool = False
    ) -> SymbolSelectRequestMessage: ...


class _CopyRatesRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", timeframe: int = 0, date_from: int = 0, count: int = 0
    ) -> CopyRatesRequestMessage: ...


class _CopyRatesPosRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", timeframe: int = 0, start_pos: int = 0, count: int = 0
    ) -> CopyRatesPosRequestMessage: ...


class _CopyRatesRangeRequestFactory(Protocol):
    def __call__(
        self,
        symbol: str = "",
        timeframe: int = 0,
        date_from: int = 0,
        date_to: int = 0,
    ) -> CopyRatesRangeRequestMessage: ...


class _CopyTicksRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", date_from: int = 0, count: int = 0, flags: int = 0
    ) -> CopyTicksRequestMessage: ...


class _CopyTicksRangeRequestFactory(Protocol):
    def __call__(
        self,
        symbol: str = "",
        date_from: int = 0,
        date_to: int = 0,
        flags: int = 0,
    ) -> CopyTicksRangeRequestMessage: ...


class _OrderRequestFactory(Protocol):
    def __call__(self, json_request: str = "") -> OrderRequestMessage: ...


class _PositionsRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", group: str = "", ticket: int = 0
    ) -> PositionsRequestMessage: ...


class _OrdersRequestFactory(Protocol):
    def __call__(
        self, symbol: str = "", group: str = "", ticket: int = 0
    ) -> OrdersRequestMessage: ...


class _HistoryRequestFactory(Protocol):
    def __call__(
        self,
        date_from: int = 0,
        date_to: int = 0,
        group: str = "",
        ticket: int = 0,
        position: int = 0,
    ) -> HistoryRequestMessage: ...


class _MarginRequestFactory(Protocol):
    def __call__(
        self,
        action: int = 0,
        symbol: str = "",
        volume: float = 0.0,
        price: float = 0.0,
    ) -> MarginRequestMessage: ...


class _ProfitRequestFactory(Protocol):
    def __call__(
        self,
        action: int = 0,
        symbol: str = "",
        volume: float = 0.0,
        price_open: float = 0.0,
        price_close: float = 0.0,
    ) -> ProfitRequestMessage: ...


class _ProvisionedAccountFactory(Protocol):
    def __call__(
        self,
        *,
        login: int = 0,
        server: str = "",
        email: str = "",
        created_at: str = "",
        login_confirmed: bool = False,
        credentials_persisted: bool = False,
        connected: bool = False,
        source: str = "",
    ) -> ProvisionedAccountMessage: ...


class _CreateDemoRequestFactory(Protocol):
    def __call__(
        self,
        *,
        server: str = "",
        email: str = "",
        phone: str = "",
        first_name: str = "",
        last_name: str = "",
        dob_year: str = "",
    ) -> CreateDemoRequestMessage: ...


class Mt5Pb2Module(Protocol):
    Empty: _EmptyFactory
    BoolResponse: _BoolResponseFactory
    IntResponse: _IntResponseFactory
    FloatResponse: _FloatResponseFactory
    ErrorInfo: _ErrorInfoFactory
    MT5Version: _MT5VersionFactory
    Constants: _ConstantsFactory
    ParameterInfo: _ParameterInfoFactory
    MethodInfo: _MethodInfoFactory
    MethodsResponse: _MethodsResponseFactory
    FieldInfo: _FieldInfoFactory
    ModelInfo: _ModelInfoFactory
    ModelsResponse: _ModelsResponseFactory
    DictData: _DictDataFactory
    DictList: _DictListFactory
    NumpyArray: _NumpyArrayFactory
    SymbolsResponse: _SymbolsResponseFactory
    HealthStatus: _HealthStatusFactory
    InitRequest: _InitRequestFactory
    LoginRequest: _LoginRequestFactory
    SymbolRequest: _SymbolRequestFactory
    SymbolsRequest: _SymbolsRequestFactory
    SymbolSelectRequest: _SymbolSelectRequestFactory
    CopyRatesRequest: _CopyRatesRequestFactory
    CopyRatesPosRequest: _CopyRatesPosRequestFactory
    CopyRatesRangeRequest: _CopyRatesRangeRequestFactory
    CopyTicksRequest: _CopyTicksRequestFactory
    CopyTicksRangeRequest: _CopyTicksRangeRequestFactory
    OrderRequest: _OrderRequestFactory
    PositionsRequest: _PositionsRequestFactory
    OrdersRequest: _OrdersRequestFactory
    HistoryRequest: _HistoryRequestFactory
    MarginRequest: _MarginRequestFactory
    ProfitRequest: _ProfitRequestFactory
    ProvisionedAccount: _ProvisionedAccountFactory
    CreateDemoRequest: _CreateDemoRequestFactory


class MT5ServiceStubProtocol(Protocol):
    def HealthCheck(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> HealthStatusMessage: ...
    def Initialize(
        self, request: InitRequestMessage, timeout: float | None = None
    ) -> BoolResponseMessage: ...
    def Login(
        self, request: LoginRequestMessage, timeout: float | None = None
    ) -> BoolResponseMessage: ...
    def Shutdown(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> EmptyMessage: ...
    def Version(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> MT5VersionMessage: ...
    def LastError(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> ErrorInfoMessage: ...
    def GetConstants(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> ConstantsMessage: ...
    def TerminalInfo(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> DictDataMessage: ...
    def AccountInfo(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> DictDataMessage: ...
    def SymbolsTotal(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> IntResponseMessage: ...
    def SymbolInfo(
        self, request: SymbolRequestMessage, timeout: float | None = None
    ) -> DictDataMessage: ...
    def PositionsGet(
        self, request: PositionsRequestMessage, timeout: float | None = None
    ) -> DictListMessage: ...
    def OrdersGet(
        self, request: OrdersRequestMessage, timeout: float | None = None
    ) -> DictListMessage: ...


class _MT5ServiceStubFactory(Protocol):
    def __call__(self, channel: grpc.Channel) -> MT5ServiceStubProtocol: ...


class MT5ServiceServicerBase:
    """Nominal base for the generated gRPC servicer class."""


class _AddServicerToServer(Protocol):
    def __call__(
        self, servicer: MT5ServiceServicerBase, server: grpc.Server
    ) -> None: ...


class Mt5Pb2GrpcModule(Protocol):
    MT5ServiceStub: _MT5ServiceStubFactory
    add_MT5ServiceServicer_to_server: _AddServicerToServer


class _TerminalInfo(Protocol):
    connected: bool
    trade_allowed: bool
    build: int

    def _asdict(self) -> dict[str, JSONValue]: ...


class _AccountInfo(Protocol):
    def _asdict(self) -> dict[str, JSONValue]: ...


class MetaTrader5Module(Protocol):
    __version__: str

    def initialize(self, **kwargs: str | int | bool) -> bool: ...
    def shutdown(self) -> None: ...
    def login(
        self, *, login: int, password: str, server: str, timeout: int
    ) -> bool: ...
    def version(self) -> tuple[int, int, str | int] | None: ...
    def last_error(self) -> tuple[int, str]: ...
    def terminal_info(self) -> _TerminalInfo | None: ...
    def account_info(self) -> _AccountInfo | None: ...
    def symbols_total(self) -> int: ...
    def symbols_get(self, group: str | None = None) -> tuple[object, ...] | None: ...
    def symbol_info(self, symbol: str) -> object | None: ...
    def symbol_info_tick(self, symbol: str) -> object | None: ...
    def symbol_select(self, symbol: str, enable: bool) -> bool: ...
    def copy_rates_from(
        self, symbol: str, timeframe: int, date_from: int, count: int
    ) -> object | None: ...
    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> object | None: ...
    def copy_rates_range(
        self, symbol: str, timeframe: int, date_from: int, date_to: int
    ) -> object | None: ...
    def copy_ticks_from(
        self, symbol: str, date_from: int, count: int, flags: int
    ) -> object | None: ...
    def copy_ticks_range(
        self, symbol: str, date_from: int, date_to: int, flags: int
    ) -> object | None: ...
    def order_calc_margin(
        self, action: int, symbol: str, volume: float, price: float
    ) -> float | None: ...
    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | None: ...
    def order_check(self, request: dict[str, JSONValue]) -> object | None: ...
    def order_send(self, request: dict[str, JSONValue]) -> object | None: ...
    def positions_total(self) -> int: ...
    def positions_get(self, **kwargs: str | int) -> tuple[object, ...] | None: ...
    def orders_total(self) -> int: ...
    def orders_get(self, **kwargs: str | int) -> tuple[object, ...] | None: ...
    def history_orders_total(self, date_from: int, date_to: int) -> int: ...
    def history_orders_get(
        self, *args: int, **kwargs: str | int
    ) -> tuple[object, ...] | None: ...
    def history_deals_total(self, date_from: int, date_to: int) -> int: ...
    def history_deals_get(
        self, *args: int, **kwargs: str | int
    ) -> tuple[object, ...] | None: ...
    def market_book_add(self, symbol: str) -> bool: ...
    def market_book_get(self, symbol: str) -> tuple[object, ...] | None: ...
    def market_book_release(self, symbol: str) -> bool: ...


def _load_module(name: str) -> ModuleType:
    return import_module(name, __package__)


mt5_pb2 = cast("Mt5Pb2Module", _load_module(".mt5_pb2"))
mt5_pb2_grpc = cast("Mt5Pb2GrpcModule", _load_module(".mt5_pb2_grpc"))
MT5ServiceStub = mt5_pb2_grpc.MT5ServiceStub
add_MT5ServiceServicer_to_server = mt5_pb2_grpc.add_MT5ServiceServicer_to_server
MetaTrader5 = cast("MetaTrader5Module", import_module("MetaTrader5"))
