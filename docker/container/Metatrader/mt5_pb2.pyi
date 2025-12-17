import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Empty(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

type Global___Empty = Empty

@typing.final
class BoolResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    RESULT_FIELD_NUMBER: builtins.int
    result: builtins.bool
    def __init__(
        self,
        *,
        result: builtins.bool = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing.Literal["result", b"result"]
    ) -> None: ...

type Global___BoolResponse = BoolResponse

@typing.final
class IntResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.int
    def __init__(
        self,
        *,
        value: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing.Literal["value", b"value"]
    ) -> None: ...

type Global___IntResponse = IntResponse

@typing.final
class FloatResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.float
    def __init__(
        self,
        *,
        value: builtins.float | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["_value", b"_value", "value", b"value"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["_value", b"_value", "value", b"value"],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_value", b"_value"],
    ) -> typing.Literal["value"] | None: ...

type Global___FloatResponse = FloatResponse

@typing.final
class ErrorInfo(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    CODE_FIELD_NUMBER: builtins.int
    MESSAGE_FIELD_NUMBER: builtins.int
    code: builtins.int
    message: builtins.str
    def __init__(
        self,
        *,
        code: builtins.int = ...,
        message: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["code", b"code", "message", b"message"],
    ) -> None: ...

type Global___ErrorInfo = ErrorInfo

@typing.final
class MT5Version(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    MAJOR_FIELD_NUMBER: builtins.int
    MINOR_FIELD_NUMBER: builtins.int
    BUILD_FIELD_NUMBER: builtins.int
    major: builtins.int
    minor: builtins.int
    build: builtins.str
    def __init__(
        self,
        *,
        major: builtins.int = ...,
        minor: builtins.int = ...,
        build: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "build",
            b"build",
            "major",
            b"major",
            "minor",
            b"minor",
        ],
    ) -> None: ...

type Global___MT5Version = MT5Version

@typing.final
class Constants(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class ValuesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.int
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.int = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    VALUES_FIELD_NUMBER: builtins.int
    @property
    def values(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.str, builtins.int
    ]: ...
    def __init__(
        self,
        *,
        values: collections.abc.Mapping[builtins.str, builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing.Literal["values", b"values"]
    ) -> None: ...

type Global___Constants = Constants

@typing.final
class DictData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    JSON_DATA_FIELD_NUMBER: builtins.int
    json_data: builtins.str
    """JSON string of the dict"""
    def __init__(
        self,
        *,
        json_data: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["json_data", b"json_data"],
    ) -> None: ...

type Global___DictData = DictData

@typing.final
class DictList(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    JSON_ITEMS_FIELD_NUMBER: builtins.int
    @property
    def json_items(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        json_items: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["json_items", b"json_items"],
    ) -> None: ...

type Global___DictList = DictList

@typing.final
class NumpyArray(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_FIELD_NUMBER: builtins.int
    DTYPE_FIELD_NUMBER: builtins.int
    SHAPE_FIELD_NUMBER: builtins.int
    data: builtins.bytes
    """numpy.tobytes()"""
    dtype: builtins.str
    """numpy dtype string"""
    @property
    def shape(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        data: builtins.bytes = ...,
        dtype: builtins.str = ...,
        shape: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "data",
            b"data",
            "dtype",
            b"dtype",
            "shape",
            b"shape",
        ],
    ) -> None: ...

type Global___NumpyArray = NumpyArray

@typing.final
class SymbolsResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    TOTAL_FIELD_NUMBER: builtins.int
    CHUNKS_FIELD_NUMBER: builtins.int
    total: builtins.int
    @property
    def chunks(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        total: builtins.int = ...,
        chunks: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["chunks", b"chunks", "total", b"total"],
    ) -> None: ...

type Global___SymbolsResponse = SymbolsResponse

@typing.final
class HealthStatus(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    HEALTHY_FIELD_NUMBER: builtins.int
    MT5_AVAILABLE_FIELD_NUMBER: builtins.int
    CONNECTED_FIELD_NUMBER: builtins.int
    TRADE_ALLOWED_FIELD_NUMBER: builtins.int
    BUILD_FIELD_NUMBER: builtins.int
    REASON_FIELD_NUMBER: builtins.int
    healthy: builtins.bool
    mt5_available: builtins.bool
    connected: builtins.bool
    trade_allowed: builtins.bool
    build: builtins.int
    reason: builtins.str
    def __init__(
        self,
        *,
        healthy: builtins.bool = ...,
        mt5_available: builtins.bool = ...,
        connected: builtins.bool = ...,
        trade_allowed: builtins.bool = ...,
        build: builtins.int = ...,
        reason: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "build",
            b"build",
            "connected",
            b"connected",
            "healthy",
            b"healthy",
            "mt5_available",
            b"mt5_available",
            "reason",
            b"reason",
            "trade_allowed",
            b"trade_allowed",
        ],
    ) -> None: ...

type Global___HealthStatus = HealthStatus

@typing.final
class InitRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PATH_FIELD_NUMBER: builtins.int
    LOGIN_FIELD_NUMBER: builtins.int
    PASSWORD_FIELD_NUMBER: builtins.int
    SERVER_FIELD_NUMBER: builtins.int
    TIMEOUT_FIELD_NUMBER: builtins.int
    PORTABLE_FIELD_NUMBER: builtins.int
    path: builtins.str
    login: builtins.int
    password: builtins.str
    server: builtins.str
    timeout: builtins.int
    portable: builtins.bool
    def __init__(
        self,
        *,
        path: builtins.str | None = ...,
        login: builtins.int | None = ...,
        password: builtins.str | None = ...,
        server: builtins.str | None = ...,
        timeout: builtins.int | None = ...,
        portable: builtins.bool = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "_login",
            b"_login",
            "_password",
            b"_password",
            "_path",
            b"_path",
            "_server",
            b"_server",
            "_timeout",
            b"_timeout",
            "login",
            b"login",
            "password",
            b"password",
            "path",
            b"path",
            "server",
            b"server",
            "timeout",
            b"timeout",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "_login",
            b"_login",
            "_password",
            b"_password",
            "_path",
            b"_path",
            "_server",
            b"_server",
            "_timeout",
            b"_timeout",
            "login",
            b"login",
            "password",
            b"password",
            "path",
            b"path",
            "portable",
            b"portable",
            "server",
            b"server",
            "timeout",
            b"timeout",
        ],
    ) -> None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_login", b"_login"],
    ) -> typing.Literal["login"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_password", b"_password"],
    ) -> typing.Literal["password"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_path", b"_path"],
    ) -> typing.Literal["path"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_server", b"_server"],
    ) -> typing.Literal["server"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_timeout", b"_timeout"],
    ) -> typing.Literal["timeout"] | None: ...

type Global___InitRequest = InitRequest

@typing.final
class LoginRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    LOGIN_FIELD_NUMBER: builtins.int
    PASSWORD_FIELD_NUMBER: builtins.int
    SERVER_FIELD_NUMBER: builtins.int
    TIMEOUT_FIELD_NUMBER: builtins.int
    login: builtins.int
    password: builtins.str
    server: builtins.str
    timeout: builtins.int
    def __init__(
        self,
        *,
        login: builtins.int = ...,
        password: builtins.str = ...,
        server: builtins.str = ...,
        timeout: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "login",
            b"login",
            "password",
            b"password",
            "server",
            b"server",
            "timeout",
            b"timeout",
        ],
    ) -> None: ...

type Global___LoginRequest = LoginRequest

@typing.final
class SymbolRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing.Literal["symbol", b"symbol"]
    ) -> None: ...

type Global___SymbolRequest = SymbolRequest

@typing.final
class SymbolsRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    GROUP_FIELD_NUMBER: builtins.int
    group: builtins.str
    def __init__(
        self,
        *,
        group: builtins.str | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["_group", b"_group", "group", b"group"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["_group", b"_group", "group", b"group"],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_group", b"_group"],
    ) -> typing.Literal["group"] | None: ...

type Global___SymbolsRequest = SymbolsRequest

@typing.final
class SymbolSelectRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    ENABLE_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    enable: builtins.bool
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        enable: builtins.bool = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["enable", b"enable", "symbol", b"symbol"],
    ) -> None: ...

type Global___SymbolSelectRequest = SymbolSelectRequest

@typing.final
class CopyRatesRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    TIMEFRAME_FIELD_NUMBER: builtins.int
    DATE_FROM_FIELD_NUMBER: builtins.int
    COUNT_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    timeframe: builtins.int
    date_from: builtins.int
    count: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        timeframe: builtins.int = ...,
        date_from: builtins.int = ...,
        count: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "count",
            b"count",
            "date_from",
            b"date_from",
            "symbol",
            b"symbol",
            "timeframe",
            b"timeframe",
        ],
    ) -> None: ...

