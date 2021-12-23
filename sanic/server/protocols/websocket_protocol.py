from typing import TYPE_CHECKING, Optional, Sequence, cast

from websockets.connection import CLOSED, CLOSING, OPEN
from websockets.server import ServerConnection
from websockets.typing import Subprotocol

from sanic.exceptions import ServerError
from sanic.log import deprecation, error_logger
from sanic.server import HttpProtocol

from ..websockets.impl import WebsocketImplProtocol


if TYPE_CHECKING:
    from websockets import http11


class WebSocketProtocol(HttpProtocol):
    __slots__ = (
        "websocket",
        "websocket_timeout",
        "websocket_max_size",
        "websocket_ping_interval",
        "websocket_ping_timeout",
    )

    def __init__(
        self,
        *args,
        websocket_timeout: float = 10.0,
        websocket_max_size: Optional[int] = None,
        websocket_max_queue: Optional[int] = None,  # max_queue is deprecated
        websocket_read_limit: Optional[int] = None,  # read_limit is deprecated
        websocket_write_limit: Optional[int] = None,  # write_limit deprecated
        websocket_ping_interval: Optional[float] = 20.0,
        websocket_ping_timeout: Optional[float] = 20.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.websocket: Optional[WebsocketImplProtocol] = None
        self.websocket_timeout = websocket_timeout
        self.websocket_max_size = websocket_max_size
        if websocket_max_queue is not None and websocket_max_queue > 0:
            # TODO: Reminder remove this warning in v22.3
            deprecation(
                "Websocket no longer uses queueing, so websocket_max_queue"
                " is no longer required.",
                22.3,
            )
        if websocket_read_limit is not None and websocket_read_limit > 0:
            # TODO: Reminder remove this warning in v22.3
            deprecation(
                "Websocket no longer uses read buffers, so "
                "websocket_read_limit is not required.",
                22.3,
            )
        if websocket_write_limit is not None and websocket_write_limit > 0:
            # TODO: Reminder remove this warning in v22.3
            deprecation(
                "Websocket no longer uses write buffers, so "
                "websocket_write_limit is not required.",
                22.3,
            )
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
            # Note, we don't want to use websocket.close()
            # That is used for user's application code to send a
            # websocket close packet. This is different.
            self.websocket.end_connection(1001)
        else:
            super().close()

    def close_if_idle(self):
        # Called by Sanic Server when shutting down
        # If we've upgraded to websocket, shut it down
        if self.websocket is not None:
            if self.websocket.connection.state in (CLOSING, CLOSED):
                return True
            elif self.websocket.loop is not None:
                self.websocket.loop.create_task(self.websocket.close(1001))
            else:
                self.websocket.end_connection(1001)
        else:
            return super().close_if_idle()

    async def websocket_handshake(
        self, request, subprotocols: Optional[Sequence[str]] = None
    ):
        # let the websockets package do the handshake with the client
        try:
            if subprotocols is not None:
                # subprotocols can be a set or frozenset,
                # but ServerConnection needs a list
                subprotocols = cast(
                    Optional[Sequence[Subprotocol]],
                    list(
                        [
                            Subprotocol(subprotocol)
                            for subprotocol in subprotocols
                        ]
                    ),
                )
            ws_conn = ServerConnection(
                max_size=self.websocket_max_size,
                subprotocols=subprotocols,
                state=OPEN,
                logger=error_logger,
            )
            resp: "http11.Response" = ws_conn.accept(request)
        except Exception:
            msg = (
                "Failed to open a WebSocket connection.\n"
                "See server log for more information.\n"
            )
            raise ServerError(msg, status_code=500)
        if 100 <= resp.status_code <= 299:
            first_line = (
                f"HTTP/1.1 {resp.status_code} {resp.reason_phrase}\r\n"
            ).encode()
            rbody = bytearray(first_line)
            rbody += (
                "".join([f"{k}: {v}\r\n" for k, v in resp.headers.items()])
            ).encode()
            rbody += b"\r\n"
            if resp.body is not None:
                rbody += resp.body
                rbody += b"\r\n\r\n"
            await super().send(rbody)
        else:
            raise ServerError(resp.body, resp.status_code)
        self.websocket = WebsocketImplProtocol(
            ws_conn,
            ping_interval=self.websocket_ping_interval,
            ping_timeout=self.websocket_ping_timeout,
            close_timeout=self.websocket_timeout,
        )
        loop = (
            request.transport.loop
            if hasattr(request, "transport")
            and hasattr(request.transport, "loop")
            else None
        )
        await self.websocket.connection_made(self, loop=loop)
        return self.websocket
