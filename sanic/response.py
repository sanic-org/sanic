from mimetypes import guess_type
from os import path

try:
    from ujson import dumps as json_dumps
except:
    from json import dumps as json_dumps

from aiofiles import open as open_async

from sanic.cookies import CookieJar

COMMON_STATUS_CODES = {
    200: b'OK',
    400: b'Bad Request',
    404: b'Not Found',
    500: b'Internal Server Error',
}
ALL_STATUS_CODES = {
    100: b'Continue',
    101: b'Switching Protocols',
    102: b'Processing',
    200: b'OK',
    201: b'Created',
    202: b'Accepted',
    203: b'Non-Authoritative Information',
    204: b'No Content',
    205: b'Reset Content',
    206: b'Partial Content',
    207: b'Multi-Status',
    208: b'Already Reported',
    226: b'IM Used',
    300: b'Multiple Choices',
    301: b'Moved Permanently',
    302: b'Found',
    303: b'See Other',
    304: b'Not Modified',
    305: b'Use Proxy',
    307: b'Temporary Redirect',
    308: b'Permanent Redirect',
    400: b'Bad Request',
    401: b'Unauthorized',
    402: b'Payment Required',
    403: b'Forbidden',
    404: b'Not Found',
    405: b'Method Not Allowed',
    406: b'Not Acceptable',
    407: b'Proxy Authentication Required',
    408: b'Request Timeout',
    409: b'Conflict',
    410: b'Gone',
    411: b'Length Required',
    412: b'Precondition Failed',
    413: b'Request Entity Too Large',
    414: b'Request-URI Too Long',
    415: b'Unsupported Media Type',
    416: b'Requested Range Not Satisfiable',
    417: b'Expectation Failed',
    422: b'Unprocessable Entity',
    423: b'Locked',
    424: b'Failed Dependency',
    426: b'Upgrade Required',
    428: b'Precondition Required',
    429: b'Too Many Requests',
    431: b'Request Header Fields Too Large',
    500: b'Internal Server Error',
    501: b'Not Implemented',
    502: b'Bad Gateway',
    503: b'Service Unavailable',
    504: b'Gateway Timeout',
    505: b'HTTP Version Not Supported',
    506: b'Variant Also Negotiates',
    507: b'Insufficient Storage',
    508: b'Loop Detected',
    510: b'Not Extended',
    511: b'Network Authentication Required'
}


class BaseHTTPResponse:
    def _encode_body(self, data):
        try:
            # Try to encode it regularly
            return data.encode()
        except AttributeError:
            # Convert it to a str if you can't
            return str(data).encode()

    def _parse_headers(self):
        headers = b''
        for name, value in self.headers.items():
            try:
                headers += (
                    b'%b: %b\r\n' % (
                        name.encode(), value.encode('utf-8')))
            except AttributeError:
                headers += (
                    b'%b: %b\r\n' % (
                        str(name).encode(), str(value).encode('utf-8')))

        return headers

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies


class StreamingHTTPResponse(BaseHTTPResponse):
    __slots__ = (
        'transport', 'streaming_fn',
        'status', 'content_type', 'headers', '_cookies')

    def __init__(self, streaming_fn, status=200, headers=None,
                 content_type='text/plain'):
        self.content_type = content_type
        self.streaming_fn = streaming_fn
        self.status = status
        self.headers = headers or {}
        self._cookies = None

    def write(self, data):
        """Writes a chunk of data to the streaming response.

        :param data: bytes-ish data to be written.
        """
        if type(data) != bytes:
            data = self._encode_body(data)

        self.transport.write(
            b"%x\r\n%b\r\n" % (len(data), data))

    async def stream(
            self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        """Streams headers, runs the `streaming_fn` callback that writes
        content to the response body, then finalizes the response body.
        """
        headers = self.get_headers(
            version, keep_alive=keep_alive,
            keep_alive_timeout=keep_alive_timeout)
        self.transport.write(headers)

        await self.streaming_fn(self)
        self.transport.write(b'0\r\n\r\n')

    def get_headers(
            self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        # This is all returned in a kind-of funky way
        # We tried to make this as fast as possible in pure python
        timeout_header = b''
        if keep_alive and keep_alive_timeout is not None:
            timeout_header = b'Keep-Alive: %d\r\n' % keep_alive_timeout

        self.headers['Transfer-Encoding'] = 'chunked'
        self.headers.pop('Content-Length', None)
        self.headers['Content-Type'] = self.headers.get(
            'Content-Type', self.content_type)

        headers = self._parse_headers()

        # Try to pull from the common codes first
        # Speeds up response rate 6% over pulling from all
        status = COMMON_STATUS_CODES.get(self.status)
        if not status:
            status = ALL_STATUS_CODES.get(self.status)

        return (b'HTTP/%b %d %b\r\n'
                b'%b'
                b'%b\r\n') % (
                   version.encode(),
                   self.status,
                   status,
                   timeout_header,
                   headers
               )


class HTTPResponse(BaseHTTPResponse):
    __slots__ = ('body', 'status', 'content_type', 'headers', '_cookies')

    def __init__(self, body=None, status=200, headers=None,
                 content_type='text/plain', body_bytes=b''):
        self.content_type = content_type

        if body is not None:
            self.body = self._encode_body(body)
        else:
            self.body = body_bytes

        self.status = status
        self.headers = headers or {}
        self._cookies = None

    def output(
            self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        # This is all returned in a kind-of funky way
        # We tried to make this as fast as possible in pure python
        timeout_header = b''
        if keep_alive and keep_alive_timeout is not None:
            timeout_header = b'Keep-Alive: %d\r\n' % keep_alive_timeout
        self.headers['Content-Length'] = self.headers.get(
            'Content-Length', len(self.body))
        self.headers['Content-Type'] = self.headers.get(
            'Content-Type', self.content_type)

        headers = self._parse_headers()

        # Try to pull from the common codes first
        # Speeds up response rate 6% over pulling from all
        status = COMMON_STATUS_CODES.get(self.status)
        if not status:
            status = ALL_STATUS_CODES.get(self.status, b'UNKNOWN RESPONSE')

        return (b'HTTP/%b %d %b\r\n'
                b'Connection: %b\r\n'
                b'%b'
                b'%b\r\n'
                b'%b') % (
                   version.encode(),
                   self.status,
                   status,
                   b'keep-alive' if keep_alive else b'close',
                   timeout_header,
                   headers,
                   self.body
               )

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = CookieJar(self.headers)
        return self._cookies


def json(body, status=200, headers=None,
         content_type="application/json", **kwargs):
    """
    Returns response object with body in json format.

    :param body: Response data to be serialized.
    :param status: Response code.
    :param headers: Custom Headers.
    :param kwargs: Remaining arguments that are passed to the json encoder.
    """
    return HTTPResponse(json_dumps(body, **kwargs), headers=headers,
                        status=status, content_type=content_type)


def text(body, status=200, headers=None,
         content_type="text/plain; charset=utf-8"):
    """
    Returns response object with body in text format.

    :param body: Response data to be encoded.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response
    """
    return HTTPResponse(
        body, status=status, headers=headers,
        content_type=content_type)


def raw(body, status=200, headers=None,
        content_type="application/octet-stream"):
    """
    Returns response object without encoding the body.

    :param body: Response data.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response.
    """
    return HTTPResponse(body_bytes=body, status=status, headers=headers,
                        content_type=content_type)


def html(body, status=200, headers=None):
    """
    Returns response object with body in html format.

    :param body: Response data to be encoded.
    :param status: Response code.
    :param headers: Custom Headers.
    """
    return HTTPResponse(body, status=status, headers=headers,
                        content_type="text/html; charset=utf-8")


async def file(location, mime_type=None, headers=None, _range=None):
    """Return a response object with file data.

    :param location: Location of file on system.
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param _range:
    """
    filename = path.split(location)[-1]

    async with open_async(location, mode='rb') as _file:
        if _range:
            await _file.seek(_range.start)
            out_stream = await _file.read(_range.size)
            headers['Content-Range'] = 'bytes %s-%s/%s' % (
                _range.start, _range.end, _range.total)
        else:
            out_stream = await _file.read()

    mime_type = mime_type or guess_type(filename)[0] or 'text/plain'

    return HTTPResponse(status=200,
                        headers=headers,
                        content_type=mime_type,
                        body_bytes=out_stream)


async def file_stream(location, chunk_size=4096, mime_type=None, headers=None,
                      _range=None):
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param _range:
    """
    filename = path.split(location)[-1]

    _file = await open_async(location, mode='rb')

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
                    response.write(content)
            else:
                while True:
                    content = await _file.read(chunk_size)
                    if len(content) < 1:
                        break
                    response.write(content)
        finally:
            await _file.close()
        return  # Returning from this fn closes the stream

    mime_type = mime_type or guess_type(filename)[0] or 'text/plain'
    if _range:
        headers['Content-Range'] = 'bytes %s-%s/%s' % (
            _range.start, _range.end, _range.total)
    return StreamingHTTPResponse(streaming_fn=_streaming_fn,
                                 status=200,
                                 headers=headers,
                                 content_type=mime_type)


def stream(
        streaming_fn, status=200, headers=None,
        content_type="text/plain; charset=utf-8"):
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
    """
    return StreamingHTTPResponse(
        streaming_fn,
        headers=headers,
        content_type=content_type,
        status=status
    )


def redirect(to, headers=None, status=302,
             content_type="text/html; charset=utf-8"):
    """Abort execution and cause a 302 redirect (by default).

    :param to: path or fully qualified URL to redirect to
    :param headers: optional dict of headers to include in the new request
    :param status: status code (int) of the new request, defaults to 302
    :param content_type: the content type (string) of the response
    :returns: the redirecting Response
    """
    headers = headers or {}

    # According to RFC 7231, a relative URI is now permitted.
    headers['Location'] = to

    return HTTPResponse(
        status=status,
        headers=headers,
        content_type=content_type)
