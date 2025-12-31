from __future__ import annotations

from typing import TYPE_CHECKING

from sanic.http.constants import Stage


if TYPE_CHECKING:
    from sanic.response import BaseHTTPResponse
    from sanic.server.protocols.http_protocol import HttpProtocol


class Stream:
    stage: Stage
    response: BaseHTTPResponse | None
    protocol: HttpProtocol
    url: str | None
    request_body: bytes | None
    request_max_size: int | float

    __touchup__: tuple[str, ...] = tuple()
    __slots__ = ("request_max_size",)

    def respond(
        self, response: BaseHTTPResponse
    ) -> BaseHTTPResponse:  # no cov
        raise NotImplementedError("Not implemented")
