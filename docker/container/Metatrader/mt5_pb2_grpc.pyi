import abc
import collections.abc
import typing
import typing as typing_extensions

import grpc
import grpc.aio

import mt5linux.mt5_pb2

_T = typing.TypeVar("_T")

class _MaybeAsyncIterator(
    collections.abc.AsyncIterator[_T],
    collections.abc.Iterator[_T],
    abc.ABC,
): ...
class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore[misc, type-arg]
    ...

GRPC_GENERATED_VERSION: str
GRPC_VERSION: str
_MT5ServiceHealthCheckType = typing_extensions.TypeVar(
    "_MT5ServiceHealthCheckType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.HealthStatus,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.HealthStatus,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.HealthStatus,
    ],
)

_MT5ServiceInitializeType = typing_extensions.TypeVar(
    "_MT5ServiceInitializeType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.InitRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.InitRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.InitRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
)

_MT5ServiceLoginType = typing_extensions.TypeVar(
    "_MT5ServiceLoginType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.LoginRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.LoginRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.LoginRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
)

_MT5ServiceShutdownType = typing_extensions.TypeVar(
    "_MT5ServiceShutdownType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Empty,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Empty,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Empty,
    ],
)

_MT5ServiceVersionType = typing_extensions.TypeVar(
    "_MT5ServiceVersionType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.MT5Version,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.MT5Version,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.MT5Version,
    ],
)

_MT5ServiceLastErrorType = typing_extensions.TypeVar(
    "_MT5ServiceLastErrorType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.ErrorInfo,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.ErrorInfo,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.ErrorInfo,
    ],
)

_MT5ServiceGetConstantsType = typing_extensions.TypeVar(
    "_MT5ServiceGetConstantsType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Constants,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Constants,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Constants,
    ],
)

_MT5ServiceTerminalInfoType = typing_extensions.TypeVar(
    "_MT5ServiceTerminalInfoType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServiceAccountInfoType = typing_extensions.TypeVar(
    "_MT5ServiceAccountInfoType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServiceSymbolsTotalType = typing_extensions.TypeVar(
    "_MT5ServiceSymbolsTotalType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
)

_MT5ServiceSymbolsGetType = typing_extensions.TypeVar(
    "_MT5ServiceSymbolsGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolsRequest,
        mt5linux.mt5_pb2.SymbolsResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolsRequest,
        mt5linux.mt5_pb2.SymbolsResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolsRequest,
        mt5linux.mt5_pb2.SymbolsResponse,
    ],
)

_MT5ServiceSymbolInfoType = typing_extensions.TypeVar(
    "_MT5ServiceSymbolInfoType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServiceSymbolInfoTickType = typing_extensions.TypeVar(
    "_MT5ServiceSymbolInfoTickType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServiceSymbolSelectType = typing_extensions.TypeVar(
    "_MT5ServiceSymbolSelectType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolSelectRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolSelectRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolSelectRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
)

_MT5ServiceCopyRatesFromType = typing_extensions.TypeVar(
    "_MT5ServiceCopyRatesFromType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
)

_MT5ServiceCopyRatesFromPosType = typing_extensions.TypeVar(
    "_MT5ServiceCopyRatesFromPosType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesPosRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesPosRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesPosRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
)

_MT5ServiceCopyRatesRangeType = typing_extensions.TypeVar(
    "_MT5ServiceCopyRatesRangeType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
)

_MT5ServiceCopyTicksFromType = typing_extensions.TypeVar(
    "_MT5ServiceCopyTicksFromType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
)

_MT5ServiceCopyTicksRangeType = typing_extensions.TypeVar(
    "_MT5ServiceCopyTicksRangeType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
)

_MT5ServiceOrderCalcMarginType = typing_extensions.TypeVar(
    "_MT5ServiceOrderCalcMarginType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.MarginRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.MarginRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.MarginRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
)

_MT5ServiceOrderCalcProfitType = typing_extensions.TypeVar(
    "_MT5ServiceOrderCalcProfitType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.ProfitRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.ProfitRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.ProfitRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
)