type Global___CopyRatesRequest = CopyRatesRequest

@typing.final
class CopyRatesPosRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    TIMEFRAME_FIELD_NUMBER: builtins.int
    START_POS_FIELD_NUMBER: builtins.int
    COUNT_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    timeframe: builtins.int
    start_pos: builtins.int
    count: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        timeframe: builtins.int = ...,
        start_pos: builtins.int = ...,
        count: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "count",
            b"count",
            "start_pos",
            b"start_pos",
            "symbol",
            b"symbol",
            "timeframe",
            b"timeframe",
        ],
    ) -> None: ...

type Global___CopyRatesPosRequest = CopyRatesPosRequest

@typing.final
class CopyRatesRangeRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    TIMEFRAME_FIELD_NUMBER: builtins.int
    DATE_FROM_FIELD_NUMBER: builtins.int
    DATE_TO_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    timeframe: builtins.int
    date_from: builtins.int
    date_to: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        timeframe: builtins.int = ...,
        date_from: builtins.int = ...,
        date_to: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "date_from",
            b"date_from",
            "date_to",
            b"date_to",
            "symbol",
            b"symbol",
            "timeframe",
            b"timeframe",
        ],
    ) -> None: ...

type Global___CopyRatesRangeRequest = CopyRatesRangeRequest

