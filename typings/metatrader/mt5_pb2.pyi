"""Minimal manual stubs for the generated metatrader.mt5_pb2 module.

These types are generated at runtime by protobuf; listing every field would
be fragile and auto-generated stubs are forbidden by project policy. The
classes below inherit from google.protobuf.message.Message so type checkers
can resolve the symbols used in bridge.py and tests without losing the fact
that they are protocol-buffer messages.
"""

from __future__ import annotations

from typing import Any

from google.protobuf.message import Message

class Empty(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class BoolResponse(Message):
    result: bool
    def __init__(self, result: bool = False, **kwargs: Any) -> None: ...

class IntResponse(Message):
    result: int
    def __init__(self, result: int = 0, **kwargs: Any) -> None: ...

class FloatResponse(Message):
    result: float
    def __init__(self, result: float = 0.0, **kwargs: Any) -> None: ...

class HealthStatus(Message):
    healthy: bool
    def __init__(self, healthy: bool = False, **kwargs: Any) -> None: ...

class NumpyArray(Message):
    data: bytes
    dtype: str
    shape: list[int]
    def __init__(self, **kwargs: Any) -> None: ...

class DictData(Message):
    def __init__(self, **kwargs: Any) -> None: ...
    def __getitem__(self, key: str) -> Any: ...

class DictList(Message):
    data: list[DictData]
    def __init__(self, **kwargs: Any) -> None: ...

class SymbolRequest(Message):
    symbol: str
    def __init__(self, symbol: str = "", **kwargs: Any) -> None: ...

class InitRequest(Message):
    path: str
    def __init__(self, path: str = "", **kwargs: Any) -> None: ...

class HistoryRequest(Message):
    symbol: str
    timeframe: int
    date_from: int
    date_to: int
    def __init__(self, **kwargs: Any) -> None: ...

class SymbolsResponse(Message):
    symbols: list[str]
    def __init__(self, **kwargs: Any) -> None: ...

class ProvisionedAccount(Message):
    login: int
    password: str
    server: str
    def __init__(self, **kwargs: Any) -> None: ...

class MT5Version(Message):
    version: int
    build: int
    def __init__(self, **kwargs: Any) -> None: ...

class LoginRequest(Message):
    login: int
    password: str
    server: str
    def __init__(self, **kwargs: Any) -> None: ...

class CreateDemoRequest(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class CopyRatesRequest(Message):
    symbol: str
    timeframe: int
    date_from: int
    count: int
    def __init__(self, **kwargs: Any) -> None: ...

class CopyRatesRangeRequest(Message):
    symbol: str
    timeframe: int
    date_from: int
    date_to: int
    def __init__(self, **kwargs: Any) -> None: ...

class CopyRatesPosRequest(Message):
    symbol: str
    timeframe: int
    start_pos: int
    count: int
    def __init__(self, **kwargs: Any) -> None: ...

class CopyTicksRequest(Message):
    symbol: str
    flags: int
    count: int
    def __init__(self, **kwargs: Any) -> None: ...

class CopyTicksRangeRequest(Message):
    symbol: str
    flags: int
    date_from: int
    date_to: int
    def __init__(self, **kwargs: Any) -> None: ...

class PositionsRequest(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class OrdersRequest(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class OrderRequest(Message):
    symbol: str
    action: int
    def __init__(self, **kwargs: Any) -> None: ...

class ModelInfo(Message):
    name: str
    def __init__(self, **kwargs: Any) -> None: ...

class ModelsResponse(Message):
    models: list[ModelInfo]
    def __init__(self, **kwargs: Any) -> None: ...

class MethodInfo(Message):
    name: str
    def __init__(self, **kwargs: Any) -> None: ...

class MethodsResponse(Message):
    methods: list[MethodInfo]
    def __init__(self, **kwargs: Any) -> None: ...

class FieldInfo(Message):
    name: str
    type: str
    def __init__(self, **kwargs: Any) -> None: ...

class ParameterInfo(Message):
    name: str
    type: str
    def __init__(self, **kwargs: Any) -> None: ...

class ErrorInfo(Message):
    code: int
    message: str
    def __init__(self, **kwargs: Any) -> None: ...

class Constants(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class SymbolSelectRequest(Message):
    symbols: list[str]
    def __init__(self, **kwargs: Any) -> None: ...

class SymbolsRequest(Message):
    def __init__(self, **kwargs: Any) -> None: ...

class ProfitRequest(Message):
    symbol: str
    volume: float
    price_open: float
    price_close: float
    order_type: int
    def __init__(self, **kwargs: Any) -> None: ...

class MarginRequest(Message):
    symbol: str
    volume: float
    price: float
    order_type: int
    def __init__(self, **kwargs: Any) -> None: ...
