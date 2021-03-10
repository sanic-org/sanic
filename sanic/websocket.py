from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Union,
)

from httptools import HttpParserUpgrade  # type: ignore
from websockets import (  # type: ignore
    ConnectionClosed,
    InvalidHandshake,
    WebSocketCommonProtocol,
    handshake,
)

from sanic.exceptions import InvalidUsage
from sanic.server import HttpProtocol


__all__ = ["ConnectionClosed", "WebSocketProtocol", "WebSocketConnection"]

ASIMessage = MutableMapping[str, Any]


class WebSocketProtocol(HttpProtocol):
    def __init__(
        self,
        *args,
        websocket_timeout=10,
        websocket_max_size=None,
        websocket_max_queue=None,
        websocket_read_limit=2 ** 16,
        websocket_write_limit=2 ** 16,
        websocket_ping_interval=20,
        websocket_ping_timeout=20,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.websocket = None
        # self.app = None
        self.websocket_timeout = websocket_timeout
        self.websocket_max_size = websocket_max_size
        self.websocket_max_queue = websocket_max_queue
        self.websocket_read_limit = websocket_read_limit
        self.websocket_write_limit = websocket_write_limit
        self.websocket_ping_interval = websocket_ping_interval
        self.websocket_ping_timeout = websocket_ping_timeout

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
        headers = {}

        try:
            key = handshake.check_request(request.headers)
            handshake.build_response(headers, key)
        except InvalidHandshake:
            raise InvalidUsage("Invalid websocket request")

        subprotocol = None
        if subprotocols and "Sec-Websocket-Protocol" in request.headers:
            # select a subprotocol
            client_subprotocols = [
                p.strip()
                for p in request.headers["Sec-Websocket-Protocol"].split(",")
            ]
            for p in client_subprotocols:
                if p in subprotocols:
                    subprotocol = p
                    headers["Sec-Websocket-Protocol"] = subprotocol
                    break

        # write the 101 response back to the client
        rv = b"HTTP/1.1 101 Switching Protocols\r\n"
        for k, v in headers.items():
            rv += k.encode("utf-8") + b": " + v.encode("utf-8") + b"\r\n"
        rv += b"\r\n"
        request.transport.write(rv)

        # hook up the websocket protocol
        self.websocket = WebSocketCommonProtocol(
            close_timeout=self.websocket_timeout,
            max_size=self.websocket_max_size,
            max_queue=self.websocket_max_queue,
            read_limit=self.websocket_read_limit,
            write_limit=self.websocket_write_limit,
            ping_interval=self.websocket_ping_interval,
            ping_timeout=self.websocket_ping_timeout,
        )
        # Following two lines are required for websockets 8.x
        self.websocket.is_client = False
        self.websocket.side = "server"
        self.websocket.subprotocol = subprotocol
        self.websocket.connection_made(request.transport)
        self.websocket.connection_open()
        return self.websocket


class WebSocketConnection:

    # TODO
    # - Implement ping/pong

    def __init__(
        self,
        send: Callable[[ASIMessage], Awaitable[None]],
        receive: Callable[[], Awaitable[ASIMessage]],
        subprotocols: Optional[List[str]] = None,
    ) -> None:
        self._send = send
        self._receive = receive
        self.subprotocols = subprotocols or []

    async def send(self, data: Union[str, bytes], *args, **kwargs) -> None:
        message: Dict[str, Union[str, bytes]] = {"type": "websocket.send"}

        if isinstance(data, bytes):
            message.update({"bytes": data})
        else:
            message.update({"text": str(data)})

        await self._send(message)

    async def recv(self, *args, **kwargs) -> Optional[str]:
        message = await self._receive()

        if message["type"] == "websocket.receive":
            return message["text"]
        elif message["type"] == "websocket.disconnect":
            pass

        return None

    receive = recv

    async def accept(self) -> None:
        await self._send(
            {
                "type": "websocket.accept",
                "subprotocol": ",".join(list(self.subprotocols)),
            }
        )

    async def close(self) -> None:
        pass
