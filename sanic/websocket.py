from sanic.exceptions import InvalidUsage
from sanic.server import HttpProtocol
from httptools import HttpParserUpgrade
from websockets import handshake, WebSocketCommonProtocol, InvalidHandshake
from websockets import ConnectionClosed  # noqa


class WebSocketProtocol(HttpProtocol):
    def __init__(self, *args, websocket_max_size=None,
                 websocket_max_queue=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket = None
        self.websocket_max_size = websocket_max_size
        self.websocket_max_queue = websocket_max_queue

    # timeouts make no sense for websocket routes
    def request_timeout_callback(self):
        if self.websocket is None:
            super().request_timeout_callback()

    def response_timeout_callback(self):
        if self.websocket is None:
            super().response_timeout_callback()

    def keep_alive_timeout_callback(self):
        if self.websocket is None:
            super().keep_alive_timeout_callback()

    def connection_lost(self, exc):
        if self.websocket is not None:
            self.websocket.connection_lost(exc)
        super().connection_lost(exc)

    def data_received(self, data):
        if self.websocket is not None:
            # pass the data to the websocket protocol
            self.websocket.data_received(data)
        else:
            try:
                super().data_received(data)
            except HttpParserUpgrade:
                # this is okay, it just indicates we've got an upgrade request
                pass

    def write_response(self, response):
        if self.websocket is not None:
            # websocket requests do not write a response
            self.transport.close()
        else:
            super().write_response(response)

    async def websocket_handshake(self, request, subprotocols=None):
        # let the websockets package do the handshake with the client
        headers = []

        def get_header(k):
            return request.headers.get(k, '')

        def set_header(k, v):
            headers.append((k, v))

        try:
            key = handshake.check_request(get_header)
            handshake.build_response(set_header, key)
        except InvalidHandshake:
            raise InvalidUsage('Invalid websocket request')

        subprotocol = None
        if subprotocols and 'Sec-Websocket-Protocol' in request.headers:
            # select a subprotocol
            client_subprotocols = [p.strip() for p in request.headers[
                'Sec-Websocket-Protocol'].split(',')]
            for p in client_subprotocols:
                if p in subprotocols:
                    subprotocol = p
                    set_header('Sec-Websocket-Protocol', subprotocol)
                    break

        # write the 101 response back to the client
        rv = b'HTTP/1.1 101 Switching Protocols\r\n'
        for k, v in headers:
            rv += k.encode('utf-8') + b': ' + v.encode('utf-8') + b'\r\n'
        rv += b'\r\n'
        request.transport.write(rv)

        # hook up the websocket protocol
        self.websocket = WebSocketCommonProtocol(
            max_size=self.websocket_max_size,
            max_queue=self.websocket_max_queue
        )
        self.websocket.subprotocol = subprotocol
        self.websocket.connection_made(request.transport)
        self.websocket.connection_open()
        return self.websocket
