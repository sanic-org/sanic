from __future__ import annotations

import sys

from asyncio import BaseTransport
from typing import TYPE_CHECKING, Any, Optional, Union


if TYPE_CHECKING:
    from sanic.http.constants import HTTP
    from sanic.models.asgi import ASGIScope


if sys.version_info < (3, 8):
    Range = Any
    HTMLProtocol = Any
else:
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
