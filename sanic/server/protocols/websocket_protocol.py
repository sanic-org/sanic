from typing import (
    Optional,
    Union,
    Sequence,
    TYPE_CHECKING
)

from httptools import HttpParserUpgrade  # type: ignore
from websockets.server import ServerConnection
from websockets.connection import OPEN, CLOSING, CLOSED

from sanic.exceptions import SanicException
from sanic.server import HttpProtocol
from sanic.log import error_logger
from ..websockets.impl import WebsocketImplProtocol

if TYPE_CHECKING:
    from websockets import http11

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
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.websocket = None  # type: Union[None, WebsocketImplProtocol]
        # self.app = None
        self.websocket_timeout = websocket_timeout
        self.websocket_max_size = websocket_max_size
        if websocket_max_queue is not None and int(websocket_max_queue) > 0:
            error_logger.warning(DeprecationWarning("websocket_max_queue is no longer used. No websocket message queueing is implemented."))
        self.websocket_read_limit = websocket_read_limit
        self.websocket_write_limit = websocket_write_limit
        self.websocket_ping_interval = websocket_ping_interval
        self.websocket_ping_timeout = websocket_ping_timeout

    def connection_lost(self, exc):
        if self.websocket is not None:
            self.websocket.connection_lost(exc)
        super().connection_lost(exc)

    def data_received(self, data):
        if self.websocket is not None:
            self.websocket.data_received(data)
        else:
            # Pass it to HttpProtocol handler first
            # That will (hopefully) upgrade it to a websocket.
            super().data_received(data)

    def eof_received(self) -> Optional[bool]:
        if self.websocket is not None:
            return self.websocket.eof_received()
        else:
            return False

    def close(self, timeout: Optional[float] = None):
        # Called by HttpProtocol at the end of connection_task
        # If we've upgraded to websocket, we do our own closing
        if self.websocket is not None:
            self.websocket.fail_connection(1001)
        else:
            super().close()

    def close_if_idle(self):
        # Called by Sanic Server when shutting down
        # If we've upgraded to websocket, shut it down
        if self.websocket is not None:
            if self.websocket.connection.state in (CLOSING, CLOSED):
                return True
            else:
                return self.websocket.fail_connection(1001)
        else:
            return super().close_if_idle()

    async def websocket_handshake(self, request, subprotocols=Optional[Sequence[str]]):
        # let the websockets package do the handshake with the client
        headers = {"Upgrade": "websocket", "Connection": "Upgrade"}
        try:
            if subprotocols is not None:
                # subprotocols can be a set or frozenset, but ServerConnection needs a list
                subprotocols = list(subprotocols)
            ws_conn = ServerConnection(max_size=self.websocket_max_size, subprotocols=subprotocols,
                                       state=OPEN, logger=error_logger)
            resp: "http11.Response" = ws_conn.accept(request)
        except Exception as exc:
            msg = (
                    "Failed to open a WebSocket connection.\n"
                    "See server log for more information.\n"
                )
            raise SanicException(msg, status_code=500)
        if 100 <= resp.status_code <= 299:
            rbytes = b"".join([b"HTTP/1.1 ", b'%d' % resp.status_code, b" ", resp.reason_phrase.encode("utf-8"), b"\r\n"])
            for k, v in resp.headers.items():
                rbytes += k.encode("utf-8") + b": " + v.encode("utf-8") + b"\r\n"
            if resp.body:
                rbytes += b"\r\n" + resp.body + b"\r\n"
            rbytes += b"\r\n"
            await super().send(rbytes)
        else:
            raise SanicException(resp.body, resp.status_code)

        self.websocket = WebsocketImplProtocol(ws_conn, ping_interval=self.websocket_ping_interval, ping_timeout=self.websocket_ping_timeout)
        loop = request.transport.loop if hasattr(request, "transport") and hasattr(request.transport, "loop") else None
        await self.websocket.connection_made(self, loop=loop)
        return self.websocket
