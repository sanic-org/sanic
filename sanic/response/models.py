from __future__ import annotations

from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Callable,
    Coroutine,
    Dict,
    Iterator,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from django.shortcuts import HttpResponse

from sanic.compat import Header
from sanic.cookies import CookieJar
from sanic.exceptions import SanicException, ServerError
from sanic.helpers import (
    has_message_body,
    remove_entity_headers,
)
from sanic.http import Http


if TYPE_CHECKING:
    from sanic.asgi import ASGIApp
    from sanic.http.http3 import HTTPReceiver
    from sanic.request import Request
else:
    Request = TypeVar("Request")


try:
    from ujson import dumps as json_dumps
except ImportError:
    # This is done in order to ensure that the JSON response is
    # kept consistent across both ujson and inbuilt json usage.
    from json import dumps

    json_dumps = partial(dumps, separators=(",", ":"))


class BaseHTTPResponse:
    """
    The base class for all HTTP Responses
    """

    __slots__ = (
        "asgi",
        "body",
        "content_type",
        "stream",
        "status",
        "headers",
        "_cookies",
    )

    _dumps = json_dumps

    def __init__(self):
        self.asgi: bool = False
        self.body: Optional[bytes] = None
        self.content_type: Optional[str] = None
        self.stream: Optional[Union[Http, ASGIApp, HTTPReceiver]] = None
        self.status: int = None
        self.headers = Header({})
        self._cookies: Optional[CookieJar] = None

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"<{class_name}: {self.status} {self.content_type}>"

    def _encode_body(self, data: Optional[AnyStr]):
        if data is None:
            return b""
        return (
            data.encode() if hasattr(data, "encode") else data  # type: ignore
        )

    @property
    def cookies(self) -> CookieJar:
        """
        The response cookies. Cookies should be set and written as follows:

        .. code-block:: python

                response.cookies["test"] = "It worked!"
                response.cookies["test"]["domain"] = ".yummy-yummy-cookie.com"
                response.cookies["test"]["httponly"] = True

        `See user guide re: cookies
        <https://sanicframework.org/guide/basics/cookies.html>`__

        :return: the cookie jar
        :rtype: CookieJar
        """
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies

    @property
    def processed_headers(self) -> Iterator[Tuple[bytes, bytes]]:
        """
        Obtain a list of header tuples encoded in bytes for sending.

        Add and remove headers based on status and content_type.

        :return: response headers
        :rtype: Tuple[Tuple[bytes, bytes], ...]
        """
        # TODO: Make a blacklist set of header names and then filter with that
        if self.status in (304, 412):  # Not Modified, Precondition Failed
            self.headers = remove_entity_headers(self.headers)
        if has_message_body(self.status):
            self.headers.setdefault("content-type", self.content_type)
        # Encode headers into bytes
        return (
            (name.encode("ascii"), f"{value}".encode(errors="surrogateescape"))
            for name, value in self.headers.items()
        )

    async def send(
        self,
        data: Optional[AnyStr] = None,
        end_stream: Optional[bool] = None,
    ) -> None:
        """
        Send any pending response headers and the given data as body.

        :param data: str or bytes to be written
        :param end_stream: whether to close the stream after this block
        """
        if data is None and end_stream is None:
            end_stream = True
        if self.stream is None:
            raise SanicException(
                "No stream is connected to the response object instance."
            )
        if self.stream.send is None:
            if end_stream and not data:
                return
            raise ServerError(
                "Response stream was ended, no more response data is "
                "allowed to be sent."
            )
        data = (
            data.encode()  # type: ignore
            if hasattr(data, "encode")
            else data or b""
        )
        await self.stream.send(
            data,  # type: ignore
            end_stream=end_stream or False,
        )


class HTTPResponse(BaseHTTPResponse):
    """
    HTTP response to be sent back to the client.

    :param body: the body content to be returned
    :type body: Optional[bytes]
    :param status: HTTP response number. **Default=200**
    :type status: int
    :param headers: headers to be returned
    :type headers: Optional;
    :param content_type: content type to be returned (as a header)
    :type content_type: Optional[str]
    """

    __slots__ = ()

    def __init__(
        self,
        body: Optional[AnyStr] = None,
        status: int = 200,
        headers: Optional[Union[Header, Dict[str, str]]] = None,
        content_type: Optional[str] = None,
    ):
        super().__init__()

        self.content_type: Optional[str] = content_type
        self.body = self._encode_body(body)
        self.status = status
        self.headers = Header(headers or {})
        self._cookies = None

    async def eof(self):
        await self.send("", True)

    async def __aenter__(self):
        return self.send

    async def __aexit__(self, *_):
        await self.eof()


class ResponseStream:
    """
    ResponseStream is a compat layer to bridge the gap after the deprecation
    of StreamingHTTPResponse. It will be removed when:
    - file_stream is moved to new style streaming
    - file and file_stream are combined into a single API
    """

    __slots__ = (
        "_cookies",
        "content_type",
        "headers",
        "request",
        "response",
        "status",
        "streaming_fn",
    )

    def __init__(
        self,
        streaming_fn: Callable[
            [Union[BaseHTTPResponse, ResponseStream]],
            Coroutine[Any, Any, None],
        ],
        status: int = 200,
        headers: Optional[Union[Header, Dict[str, str]]] = None,
        content_type: Optional[str] = None,
    ):
        self.streaming_fn = streaming_fn
        self.status = status
        self.headers = headers or Header()
        self.content_type = content_type
        self.request: Optional[Request] = None
        self._cookies: Optional[CookieJar] = None

    async def write(self, message: str):
        await self.response.send(message)

    async def stream(self) -> HTTPResponse:
        if not self.request:
            raise ServerError("Attempted response to unknown request")
        self.response = await self.request.respond(
            headers=self.headers,
            status=self.status,
            content_type=self.content_type,
        )
        await self.streaming_fn(self)
        return self.response

    async def eof(self) -> None:
        await self.response.eof()

    @property
    def cookies(self) -> CookieJar:
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies

    @property
    def processed_headers(self):
        return self.response.processed_headers

    @property
    def body(self):
        return self.response.body

    def __call__(self, request: Request) -> ResponseStream:
        self.request = request
        return self

    def __await__(self):
        return self.stream().__await__()