_MT5ServiceOrderCheckType = typing_extensions.TypeVar(
    "_MT5ServiceOrderCheckType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServiceOrderSendType = typing_extensions.TypeVar(
    "_MT5ServiceOrderSendType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
)

_MT5ServicePositionsTotalType = typing_extensions.TypeVar(
    "_MT5ServicePositionsTotalType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
)

_MT5ServicePositionsGetType = typing_extensions.TypeVar(
    "_MT5ServicePositionsGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.PositionsRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.PositionsRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.PositionsRequest,
        mt5linux.mt5_pb2.DictList,
    ],
)

_MT5ServiceOrdersTotalType = typing_extensions.TypeVar(
    "_MT5ServiceOrdersTotalType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
)

_MT5ServiceOrdersGetType = typing_extensions.TypeVar(
    "_MT5ServiceOrdersGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrdersRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrdersRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrdersRequest,
        mt5linux.mt5_pb2.DictList,
    ],
)

_MT5ServiceHistoryOrdersTotalType = typing_extensions.TypeVar(
    "_MT5ServiceHistoryOrdersTotalType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
)

_MT5ServiceHistoryOrdersGetType = typing_extensions.TypeVar(
    "_MT5ServiceHistoryOrdersGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
)

_MT5ServiceHistoryDealsTotalType = typing_extensions.TypeVar(
    "_MT5ServiceHistoryDealsTotalType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
)

_MT5ServiceHistoryDealsGetType = typing_extensions.TypeVar(
    "_MT5ServiceHistoryDealsGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
)

_MT5ServiceMarketBookAddType = typing_extensions.TypeVar(
    "_MT5ServiceMarketBookAddType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
)

_MT5ServiceMarketBookGetType = typing_extensions.TypeVar(
    "_MT5ServiceMarketBookGetType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictList,
    ],
)

_MT5ServiceMarketBookReleaseType = typing_extensions.TypeVar(
    "_MT5ServiceMarketBookReleaseType",
    grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
)

