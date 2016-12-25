from aiofiles import open as open_async
from mimetypes import guess_type
from os import path

from ujson import dumps as json_dumps

from .cookies import CookieJar

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


class HTTPResponse:
    __slots__ = ('body', 'status', 'content_type', 'headers', '_cookies')

    def __init__(self, body=None, status=200, headers=None,
                 content_type='text/plain', body_bytes=b''):
        self.content_type = content_type

        if body is not None:
            try:
                # Try to encode it regularly
                self.body = body.encode('utf-8')
            except AttributeError:
                # Convert it to a str if you can't
                self.body = str(body).encode('utf-8')
        else:
            self.body = body_bytes

        self.status = status
        self.headers = headers or {}
        self._cookies = None

    def output(self, version="1.1", keep_alive=False, keep_alive_timeout=None):
        # This is all returned in a kind-of funky way
        # We tried to make this as fast as possible in pure python
        timeout_header = b''
        if keep_alive and keep_alive_timeout:
            timeout_header = b'Keep-Alive: timeout=%d\r\n' % keep_alive_timeout

        headers = b''
        if self.headers:
            headers = b''.join(
                b'%b: %b\r\n' % (name.encode(), value.encode('utf-8'))
                for name, value in self.headers.items()
            )

        # Try to pull from the common codes first
        # Speeds up response rate 6% over pulling from all
        status = COMMON_STATUS_CODES.get(self.status)
        if not status:
            status = ALL_STATUS_CODES.get(self.status)

        return (b'HTTP/%b %d %b\r\n'
                b'Content-Type: %b\r\n'
                b'Content-Length: %d\r\n'
                b'Connection: %b\r\n'
                b'%b%b\r\n'
                b'%b') % (
            version.encode(),
            self.status,
            status,
            self.content_type.encode(),
            len(self.body),
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


def json(body, status=200, headers=None):
    return HTTPResponse(json_dumps(body), headers=headers, status=status,
                        content_type="application/json")


def text(body, status=200, headers=None):
    return HTTPResponse(body, status=status, headers=headers,
                        content_type="text/plain; charset=utf-8")


def html(body, status=200, headers=None):
    return HTTPResponse(body, status=status, headers=headers,
                        content_type="text/html; charset=utf-8")


async def file(location, mime_type=None, headers=None):
    filename = path.split(location)[-1]

    async with open_async(location, mode='rb') as _file:
        out_stream = await _file.read()

    mime_type = mime_type or guess_type(filename)[0] or 'text/plain'

    return HTTPResponse(status=200,
                        headers=headers,
                        content_type=mime_type,
                        body_bytes=out_stream)
