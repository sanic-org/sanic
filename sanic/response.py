from functools import partial
from mimetypes import guess_type
from os import path
from urllib.parse import quote_plus
from warnings import warn

from sanic.compat import Header, open_async
from sanic.cookies import CookieJar
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

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies

    @property
    def processed_headers(self):
        """Obtain a list of header tuples encoded in bytes for sending.

        Add and remove headers based on status and content_type.
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

    async def send(self, data=None, end_stream=None):
        """Send any pending response headers and the given data as body.
        :param data: str or bytes to be written
        :end_stream: whether to close the stream after this block
        """
        if data is None and end_stream is None:
            end_stream = True
        if end_stream and not data and self.stream.send is None:
            return
        data = data.encode() if hasattr(data, "encode") else data or b""
        await self.stream.send(data, end_stream=end_stream)


class StreamingHTTPResponse(BaseHTTPResponse):
    """Old style streaming response. Use `request.respond()` instead of this in
    new code to avoid the callback."""

    __slots__ = (
        "streaming_fn",
        "status",
        "content_type",
        "headers",
        "_cookies",
    )

    def __init__(
        self,
        streaming_fn,
        status=200,
        headers=None,
        content_type="text/plain; charset=utf-8",
        chunked="deprecated",
    ):
        if chunked != "deprecated":
            warn(
                "The chunked argument has been deprecated and will be "
                "removed in v21.6"
            )

        super().__init__()

        self.content_type = content_type
        self.streaming_fn = streaming_fn
        self.status = status
        self.headers = Header(headers or {})
        self._cookies = None

    async def write(self, data):
        """Writes a chunk of data to the streaming response.

        :param data: str or bytes-ish data to be written.
        """
        await super().send(self._encode_body(data))

    async def send(self, *args, **kwargs):
        if self.streaming_fn is not None:
            await self.streaming_fn(self)
            self.streaming_fn = None
        await super().send(*args, **kwargs)


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
    chunked="deprecated",
    _range=None,
):
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param chunked: Deprecated
    :param _range:
    """
    if chunked != "deprecated":
        warn(
            "The chunked argument has been deprecated and will be "
            "removed in v21.6"
        )

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
    )


def stream(
    streaming_fn,
    status=200,
    headers=None,
    content_type="text/plain; charset=utf-8",
    chunked="deprecated",
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
    :param chunked: Deprecated
    """
    if chunked != "deprecated":
        warn(
            "The chunked argument has been deprecated and will be "
            "removed in v21.6"
        )

    return StreamingHTTPResponse(
        streaming_fn,
        headers=headers,
        content_type=content_type,
        status=status,
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
