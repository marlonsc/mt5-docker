"""Type stubs for pytest."""

from collections.abc import Callable
from typing import Any, Literal, TypeVar, overload

_F = TypeVar("_F", bound=Callable[..., Any])

class MarkDecorator:
    def __call__(self, func: _F) -> _F: ...

class MarkGenerator:
    def usefixtures(self, *names: str) -> MarkDecorator: ...
    def slow(self) -> MarkDecorator: ...
    def requires_container(self) -> MarkDecorator: ...
    def __getattr__(self, name: str) -> MarkDecorator: ...

mark: MarkGenerator

# Overloads to support both @fixture and @fixture(scope=...)
@overload
def fixture(func: _F) -> _F: ...
@overload
def fixture(
    scope: Literal["function", "class", "module", "package", "session"] = ...,
    autouse: bool = ...,
    name: str | None = ...,
) -> Callable[[_F], _F]: ...

def skip(reason: str = ...) -> None: ...