class MT5ServiceStub[
    MT5ServiceHealthCheckType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.HealthStatus,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.HealthStatus,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.HealthStatus,
    ],
    MT5ServiceInitializeType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.InitRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.InitRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.InitRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    MT5ServiceLoginType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.LoginRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.LoginRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.LoginRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    MT5ServiceShutdownType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.Empty,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.Empty,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Empty,
    ],
    MT5ServiceVersionType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.MT5Version,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.MT5Version,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.MT5Version,
    ],
    MT5ServiceLastErrorType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.ErrorInfo,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.ErrorInfo,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.ErrorInfo,
    ],
    MT5ServiceGetConstantsType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.Constants,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.Constants,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Constants,
    ],
    MT5ServiceTerminalInfoType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServiceAccountInfoType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServiceSymbolsTotalType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    MT5ServiceSymbolsGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolsRequest,
            mt5linux.mt5_pb2.SymbolsResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolsRequest,
            mt5linux.mt5_pb2.SymbolsResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolsRequest,
        mt5linux.mt5_pb2.SymbolsResponse,
    ],
    MT5ServiceSymbolInfoType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServiceSymbolInfoTickType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServiceSymbolSelectType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolSelectRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolSelectRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolSelectRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    MT5ServiceCopyRatesFromType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    MT5ServiceCopyRatesFromPosType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesPosRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesPosRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesPosRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    MT5ServiceCopyRatesRangeType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesRangeRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyRatesRangeRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    MT5ServiceCopyTicksFromType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyTicksRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyTicksRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    MT5ServiceCopyTicksRangeType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyTicksRangeRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.CopyTicksRangeRequest,
            mt5linux.mt5_pb2.NumpyArray,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    MT5ServiceOrderCalcMarginType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.MarginRequest,
            mt5linux.mt5_pb2.FloatResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.MarginRequest,
            mt5linux.mt5_pb2.FloatResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.MarginRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    MT5ServiceOrderCalcProfitType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.ProfitRequest,
            mt5linux.mt5_pb2.FloatResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.ProfitRequest,
            mt5linux.mt5_pb2.FloatResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.ProfitRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    MT5ServiceOrderCheckType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrderRequest,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrderRequest,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServiceOrderSendType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrderRequest,
            mt5linux.mt5_pb2.DictData,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrderRequest,
            mt5linux.mt5_pb2.DictData,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    MT5ServicePositionsTotalType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    MT5ServicePositionsGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.PositionsRequest,
            mt5linux.mt5_pb2.DictList,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.PositionsRequest,
            mt5linux.mt5_pb2.DictList,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.PositionsRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    MT5ServiceOrdersTotalType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.Empty,
            mt5linux.mt5_pb2.IntResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    MT5ServiceOrdersGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrdersRequest,
            mt5linux.mt5_pb2.DictList,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.OrdersRequest,
            mt5linux.mt5_pb2.DictList,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrdersRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    MT5ServiceHistoryOrdersTotalType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.IntResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.IntResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    MT5ServiceHistoryOrdersGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.DictList,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.DictList,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    MT5ServiceHistoryDealsTotalType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.IntResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.IntResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    MT5ServiceHistoryDealsGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.DictList,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.HistoryRequest,
            mt5linux.mt5_pb2.DictList,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    MT5ServiceMarketBookAddType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    MT5ServiceMarketBookGetType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictList,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.DictList,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    MT5ServiceMarketBookReleaseType: (
        grpc.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            mt5linux.mt5_pb2.SymbolRequest,
            mt5linux.mt5_pb2.BoolResponse,
        ],
    ) = grpc.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
]:
    @typing.overload
    def __init__(
        self: MT5ServiceStub[
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.HealthStatus,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.InitRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.LoginRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.Empty,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.MT5Version,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.ErrorInfo,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.Constants,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolsRequest,
                mt5linux.mt5_pb2.SymbolsResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolSelectRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesPosRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesRangeRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyTicksRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyTicksRangeRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.MarginRequest,
                mt5linux.mt5_pb2.FloatResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.ProfitRequest,
                mt5linux.mt5_pb2.FloatResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrderRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrderRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.PositionsRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrdersRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
        ],
        channel: grpc.Channel,
    ) -> None: ...
    @typing.overload
    def __init__(
        self: MT5ServiceStub[
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.HealthStatus,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.InitRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.LoginRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.Empty,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.MT5Version,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.ErrorInfo,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.Constants,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolsRequest,
                mt5linux.mt5_pb2.SymbolsResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolSelectRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesPosRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyRatesRangeRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyTicksRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.CopyTicksRangeRequest,
                mt5linux.mt5_pb2.NumpyArray,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.MarginRequest,
                mt5linux.mt5_pb2.FloatResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.ProfitRequest,
                mt5linux.mt5_pb2.FloatResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrderRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrderRequest,
                mt5linux.mt5_pb2.DictData,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.PositionsRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.Empty,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.OrdersRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.IntResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.HistoryRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.DictList,
            ],
            grpc.aio.UnaryUnaryMultiCallable[
                mt5linux.mt5_pb2.SymbolRequest,
                mt5linux.mt5_pb2.BoolResponse,
            ],
        ],
        channel: grpc.aio.Channel,
    ) -> None: ...

    HealthCheck: _MT5ServiceHealthCheckType
    """Terminal operations"""

    Initialize: _MT5ServiceInitializeType

    Login: _MT5ServiceLoginType

    Shutdown: _MT5ServiceShutdownType

    Version: _MT5ServiceVersionType

    LastError: _MT5ServiceLastErrorType

    GetConstants: _MT5ServiceGetConstantsType

    TerminalInfo: _MT5ServiceTerminalInfoType
    """Account/Terminal info"""

    AccountInfo: _MT5ServiceAccountInfoType

    SymbolsTotal: _MT5ServiceSymbolsTotalType
    """Symbol operations"""

    SymbolsGet: _MT5ServiceSymbolsGetType

    SymbolInfo: _MT5ServiceSymbolInfoType

    SymbolInfoTick: _MT5ServiceSymbolInfoTickType

    SymbolSelect: _MT5ServiceSymbolSelectType

    CopyRatesFrom: _MT5ServiceCopyRatesFromType
    """Market data - returns numpy arrays as bytes"""

    CopyRatesFromPos: _MT5ServiceCopyRatesFromPosType

    CopyRatesRange: _MT5ServiceCopyRatesRangeType

    CopyTicksFrom: _MT5ServiceCopyTicksFromType

    CopyTicksRange: _MT5ServiceCopyTicksRangeType

    OrderCalcMargin: _MT5ServiceOrderCalcMarginType
    """Trading operations"""

    OrderCalcProfit: _MT5ServiceOrderCalcProfitType

    OrderCheck: _MT5ServiceOrderCheckType

    OrderSend: _MT5ServiceOrderSendType

    PositionsTotal: _MT5ServicePositionsTotalType
    """Position operations"""

    PositionsGet: _MT5ServicePositionsGetType

    OrdersTotal: _MT5ServiceOrdersTotalType
    """Order operations"""

    OrdersGet: _MT5ServiceOrdersGetType

    HistoryOrdersTotal: _MT5ServiceHistoryOrdersTotalType
    """History operations"""

    HistoryOrdersGet: _MT5ServiceHistoryOrdersGetType

    HistoryDealsTotal: _MT5ServiceHistoryDealsTotalType

    HistoryDealsGet: _MT5ServiceHistoryDealsGetType

    MarketBookAdd: _MT5ServiceMarketBookAddType
    """Market Depth (DOM) operations"""

    MarketBookGet: _MT5ServiceMarketBookGetType

    MarketBookRelease: _MT5ServiceMarketBookReleaseType