@typing.final
class CopyTicksRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    DATE_FROM_FIELD_NUMBER: builtins.int
    COUNT_FIELD_NUMBER: builtins.int
    FLAGS_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    date_from: builtins.int
    count: builtins.int
    flags: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        date_from: builtins.int = ...,
        count: builtins.int = ...,
        flags: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "count",
            b"count",
            "date_from",
            b"date_from",
            "flags",
            b"flags",
            "symbol",
            b"symbol",
        ],
    ) -> None: ...

type Global___CopyTicksRequest = CopyTicksRequest

@typing.final
class CopyTicksRangeRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    DATE_FROM_FIELD_NUMBER: builtins.int
    DATE_TO_FIELD_NUMBER: builtins.int
    FLAGS_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    date_from: builtins.int
    date_to: builtins.int
    flags: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str = ...,
        date_from: builtins.int = ...,
        date_to: builtins.int = ...,
        flags: builtins.int = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "date_from",
            b"date_from",
            "date_to",
            b"date_to",
            "flags",
            b"flags",
            "symbol",
            b"symbol",
        ],
    ) -> None: ...

type Global___CopyTicksRangeRequest = CopyTicksRangeRequest

@typing.final
class OrderRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    JSON_REQUEST_FIELD_NUMBER: builtins.int
    json_request: builtins.str
    """JSON-serialized order dict"""
    def __init__(
        self,
        *,
        json_request: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["json_request", b"json_request"],
    ) -> None: ...

type Global___OrderRequest = OrderRequest

@typing.final
class PositionsRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    GROUP_FIELD_NUMBER: builtins.int
    TICKET_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    group: builtins.str
    ticket: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str | None = ...,
        group: builtins.str | None = ...,
        ticket: builtins.int | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "_group",
            b"_group",
            "_symbol",
            b"_symbol",
            "_ticket",
            b"_ticket",
            "group",
            b"group",
            "symbol",
            b"symbol",
            "ticket",
            b"ticket",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "_group",
            b"_group",
            "_symbol",
            b"_symbol",
            "_ticket",
            b"_ticket",
            "group",
            b"group",
            "symbol",
            b"symbol",
            "ticket",
            b"ticket",
        ],
    ) -> None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_group", b"_group"],
    ) -> typing.Literal["group"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_symbol", b"_symbol"],
    ) -> typing.Literal["symbol"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_ticket", b"_ticket"],
    ) -> typing.Literal["ticket"] | None: ...

type Global___PositionsRequest = PositionsRequest

