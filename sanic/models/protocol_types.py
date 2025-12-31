from __future__ import annotations

from asyncio import BaseTransport
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from sanic.http.constants import HTTP
    from sanic.models.asgi import ASGIScope


class HTMLProtocol(Protocol):
    def __html__(self) -> str | bytes: ...

    def _repr_html_(self) -> str | bytes: ...


class Range(Protocol):
    start: int | None
    end: int | None
    size: int | None
    total: int | None
    __slots__ = ()


class TransportProtocol(BaseTransport):
    scope: ASGIScope
    version: HTTP
    __slots__ = ()
