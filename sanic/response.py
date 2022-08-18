from __future__ import annotations

from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from functools import partial
from mimetypes import guess_type
from os import path
from pathlib import PurePath
from time import time
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
from urllib.parse import quote_plus

from sanic.compat import Header, open_async, stat_async
from sanic.constants import DEFAULT_HTTP_CONTENT_TYPE
from sanic.cookies import CookieJar
from sanic.exceptions import SanicException, ServerError
from sanic.helpers import (
    Default,
    _default,
    has_message_body,
    remove_entity_headers,
)
from sanic.http import Http
from sanic.log import logger
from sanic.models.protocol_types import HTMLProtocol, Range


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


def empty(
    status: int = 204, headers: Optional[Dict[str, str]] = None
) -> HTTPResponse:
    """
    Returns an empty response to the client.

    :param status Response code.
    :param headers Custom Headers.
    """
    return HTTPResponse(body=b"", status=status, headers=headers)


def json(
    body: Any,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "application/json",
    dumps: Optional[Callable[..., str]] = None,
    **kwargs: Any,
) -> HTTPResponse:
    """
    Returns response object with body in json format.

    :param body: Response data to be serialized.
    :param status: Response code.
    :param headers: Custom Headers.
    :param kwargs: Remaining arguments that are passed to the json encoder.
    """
    if not dumps:
        dumps = BaseHTTPResponse._dumps
    return HTTPResponse(
        dumps(body, **kwargs),
        headers=headers,
        status=status,
        content_type=content_type,
    )


def text(
    body: str,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "text/plain; charset=utf-8",
) -> HTTPResponse:
    """
    Returns response object with body in text format.

    :param body: Response data to be encoded.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response
    """
    if not isinstance(body, str):
        raise TypeError(
            f"Bad body type. Expected str, got {type(body).__name__})"
        )

    return HTTPResponse(
        body, status=status, headers=headers, content_type=content_type
    )


def raw(
    body: Optional[AnyStr],
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = DEFAULT_HTTP_CONTENT_TYPE,
) -> HTTPResponse:
    """
    Returns response object without encoding the body.

    :param body: Response data.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response.
    """
    return HTTPResponse(
        body=body,
        status=status,
        headers=headers,
        content_type=content_type,
    )


def html(
    body: Union[str, bytes, HTMLProtocol],
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPResponse:
    """
    Returns response object with body in html format.

    :param body: str or bytes-ish, or an object with __html__ or _repr_html_.
    :param status: Response code.
    :param headers: Custom Headers.
    """
    if not isinstance(body, (str, bytes)):
        if hasattr(body, "__html__"):
            body = body.__html__()
        elif hasattr(body, "_repr_html_"):
            body = body._repr_html_()

    return HTTPResponse(  # type: ignore
        body,
        status=status,
        headers=headers,
        content_type="text/html; charset=utf-8",
    )


async def validate_file(
    request_headers: Header, last_modified: Union[datetime, float, int]
):
    try:
        if_modified_since = request_headers.getone("If-Modified-Since")
    except KeyError:
        return
    try:
        if_modified_since = parsedate_to_datetime(if_modified_since)
    except (TypeError, ValueError):
        logger.warning(
            "Ignorning invalid If-Modified-Since header received: " "'%s'",
            if_modified_since,
        )
        return
    if not isinstance(last_modified, datetime):
        last_modified = datetime.fromtimestamp(
            float(last_modified), tz=timezone.utc
        ).replace(microsecond=0)
    if last_modified <= if_modified_since:
        return HTTPResponse(status=304)


async def file(
    location: Union[str, PurePath],
    status: int = 200,
    request_headers: Optional[Header] = None,
    validate_when_requested: bool = True,
    mime_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    last_modified: Optional[Union[datetime, float, int, Default]] = _default,
    max_age: Optional[Union[float, int]] = None,
    no_store: Optional[bool] = None,
    _range: Optional[Range] = None,
) -> HTTPResponse:
    """Return a response object with file data.
    :param status: HTTP response code. Won't enforce the passed in
        status if only a part of the content will be sent (206)
        or file is being validated (304).
    :param request_headers: The request headers.
    :param validate_when_requested: If True, will validate the
        file when requested.
    :param location: Location of file on system.
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param last_modified: The last modified date and time of the file.
    :param max_age: Max age for cache control.
    :param no_store: Any cache should not store this response.
    :param _range:
    """

    if isinstance(last_modified, datetime):
        last_modified = last_modified.replace(microsecond=0).timestamp()
    elif isinstance(last_modified, Default):
        stat = await stat_async(location)
        last_modified = stat.st_mtime

    if (
        validate_when_requested
        and request_headers is not None
        and last_modified
    ):
        response = await validate_file(request_headers, last_modified)
        if response:
            return response

    headers = headers or {}
    if last_modified:
        headers.setdefault(
            "Last-Modified", formatdate(last_modified, usegmt=True)
        )

    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )

    if no_store:
        cache_control = "no-store"
    elif max_age:
        cache_control = f"public, max-age={max_age}"
        headers.setdefault(
            "expires",
            formatdate(
                time() + max_age,
                usegmt=True,
            ),
        )
    else:
        cache_control = "no-cache"

    headers.setdefault("cache-control", cache_control)

    filename = filename or path.split(location)[-1]

    async with await open_async(location, mode="rb") as f:
        if _range:
            await f.seek(_range.start)
            out_stream = await f.read(_range.size)
            headers[
                "Content-Range"
            ] = f"bytes {_range.start}-{_range.end}/{_range.total}"
            status = 206
        else:
            out_stream = await f.read()

    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    return HTTPResponse(
        body=out_stream,
        status=status,
        headers=headers,
        content_type=mime_type,
    )


def redirect(
    to: str,
    headers: Optional[Dict[str, str]] = None,
    status: int = 302,
    content_type: str = "text/html; charset=utf-8",
) -> HTTPResponse:
    """
    Abort execution and cause a 302 redirect (by default) by setting a
    Location header.

    :param to: path or fully qualified URL to redirect to
    :param headers: optional dict of headers to include in the new request
    :param status: status code (int) of the new request, defaults to 302
    :param content_type: the content type (string) of the response
    """
    headers = headers or {}

    # URL Quote the URL before redirecting
    safe_to = quote_plus(to, safe=":/%#?&=@[]!$&'()*+,;")

    # According to RFC 7231, a relative URI is now permitted.
    headers["Location"] = safe_to

    return HTTPResponse(
        status=status, headers=headers, content_type=content_type
    )


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


async def file_stream(
    location: Union[str, PurePath],
    status: int = 200,
    chunk_size: int = 4096,
    mime_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    _range: Optional[Range] = None,
) -> ResponseStream:
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param _range:
    """
    headers = headers or {}
    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
    filename = filename or path.split(location)[-1]
    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    if _range:
        start = _range.start
        end = _range.end
        total = _range.total

        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        status = 206

    async def _streaming_fn(response):
        async with await open_async(location, mode="rb") as f:
            if _range:
                await f.seek(_range.start)
                to_send = _range.size
                while to_send > 0:
                    content = await f.read(min((_range.size, chunk_size)))
                    if len(content) < 1:
                        break
                    to_send -= len(content)
                    await response.write(content)
            else:
                while True:
                    content = await f.read(chunk_size)
                    if len(content) < 1:
                        break
                    await response.write(content)

    return ResponseStream(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=mime_type,
    )
