from functools import partial
from mimetypes import guess_type
from os import path
from urllib.parse import quote_plus

from aiofiles import open as open_async
from multidict import CIMultiDict

from sanic.cookies import CookieJar
from sanic.helpers import STATUS_CODES, has_message_body, remove_entity_headers


try:
    from ujson import dumps as json_dumps
except BaseException:
    from json import dumps

    # This is done in order to ensure that the JSON response is
    # kept consistent across both ujson and inbuilt json usage.
    json_dumps = partial(dumps, separators=(",", ":"))


class BaseHTTPResponse:
    def _encode_body(self, data):
        try:
            # Try to encode it regularly
            return data.encode()
        except AttributeError:
            # Convert it to a str if you can't
            return str(data).encode()

    def _parse_headers(self):
        headers = b""
        for name, value in self.headers.items():
            try:
                headers += b"%b: %b\r\n" % (
                    name.encode(),
                    value.encode("utf-8"),
                )
            except AttributeError:
                headers += b"%b: %b\r\n" % (
                    str(name).encode(),
                    str(value).encode("utf-8"),
                )

        return headers

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies


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
        content_type="text/plain",
        chunked=True,
    ):
        self.content_type = content_type
        self.streaming_fn = streaming_fn
        self.status = status
        self.headers = CIMultiDict(headers or {})
        self.chunked = chunked
        self._cookies = None

    async def write(self, data):
        """Writes a chunk of data to the streaming response.

        :param data: bytes-ish data to be written.
        """
        if type(data) != bytes:
            data = self._encode_body(data)

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
        # This is all returned in a kind-of funky way
        # We tried to make this as fast as possible in pure python
        timeout_header = b""
        if keep_alive and keep_alive_timeout is not None:
            timeout_header = b"Keep-Alive: %d\r\n" % keep_alive_timeout

        if self.chunked and version == "1.1":
            self.headers["Transfer-Encoding"] = "chunked"
            self.headers.pop("Content-Length", None)
        self.headers["Content-Type"] = self.headers.get(
            "Content-Type", self.content_type
        )

        headers = self._parse_headers()

        if self.status == 200:
            status = b"OK"
        else:
            status = STATUS_CODES.get(self.status)

        return (b"HTTP/%b %d %b\r\n" b"%b" b"%b\r\n") % (
            version.encode(),
            self.status,
            status,
            timeout_header,
            headers,
        )


class HTTPResponse(BaseHTTPResponse):
    __slots__ = ("body", "status", "content_type", "headers", "_cookies")

    def __init__(
        self,
        body=None,
        status=200,
        headers=None,
        content_type="text/plain",
        body_bytes=b"",
    ):
        self.content_type = content_type

        if body is not None:
            self.body = self._encode_body(body)
        else:
            self.body = body_bytes

        self.status = status
        self.headers = CIMultiDict(headers or {})
        self._cookies = None

    def output(self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        # This is all returned in a kind-of funky way
        # We tried to make this as fast as possible in pure python
        timeout_header = b""
        if keep_alive and keep_alive_timeout is not None:
            timeout_header = b"Keep-Alive: %d\r\n" % keep_alive_timeout

        body = b""
        if has_message_body(self.status):
            body = self.body
            self.headers["Content-Length"] = self.headers.get(
                "Content-Length", len(self.body)
            )

        self.headers["Content-Type"] = self.headers.get(
            "Content-Type", self.content_type
        )

        if self.status in (304, 412):
            self.headers = remove_entity_headers(self.headers)

        headers = self._parse_headers()

        if self.status == 200:
            status = b"OK"
        else:
            status = STATUS_CODES.get(self.status, b"UNKNOWN RESPONSE")

        return (
            b"HTTP/%b %d %b\r\n" b"Connection: %b\r\n" b"%b" b"%b\r\n" b"%b"
        ) % (
            version.encode(),
            self.status,
            status,
            b"keep-alive" if keep_alive else b"close",
            timeout_header,
            headers,
            body,
        )

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies


def json(
    body,
    status=200,
    headers=None,
    content_type="application/json",
    dumps=json_dumps,
    **kwargs
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
        body_bytes=body,
        status=status,
        headers=headers,
        content_type=content_type,
    )


def html(body, status=200, headers=None):
    """
    Returns response object with body in html format.

    :param body: Response data to be encoded.
    :param status: Response code.
    :param headers: Custom Headers.
    """
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
            "Content-Disposition", 'attachment; filename="{}"'.format(filename)
        )
    filename = filename or path.split(location)[-1]

    async with open_async(location, mode="rb") as _file:
        if _range:
            await _file.seek(_range.start)
            out_stream = await _file.read(_range.size)
            headers["Content-Range"] = "bytes %s-%s/%s" % (
                _range.start,
                _range.end,
                _range.total,
            )
            status = 206
        else:
            out_stream = await _file.read()

    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    return HTTPResponse(
        status=status,
        headers=headers,
        content_type=mime_type,
        body_bytes=out_stream,
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
            "Content-Disposition", 'attachment; filename="{}"'.format(filename)
        )
    filename = filename or path.split(location)[-1]

    _file = await open_async(location, mode="rb")

    async def _streaming_fn(response):
        nonlocal _file, chunk_size
        try:
            if _range:
                chunk_size = min((_range.size, chunk_size))
                await _file.seek(_range.start)
                to_send = _range.size
                while to_send > 0:
                    content = await _file.read(chunk_size)
                    if len(content) < 1:
                        break
                    to_send -= len(content)
                    await response.write(content)
            else:
                while True:
                    content = await _file.read(chunk_size)
                    if len(content) < 1:
                        break
                    await response.write(content)
        finally:
            await _file.close()
        return  # Returning from this fn closes the stream

    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    if _range:
        headers["Content-Range"] = "bytes %s-%s/%s" % (
            _range.start,
            _range.end,
            _range.total,
        )
        status = 206
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
