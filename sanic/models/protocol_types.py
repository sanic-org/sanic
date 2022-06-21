import sys

from asyncio import BaseTransport
from typing import Any, AnyStr, TypeVar, Union

from sanic.models.asgi import ASGIScope


if sys.version_info < (3, 8):

    # from sanic.models.asgi import MockTransport
    MockTransport = TypeVar("MockTransport")

    TransportProtocol = Union[MockTransport, BaseTransport]
    Range = Any
    HTMLProtocol = Any
else:
    # Protocol is a 3.8+ feature
    from typing import Protocol

    class TransportProtocol(BaseTransport):
        scope: ASGIScope
        __slots__ = ()

    class HTMLProtocol(Protocol):
        def __html__(self) -> AnyStr:
            ...

        def _repr_html_(self) -> AnyStr:
            ...

    class Range(Protocol):
        def start(self) -> int:
            ...

        def end(self) -> int:
            ...

        def size(self) -> int:
            ...

        def total(self) -> int:
            ...
