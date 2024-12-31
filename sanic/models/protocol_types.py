from __future__ import annotations

from asyncio import BaseTransport
from typing import TYPE_CHECKING, Optional, Union


if TYPE_CHECKING:
    from sanic.http.constants import HTTP
    from sanic.models.asgi import ASGIScope


# Protocol is a 3.8+ feature
from typing import Protocol


class HTMLProtocol(Protocol):
    def __html__(self) -> Union[str, bytes]: ...

    def _repr_html_(self) -> Union[str, bytes]: ...


class Range(Protocol):
    start: Optional[int]
    end: Optional[int]
    size: Optional[int]
    total: Optional[int]
    __slots__ = ()


class TransportProtocol(BaseTransport):
    scope: ASGIScope
    version: HTTP
    __slots__ = ()
