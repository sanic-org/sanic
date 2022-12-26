from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from sanic.http.constants import Stage


if TYPE_CHECKING:
    from sanic.response import BaseHTTPResponse
    from sanic.server.protocols.http_protocol import HttpProtocol


class Stream:
    stage: Stage
    response: Optional[BaseHTTPResponse]
    protocol: HttpProtocol
    url: Optional[str]
    request_body: Optional[bytes]
    request_max_size: Union[int, float]

    __touchup__: Tuple[str, ...] = tuple()
    __slots__ = ("request_max_size",)

    def respond(
        self, response: BaseHTTPResponse
    ) -> BaseHTTPResponse:  # no cov
        raise NotImplementedError("Not implemented")
