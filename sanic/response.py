from functools import partial
from mimetypes import guess_type
from os import path
from urllib.parse import quote_plus

from sanic.compat import Header, open_async
from sanic.cookies import CookieJar
from sanic.headers import format_http1, format_http1_response
from sanic.helpers import has_message_body, remove_entity_headers


try:
    from ujson import dumps as json_dumps
except ImportError:
    # This is done in order to ensure that the JSON response is
    # kept consistent across both ujson and inbuilt json usage.
    from json import dumps

    json_dumps = partial(dumps, separators=(",", ":"))


class BaseHTTPResponse:
    def __init__(self):
        self.asgi = False

    def _encode_body(self, data):
        if data is None:
            return b""
        return data.encode() if hasattr(data, "encode") else data

    def _parse_headers(self):
        return format_http1(self.headers.items())

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies

    def get_headers(
        self,
        version="1.1",
        keep_alive=False,
        keep_alive_timeout=None,
        body=b"",
    ):
        """.. deprecated:: 20.3:
        This function is not public API and will be removed in 21.3."""

        # self.headers get priority over content_type
        if self.content_type and "Content-Type" not in self.headers:
            self.headers["Content-Type"] = self.content_type

        if keep_alive:
            self.headers["Connection"] = "keep-alive"
            if keep_alive_timeout is not None:
                self.headers["Keep-Alive"] = keep_alive_timeout
        else:
            self.headers["Connection"] = "close"

        if self.status in (304, 412):
            self.headers = remove_entity_headers(self.headers)

        return format_http1_response(self.status, self.headers.items(), body)


class StreamingHTTPResponse(BaseHTTPResponse):
    __slots__ = (
        "protocol",
        "streaming_fn",
        "status",
        "content_type",
        "headers",
        "chunked",
        "_cookies",
    )

    def __init__(
        self,
        streaming_fn,
        status=200,
        headers=None,
        content_type="text/plain; charset=utf-8",
        chunked=True,
    ):
        super().__init__()

        self.content_type = content_type
        self.streaming_fn = streaming_fn
        self.status = status
        self.headers = Header(headers or {})
        self.chunked = chunked
        self._cookies = None
        self.protocol = None

    async def write(self, data):
        """Writes a chunk of data to the streaming response.

        :param data: str or bytes-ish data to be written.
        """
        data = self._encode_body(data)

        # `chunked` will always be False in ASGI-mode, even if the underlying
        # ASGI Transport implements Chunked transport. That does it itself.
        if self.chunked:
            await self.protocol.push_data(b"%x\r\n%b\r\n" % (len(data), data))
        else:
            await self.protocol.push_data(data)
        await self.protocol.drain()

    async def stream(
        self, version="1.1", keep_alive=False, keep_alive_timeout=None
    ):
        """Streams headers, runs the `streaming_fn` callback that writes
        content to the response body, then finalizes the response body.
        """
        if version != "1.1":
            self.chunked = False
        if not getattr(self, "asgi", False):
            headers = self.get_headers(
                version,
                keep_alive=keep_alive,
                keep_alive_timeout=keep_alive_timeout,
            )
            await self.protocol.push_data(headers)
            await self.protocol.drain()
        await self.streaming_fn(self)
        if self.chunked:
            await self.protocol.push_data(b"0\r\n\r\n")
        # no need to await drain here after this write, because it is the
        # very last thing we write and nothing needs to wait for it.

    def get_headers(
        self, version="1.1", keep_alive=False, keep_alive_timeout=None
    ):
        if self.chunked and version == "1.1":
            self.headers["Transfer-Encoding"] = "chunked"
            self.headers.pop("Content-Length", None)

        return super().get_headers(version, keep_alive, keep_alive_timeout)


