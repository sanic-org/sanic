from collections.abc import Sequence
from typing import Optional, cast


try:  # websockets >= 11.0
    from websockets.protocol import State  # type: ignore
    from websockets.server import ServerProtocol  # type: ignore
except ImportError:  # websockets < 11.0
    from websockets.connection import State
    from websockets.server import ServerConnection as ServerProtocol

from websockets import http11
from websockets.datastructures import Headers as WSHeaders
from websockets.typing import Subprotocol

from sanic.exceptions import SanicException
from sanic.log import access_logger, websockets_logger
from sanic.request import Request
from sanic.server import HttpProtocol

from ..websockets.impl import WebsocketImplProtocol


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
        self.websocket_url: Optional[str] = None
        self.websocket_peer: Optional[str] = None

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

    @staticmethod
    def sanic_request_to_ws_request(request: Request):
        return http11.Request(
            path=request.path,
            headers=WSHeaders(request.headers),
        )

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
            resp = ws_proto.accept(self.sanic_request_to_ws_request(request))
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
            if resp.body:
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
        self.websocket_peer = f"{id(self):X}"[-5:-1] + "unx"
        if ip := self._http.request.client_ip:
            self.websocket_peer = f"{ip}:{self._http.request.port}"
        self.log_websocket("OPEN")
        return self.websocket

    def log_websocket(self, message):
        if not self.access_log or not self.websocket_url:
            return
        status = ""
        close = ""
        try:
            # Can we get some useful statistics?
            p = self.websocket.ws_proto
            state = p.state
            if state == CLOSED:
                codes = {
                    1000: "NORMAL",
                    1001: "GOING AWAY",
                    1005: "NO STATUS",
                    1006: "ABNORMAL",
                    1011: "SERVER ERR",
                }
                if p.close_code == 1006:
                    message = "CLOSE_ABN"
                scode = rcode = 1006  # Abnormal closure (disconnection)
                sdesc = rdesc = ""
                if p.close_sent:
                    scode = p.close_sent.code
                    sdesc = p.close_sent.reason
                if p.close_rcvd:
                    rcode = p.close_rcvd.code
                    rdesc = p.close_rcvd.reason
                # Use repr() to escape any control characters
                sdesc = repr(sdesc[:256]) if sdesc else codes.get(scode, "")
                rdesc = repr(rdesc[:256]) if rdesc else codes.get(rcode, "")
                if p.close_rcvd_then_sent or scode == 1006:
                    status = rcode
                    close = (
                        f"{rdesc} from client"
                        if scode in (rcode, 1006)
                        else f"{rdesc} ▼▲ {scode} {sdesc}"
                    )
                else:
                    status = scode
                    close = (
                        f"{sdesc} from server"
                        if rcode in (scode, 1006)
                        else f"{sdesc} ▲▼ {rcode} {rdesc}"
                    )

        except AttributeError:
            ...
        extra = {
            "status": status,
            "byte": close,
            "host": self.websocket_peer,
            "request": f" 🔌 {self.websocket_url}",
            "duration": "",
        }
        access_logger.info(message, extra=extra)
