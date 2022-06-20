from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from sanic.compat import Header
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

    __version__ = "unknown"
    __touchup__: Tuple[str, ...] = tuple()
    __slots__ = ()

    def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        raise NotImplementedError("Not implemented")

    def create_empty_request(self) -> None:
        """
        Current error handling code needs a request object that won't exist
        if an error occurred during before a request was received. Create a
        bogus response for error handling use.
        """

        # FIXME: Avoid this by refactoring error handling and response code
        self.request = self.protocol.request_class(
            url_bytes=self.url.encode() if self.url else b"*",
            headers=Header({}),
            version=self.__class__.__version__,
            method="NONE",
            transport=self.protocol.transport,
            app=self.protocol.app,
        )
        self.request.stream = self