@typing.final
class OrdersRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SYMBOL_FIELD_NUMBER: builtins.int
    GROUP_FIELD_NUMBER: builtins.int
    TICKET_FIELD_NUMBER: builtins.int
    symbol: builtins.str
    group: builtins.str
    ticket: builtins.int
    def __init__(
        self,
        *,
        symbol: builtins.str | None = ...,
        group: builtins.str | None = ...,
        ticket: builtins.int | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "_group",
            b"_group",
            "_symbol",
            b"_symbol",
            "_ticket",
            b"_ticket",
            "group",
            b"group",
            "symbol",
            b"symbol",
            "ticket",
            b"ticket",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "_group",
            b"_group",
            "_symbol",
            b"_symbol",
            "_ticket",
            b"_ticket",
            "group",
            b"group",
            "symbol",
            b"symbol",
            "ticket",
            b"ticket",
        ],
    ) -> None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_group", b"_group"],
    ) -> typing.Literal["group"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_symbol", b"_symbol"],
    ) -> typing.Literal["symbol"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_ticket", b"_ticket"],
    ) -> typing.Literal["ticket"] | None: ...

type Global___OrdersRequest = OrdersRequest

@typing.final
class HistoryRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATE_FROM_FIELD_NUMBER: builtins.int
    DATE_TO_FIELD_NUMBER: builtins.int
    GROUP_FIELD_NUMBER: builtins.int
    TICKET_FIELD_NUMBER: builtins.int
    POSITION_FIELD_NUMBER: builtins.int
    date_from: builtins.int
    date_to: builtins.int
    group: builtins.str
    ticket: builtins.int
    position: builtins.int
    def __init__(
        self,
        *,
        date_from: builtins.int | None = ...,
        date_to: builtins.int | None = ...,
        group: builtins.str | None = ...,
        ticket: builtins.int | None = ...,
        position: builtins.int | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "_date_from",
            b"_date_from",
            "_date_to",
            b"_date_to",
            "_group",
            b"_group",
            "_position",
            b"_position",
            "_ticket",
            b"_ticket",
            "date_from",
            b"date_from",
            "date_to",
            b"date_to",
            "group",
            b"group",
            "position",
            b"position",
            "ticket",
            b"ticket",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "_date_from",
            b"_date_from",
            "_date_to",
            b"_date_to",
            "_group",
            b"_group",
            "_position",
            b"_position",
            "_ticket",
            b"_ticket",
            "date_from",
            b"date_from",
            "date_to",
            b"date_to",
            "group",
            b"group",
            "position",
            b"position",
            "ticket",
            b"ticket",
        ],
    ) -> None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_date_from", b"_date_from"],
    ) -> typing.Literal["date_from"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_date_to", b"_date_to"],
    ) -> typing.Literal["date_to"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_group", b"_group"],
    ) -> typing.Literal["group"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_position", b"_position"],
    ) -> typing.Literal["position"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal["_ticket", b"_ticket"],
    ) -> typing.Literal["ticket"] | None: ...

type Global___HistoryRequest = HistoryRequest

@typing.final
class MarginRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ACTION_FIELD_NUMBER: builtins.int
    SYMBOL_FIELD_NUMBER: builtins.int
    VOLUME_FIELD_NUMBER: builtins.int
    PRICE_FIELD_NUMBER: builtins.int
    action: builtins.int
    symbol: builtins.str
    volume: builtins.float
    price: builtins.float
    def __init__(
        self,
        *,
        action: builtins.int = ...,
        symbol: builtins.str = ...,
        volume: builtins.float = ...,
        price: builtins.float = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "action",
            b"action",
            "price",
            b"price",
            "symbol",
            b"symbol",
            "volume",
            b"volume",
        ],
    ) -> None: ...

type Global___MarginRequest = MarginRequest

@typing.final
class ProfitRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ACTION_FIELD_NUMBER: builtins.int
    SYMBOL_FIELD_NUMBER: builtins.int
    VOLUME_FIELD_NUMBER: builtins.int
    PRICE_OPEN_FIELD_NUMBER: builtins.int
    PRICE_CLOSE_FIELD_NUMBER: builtins.int
    action: builtins.int
    symbol: builtins.str
    volume: builtins.float
    price_open: builtins.float
    price_close: builtins.float
    def __init__(
        self,
        *,
        action: builtins.int = ...,
        symbol: builtins.str = ...,
        volume: builtins.float = ...,
        price_open: builtins.float = ...,
        price_close: builtins.float = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "action",
            b"action",
            "price_close",
            b"price_close",
            "price_open",
            b"price_open",
            "symbol",
            b"symbol",
            "volume",
            b"volume",
        ],
    ) -> None: ...

type Global___ProfitRequest = ProfitRequest
