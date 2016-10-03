import ujson
import httptools
from ujson import loads as json_loads
from urllib.parse import parse_qs

STATUS_CODES = {
    200: 'OK',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    400: 'Method Not Allowed',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
}
class HTTPResponse:
    __slots__ = ('body', 'status', 'content_type')

    def __init__(self, body='', status=200, content_type='text/plain'):
        self.content_type = content_type
        self.body = body
        self.status = status

    @property
    def body_bytes(self):
        body_type = type(self.body)
        if body_type is str:
            body = self.body.encode('utf-8')
        elif body_type is bytes:
            body = self.body
        else:
            body = b'Unable to interpret body'

        return body

    def output(self, version="1.1", keep_alive=False):
        body = self.body_bytes
        return b''.join([
            'HTTP/{} {} {}\r\n'.format(version, self.status, STATUS_CODES.get(self.status, 'FAIL')).encode('latin-1'),
            'Content-Type: {}\r\n'.format(self.content_type).encode('latin-1'),
            'Content-Length: {}\r\n'.format(len(body)).encode('latin-1'),
            'Connection: {}\r\n'.format('keep-alive' if keep_alive else 'close').encode('latin-1'),
            b'\r\n',
            body,
            #b'\r\n'
        ])

def json(body, status=200):
    return HTTPResponse(ujson.dumps(body), status=status, content_type="application/json")
def text(body, status=200):
    return HTTPResponse(body, status=status, content_type="text/plain")
def html(body, status=200):
    return HTTPResponse(body, status=status, content_type="text/html")