type MT5ServiceAsyncStub = MT5ServiceStub[
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.HealthStatus,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.InitRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.LoginRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Empty,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.MT5Version,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.ErrorInfo,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.Constants,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolsRequest,
        mt5linux.mt5_pb2.SymbolsResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolSelectRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesPosRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyRatesRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.CopyTicksRangeRequest,
        mt5linux.mt5_pb2.NumpyArray,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.MarginRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.ProfitRequest,
        mt5linux.mt5_pb2.FloatResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrderRequest,
        mt5linux.mt5_pb2.DictData,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.PositionsRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.Empty,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.OrdersRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.IntResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.HistoryRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.DictList,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        mt5linux.mt5_pb2.SymbolRequest,
        mt5linux.mt5_pb2.BoolResponse,
    ],
]

class MT5ServiceServicer(abc.ABC):
    @abc.abstractmethod
    def HealthCheck(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.HealthStatus
        | collections.abc.Awaitable[mt5linux.mt5_pb2.HealthStatus]
    ): ...
    @abc.abstractmethod
    def Initialize(
        self,
        request: mt5linux.mt5_pb2.InitRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.BoolResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.BoolResponse]
    ): ...
    @abc.abstractmethod
    def Login(
        self,
        request: mt5linux.mt5_pb2.LoginRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.BoolResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.BoolResponse]
    ): ...
    @abc.abstractmethod
    def Shutdown(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.Empty
        | collections.abc.Awaitable[mt5linux.mt5_pb2.Empty]
    ): ...
    @abc.abstractmethod
    def Version(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.MT5Version
        | collections.abc.Awaitable[mt5linux.mt5_pb2.MT5Version]
    ): ...
    @abc.abstractmethod
    def LastError(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.ErrorInfo
        | collections.abc.Awaitable[mt5linux.mt5_pb2.ErrorInfo]
    ): ...
    @abc.abstractmethod
    def GetConstants(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.Constants
        | collections.abc.Awaitable[mt5linux.mt5_pb2.Constants]
    ): ...
    @abc.abstractmethod
    def TerminalInfo(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def AccountInfo(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def SymbolsTotal(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.IntResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.IntResponse]
    ): ...
    @abc.abstractmethod
    def SymbolsGet(
        self,
        request: mt5linux.mt5_pb2.SymbolsRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.SymbolsResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.SymbolsResponse]
    ): ...
    @abc.abstractmethod
    def SymbolInfo(
        self,
        request: mt5linux.mt5_pb2.SymbolRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def SymbolInfoTick(
        self,
        request: mt5linux.mt5_pb2.SymbolRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def SymbolSelect(
        self,
        request: mt5linux.mt5_pb2.SymbolSelectRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.BoolResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.BoolResponse]
    ): ...
    @abc.abstractmethod
    def CopyRatesFrom(
        self,
        request: mt5linux.mt5_pb2.CopyRatesRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.NumpyArray
        | collections.abc.Awaitable[mt5linux.mt5_pb2.NumpyArray]
    ): ...
    @abc.abstractmethod
    def CopyRatesFromPos(
        self,
        request: mt5linux.mt5_pb2.CopyRatesPosRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.NumpyArray
        | collections.abc.Awaitable[mt5linux.mt5_pb2.NumpyArray]
    ): ...
    @abc.abstractmethod
    def CopyRatesRange(
        self,
        request: mt5linux.mt5_pb2.CopyRatesRangeRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.NumpyArray
        | collections.abc.Awaitable[mt5linux.mt5_pb2.NumpyArray]
    ): ...
    @abc.abstractmethod
    def CopyTicksFrom(
        self,
        request: mt5linux.mt5_pb2.CopyTicksRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.NumpyArray
        | collections.abc.Awaitable[mt5linux.mt5_pb2.NumpyArray]
    ): ...
    @abc.abstractmethod
    def CopyTicksRange(
        self,
        request: mt5linux.mt5_pb2.CopyTicksRangeRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.NumpyArray
        | collections.abc.Awaitable[mt5linux.mt5_pb2.NumpyArray]
    ): ...
    @abc.abstractmethod
    def OrderCalcMargin(
        self,
        request: mt5linux.mt5_pb2.MarginRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.FloatResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.FloatResponse]
    ): ...
    @abc.abstractmethod
    def OrderCalcProfit(
        self,
        request: mt5linux.mt5_pb2.ProfitRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.FloatResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.FloatResponse]
    ): ...
    @abc.abstractmethod
    def OrderCheck(
        self,
        request: mt5linux.mt5_pb2.OrderRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def OrderSend(
        self,
        request: mt5linux.mt5_pb2.OrderRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictData
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictData]
    ): ...
    @abc.abstractmethod
    def PositionsTotal(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.IntResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.IntResponse]
    ): ...
    @abc.abstractmethod
    def PositionsGet(
        self,
        request: mt5linux.mt5_pb2.PositionsRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictList
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictList]
    ): ...
    @abc.abstractmethod
    def OrdersTotal(
        self,
        request: mt5linux.mt5_pb2.Empty,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.IntResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.IntResponse]
    ): ...
    @abc.abstractmethod
    def OrdersGet(
        self,
        request: mt5linux.mt5_pb2.OrdersRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictList
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictList]
    ): ...
    @abc.abstractmethod
    def HistoryOrdersTotal(
        self,
        request: mt5linux.mt5_pb2.HistoryRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.IntResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.IntResponse]
    ): ...
    @abc.abstractmethod
    def HistoryOrdersGet(
        self,
        request: mt5linux.mt5_pb2.HistoryRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictList
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictList]
    ): ...
    @abc.abstractmethod
    def HistoryDealsTotal(
        self,
        request: mt5linux.mt5_pb2.HistoryRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.IntResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.IntResponse]
    ): ...
    @abc.abstractmethod
    def HistoryDealsGet(
        self,
        request: mt5linux.mt5_pb2.HistoryRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictList
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictList]
    ): ...
    @abc.abstractmethod
    def MarketBookAdd(
        self,
        request: mt5linux.mt5_pb2.SymbolRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.BoolResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.BoolResponse]
    ): ...
    @abc.abstractmethod
    def MarketBookGet(
        self,
        request: mt5linux.mt5_pb2.SymbolRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.DictList
        | collections.abc.Awaitable[mt5linux.mt5_pb2.DictList]
    ): ...
    @abc.abstractmethod
    def MarketBookRelease(
        self,
        request: mt5linux.mt5_pb2.SymbolRequest,
        context: _ServicerContext,
    ) -> (
        mt5linux.mt5_pb2.BoolResponse
        | collections.abc.Awaitable[mt5linux.mt5_pb2.BoolResponse]
    ): ...

def add_MT5ServiceServicer_to_server(
    servicer: MT5ServiceServicer,
    server: grpc.Server | grpc.aio.Server,
) -> None: ...
