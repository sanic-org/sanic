import ujson

STATUS_CODES = {
    200: b'OK',
    400: b'Bad Request',
    401: b'Unauthorized',
    402: b'Payment Required',
    403: b'Forbidden',
    404: b'Not Found',
    405: b'Method Not Allowed',
    500: b'Internal Server Error',
    501: b'Not Implemented',
    502: b'Bad Gateway',
    503: b'Service Unavailable',
    504: b'Gateway Timeout',
}


class HTTPResponse:
    __slots__ = ('body', 'status', 'content_type', 'headers')

    def __init__(self, body=None, status=200, headers=None, content_type='text/plain', body_bytes=b''):
        self.content_type = content_type

        if body is not None:
            self.body = body.encode('utf-8')
        else:
            self.body = body_bytes

        self.status = status
        self.headers = headers or {}

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
        return b'HTTP/%b %d %b\r\nContent-Type: %b\r\nContent-Length: %d\r\nConnection: %b\r\n%b%b\r\n%b' % (
            version.encode(),
            self.status,
            STATUS_CODES.get(self.status, b'FAIL'),
            self.content_type.encode(),
            len(self.body),
            b'keep-alive' if keep_alive else b'close',
            timeout_header,
            headers,
            self.body
        )


def json(body, status=200, headers=None):
    return HTTPResponse(ujson.dumps(body), headers=headers, status=status,
                        content_type="application/json; charset=utf-8")


def text(body, status=200, headers=None):
    return HTTPResponse(body, status=status, headers=headers, content_type="text/plain; charset=utf-8")


def html(body, status=200, headers=None):
    return HTTPResponse(body, status=status, headers=headers, content_type="text/html; charset=utf-8")
