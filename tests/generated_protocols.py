"""Typed runtime boundary for generated mt5linux protobuf modules in tests."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Protocol, cast

import grpc


class EmptyMessage(Protocol):
    """Empty protobuf message."""


class BoolResponseMessage(Protocol):
    result: bool


class IntResponseMessage(Protocol):
    value: int


class ErrorInfoMessage(Protocol):
    code: int
    message: str


class MT5VersionMessage(Protocol):
    major: int
    minor: int
    build: str


class ConstantsMessage(Protocol):
    values: dict[str, int]


class DictDataMessage(Protocol):
    json_data: str


class DictListMessage(Protocol):
    json_items: list[str]


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


class SymbolRequestMessage(Protocol):
    symbol: str


class PositionsRequestMessage(Protocol):
    symbol: str
    group: str
    ticket: int


class OrdersRequestMessage(Protocol):
    symbol: str
    group: str
    ticket: int


class _EmptyFactory(Protocol):
    def __call__(self) -> EmptyMessage: ...


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


class _SymbolRequestFactory(Protocol):
    def __call__(self, symbol: str = "") -> SymbolRequestMessage: ...


class _PositionsRequestFactory(Protocol):
    def __call__(
        self,
        symbol: str = "",
        group: str = "",
        ticket: int = 0,
    ) -> PositionsRequestMessage: ...


class _OrdersRequestFactory(Protocol):
    def __call__(
        self,
        symbol: str = "",
        group: str = "",
        ticket: int = 0,
    ) -> OrdersRequestMessage: ...


class Mt5Pb2Module(Protocol):
    Empty: _EmptyFactory
    InitRequest: _InitRequestFactory
    SymbolRequest: _SymbolRequestFactory
    PositionsRequest: _PositionsRequestFactory
    OrdersRequest: _OrdersRequestFactory


class MT5ServiceStubProtocol(Protocol):
    def HealthCheck(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> HealthStatusMessage: ...
    def GetConstants(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> ConstantsMessage: ...
    def Initialize(
        self, request: InitRequestMessage, timeout: float | None = None
    ) -> BoolResponseMessage: ...
    def Version(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> MT5VersionMessage: ...
    def LastError(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> ErrorInfoMessage: ...
    def SymbolsTotal(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> IntResponseMessage: ...
    def PositionsTotal(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> IntResponseMessage: ...
    def OrdersTotal(
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
    def AccountInfo(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> DictDataMessage: ...
    def TerminalInfo(
        self, request: EmptyMessage, timeout: float | None = None
    ) -> DictDataMessage: ...


class _MT5ServiceStubFactory(Protocol):
    def __call__(self, channel: grpc.Channel) -> MT5ServiceStubProtocol: ...


class Mt5Pb2GrpcModule(Protocol):
    MT5ServiceStub: _MT5ServiceStubFactory


def _load_mt5linux_module(name: str) -> ModuleType:
    return import_module(name)


mt5_pb2 = cast("Mt5Pb2Module", _load_mt5linux_module("mt5linux.mt5_pb2"))
mt5_pb2_grpc = cast(
    "Mt5Pb2GrpcModule",
    _load_mt5linux_module("mt5linux.mt5_pb2_grpc"),
)
