import ujson

STATUS_CODES = {
    200: 'OK',
    404: 'Not Found'
}
class HTTPResponse:
    __slots__ = ('body', 'status', 'content_type')

    def __init__(self, body='', status=200, content_type='text/plain'):
        self.content_type = 'text/plain'
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


def error_404(request, *args):
    return HTTPResponse("404!", status=404)
error_404.is_async = False

def json(input):
    return HTTPResponse(ujson.dumps(input), content_type="application/json")
def text(input):
    return HTTPResponse(input, content_type="text/plain")