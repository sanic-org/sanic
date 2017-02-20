from sanic.server import HttpProtocol
from httptools import HttpParserUpgrade
from websockets import handshake, WebSocketCommonProtocol
from websockets import ConnectionClosed  # noqa


class WebSocketProtocol(HttpProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = None

    def data_received(self, data):
        if self.ws is not None:
            # pass the data to the websocket protocol
            self.ws.data_received(data)
        else:
            try:
                super().data_received(data)
            except HttpParserUpgrade:
                # this is okay, it just indicates we've got an upgrade request
                pass

    def write_response(self, response):
        if self.ws is not None:
            # websocket requests do not write a response
            self.transport.close()
        else:
            super().write_response(response)

    async def websocket_handshake(self, request):
        # let the websockets package do the handshake with the client
        headers = []

        def get_header(k):
            return request.headers.get(k, '')

        def set_header(k, v):
            headers.append((k, v))

        key = handshake.check_request(get_header)
        handshake.build_response(set_header, key)

        # write the 101 response back to the client
        rv = b'HTTP/1.1 101 Switching Protocols\r\n'
        for k, v in headers:
            rv += k.encode('utf-8') + b': ' + v.encode('utf-8') + b'\r\n'
        rv += b'\r\n'
        request.transport.write(rv)

        # hook up the websocket protocol
        self.ws = WebSocketCommonProtocol()
        self.ws.connection_made(request.transport)
        return self.ws
