from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from sanic.http.constants import Stage


if TYPE_CHECKING:
    from sanic.response import BaseHTTPResponse


class Stream:
    stage: Stage
    response: Optional[BaseHTTPResponse]
    __touchup__: Tuple[str, ...] = tuple()
    __slots__ = ()

    def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        raise NotImplementedError("Not implemented")
