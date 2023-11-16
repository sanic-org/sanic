from typing import TYPE_CHECKING, Optional, Sequence, cast


try:  # websockets < 11.0
    from websockets.connection import State
    from websockets.server import ServerConnection as ServerProtocol
except ImportError:  # websockets >= 11.0
    from websockets.protocol import State  # type: ignore
    from websockets.server import ServerProtocol  # type: ignore

from websockets.typing import Subprotocol

from sanic.exceptions import SanicException
from sanic.log import access_logger, websockets_logger
from sanic.server import HttpProtocol

from ..websockets.impl import WebsocketImplProtocol


if TYPE_CHECKING:
    from websockets import http11


OPEN = State.OPEN
CLOSING = State.CLOSING
CLOSED = State.CLOSED


class WebSocketProtocol(HttpProtocol):
    __slots__ = (
        "websocket",
        "websocket_timeout",
        "websocket_max_size",
        "websocket_ping_interval",
        "websocket_ping_timeout",
        "websocket_url",
        "websocket_peer",
    )

    def __init__(
        self,
        *args,
        websocket_timeout: float = 10.0,
        websocket_max_size: Optional[int] = None,
        websocket_ping_interval: Optional[float] = 20.0,
        websocket_ping_timeout: Optional[float] = 20.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.websocket: Optional[WebsocketImplProtocol] = None
        self.websocket_timeout = websocket_timeout
        self.websocket_max_size = websocket_max_size
        self.websocket_ping_interval = websocket_ping_interval
        self.websocket_ping_timeout = websocket_ping_timeout
        self.websocket_url = None
        self.websocket_peer = None

    def connection_lost(self, exc):
        if self.websocket is not None:
            self.websocket.connection_lost(exc)
        super().connection_lost(exc)
        self.log_websocket("CLOSE")
        self.websocket_url = None
        self.websocket_peer = None

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
            if self.websocket.ws_proto.state in (CLOSING, CLOSED):
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
                # but ServerProtocol needs a list
                subprotocols = cast(
                    Optional[Sequence[Subprotocol]],
                    list(
                        [
                            Subprotocol(subprotocol)
                            for subprotocol in subprotocols
                        ]
                    ),
                )
            ws_proto = ServerProtocol(
                max_size=self.websocket_max_size,
                subprotocols=subprotocols,
                state=OPEN,
                logger=websockets_logger,
            )
            resp: "http11.Response" = ws_proto.accept(request)
        except Exception:
            msg = (
                "Failed to open a WebSocket connection.\n"
                "See server log for more information.\n"
            )
            raise SanicException(msg, status_code=500)
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
            raise SanicException(resp.body, resp.status_code)
        self.websocket = WebsocketImplProtocol(
            ws_proto,
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
        self.websocket_url = self._http.request.url
        self.websocket_peer = "UNKNOWN"
        if ip := self._http.request.client_ip:
            self.websocket_peer = f"{ip}:{self._http.request.port}"
        self.log_websocket("OPEN")
        return self.websocket

    def log_websocket(self, message):
        if not self.access_log or not self.websocket_url:
            return
        req = self._http.request if self._http else None
        status = ""
        close = ""
        try:
            # Can we get some useful statistics?
            ws_proto = self.websocket.ws_proto
            state = ws_proto.state
            if state == CLOSED:
                close_codes = {1000: "NORMAL", 1001: "GOING AWAY"}
                if ws_proto.close_code == 1006:
                    message = "CLOSE_ABNORMAL"
                scode = (
                    ws_proto.close_sent.code if ws_proto.close_sent else None
                )
                rcode = (
                    ws_proto.close_rcvd.code if ws_proto.close_rcvd else None
                )
                sdesc = close_codes.get(scode, str(scode))
                rdesc = close_codes.get(rcode, str(rcode))
                if ws_proto.close_rcvd_then_sent:
                    status = rcode
                    close = f"{rdesc} rcvd -> {sdesc} sent"
                elif scode and rcode:
                    status = scode
                    close = f"{sdesc} sent -> {rdesc} revd"
                elif rcode:
                    status = rcode
                    close = f"{rdesc} rcvd"
                else:
                    status = scode
                    close = f"{sdesc} sent"

        except AttributeError:
            ...
        extra = {
            "status": status,
            "byte": close,
            "host": self.websocket_peer,
            "request": f"🔌 {self.websocket_url}",
        }
        access_logger.info(message, extra=extra)