class HTTPResponse(BaseHTTPResponse):
    __slots__ = ("body", "status", "content_type", "headers", "_cookies")

    def __init__(
        self,
        body=None,
        status=200,
        headers=None,
        content_type=None,
    ):
        super().__init__()

        self.content_type = content_type
        self.body = self._encode_body(body)
        self.status = status
        self.headers = Header(headers or {})
        self._cookies = None

    def output(self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        body = b""
        if has_message_body(self.status):
            body = self.body
            self.headers["Content-Length"] = self.headers.get(
                "Content-Length", len(self.body)
            )

        return self.get_headers(version, keep_alive, keep_alive_timeout, body)

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies


def empty(status=204, headers=None):
    """
    Returns an empty response to the client.

    :param status Response code.
    :param headers Custom Headers.
    """
    return HTTPResponse(body=b"", status=status, headers=headers)


def json(
    body,
    status=200,
    headers=None,
    content_type="application/json",
    dumps=json_dumps,
    **kwargs,
):
    """
    Returns response object with body in json format.

    :param body: Response data to be serialized.
    :param status: Response code.
    :param headers: Custom Headers.
    :param kwargs: Remaining arguments that are passed to the json encoder.
    """
    return HTTPResponse(
        dumps(body, **kwargs),
        headers=headers,
        status=status,
        content_type=content_type,
    )


def text(
    body, status=200, headers=None, content_type="text/plain; charset=utf-8"
):
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
    body, status=200, headers=None, content_type="application/octet-stream"
):
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


def html(body, status=200, headers=None):
    """
    Returns response object with body in html format.

    :param body: str or bytes-ish, or an object with __html__ or _repr_html_.
    :param status: Response code.
    :param headers: Custom Headers.
    """
    if hasattr(body, "__html__"):
        body = body.__html__()
    elif hasattr(body, "_repr_html_"):
        body = body._repr_html_()
    return HTTPResponse(
        body,
        status=status,
        headers=headers,
        content_type="text/html; charset=utf-8",
    )


async def file(
    location,
    status=200,
    mime_type=None,
    headers=None,
    filename=None,
    _range=None,
):
    """Return a response object with file data.

    :param location: Location of file on system.
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


async def file_stream(
    location,
    status=200,
    chunk_size=4096,
    mime_type=None,
    headers=None,
    filename=None,
    chunked=True,
    _range=None,
):
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param chunked: Enable or disable chunked transfer-encoding
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

    return StreamingHTTPResponse(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=mime_type,
        chunked=chunked,
    )


def stream(
    streaming_fn,
    status=200,
    headers=None,
    content_type="text/plain; charset=utf-8",
    chunked=True,
):
    """Accepts an coroutine `streaming_fn` which can be used to
    write chunks to a streaming response. Returns a `StreamingHTTPResponse`.

    Example usage::

        @app.route("/")
        async def index(request):
            async def streaming_fn(response):
                await response.write('foo')
                await response.write('bar')

            return stream(streaming_fn, content_type='text/plain')

    :param streaming_fn: A coroutine accepts a response and
        writes content to that response.
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param chunked: Enable or disable chunked transfer-encoding
    """
    return StreamingHTTPResponse(
        streaming_fn,
        headers=headers,
        content_type=content_type,
        status=status,
        chunked=chunked,
    )


def redirect(
    to, headers=None, status=302, content_type="text/html; charset=utf-8"
):
    """Abort execution and cause a 302 redirect (by default).

    :param to: path or fully qualified URL to redirect to
    :param headers: optional dict of headers to include in the new request
    :param status: status code (int) of the new request, defaults to 302
    :param content_type: the content type (string) of the response
    :returns: the redirecting Response
    """
    headers = headers or {}

    # URL Quote the URL before redirecting
    safe_to = quote_plus(to, safe=":/%#?&=@[]!$&'()*+,;")

    # According to RFC 7231, a relative URI is now permitted.
    headers["Location"] = safe_to

    return HTTPResponse(
        status=status, headers=headers, content_type=content_type
    )
