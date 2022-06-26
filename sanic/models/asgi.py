import asyncio
import sys

from typing import Any, Awaitable, Callable, MutableMapping, Optional, Union

from sanic.exceptions import BadRequest
from sanic.models.protocol_types import TransportProtocol
from sanic.server.websockets.connection import WebSocketConnection


ASGIScope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]


class MockProtocol:  # no cov
    def __init__(self, transport: "MockTransport", loop):
        # This should be refactored when < 3.8 support is dropped
        self.transport = transport
        # Fixup for 3.8+; Sanic still supports 3.7 where loop is required
        loop = loop if sys.version_info[:2] < (3, 8) else None
        # Optional in 3.9, necessary in 3.10 because the parameter "loop"
        # was completely removed
        if not loop:
            self._not_paused = asyncio.Event()
            self._not_paused.set()
            self._complete = asyncio.Event()
        else:
            self._not_paused = asyncio.Event(loop=loop)
            self._not_paused.set()
            self._complete = asyncio.Event(loop=loop)

    def pause_writing(self) -> None:
        self._not_paused.clear()

    def resume_writing(self) -> None:
        self._not_paused.set()

    async def complete(self) -> None:
        self._not_paused.set()
        await self.transport.send(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )

    @property
    def is_complete(self) -> bool:
        return self._complete.is_set()

    async def push_data(self, data: bytes) -> None:
        if not self.is_complete:
            await self.transport.send(
                {"type": "http.response.body", "body": data, "more_body": True}
            )

    async def drain(self) -> None:
        await self._not_paused.wait()


class MockTransport(TransportProtocol):  # no cov
    _protocol: Optional[MockProtocol]

    def __init__(
        self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self._protocol = None
        self.loop = None

    def get_protocol(self) -> MockProtocol:  # type: ignore
        if not self._protocol:
            self._protocol = MockProtocol(self, self.loop)
        return self._protocol

    def get_extra_info(
        self, info: str, default=None
    ) -> Optional[Union[str, bool]]:
        if info == "peername":
            return self.scope.get("client")
        elif info == "sslcontext":
            return self.scope.get("scheme") in ["https", "wss"]
        return default

    def get_websocket_connection(self) -> WebSocketConnection:
        try:
            return self._websocket_connection
        except AttributeError:
            raise BadRequest("Improper websocket connection.")

    def create_websocket_connection(
        self, send: ASGISend, receive: ASGIReceive
    ) -> WebSocketConnection:
        self._websocket_connection = WebSocketConnection(
            send, receive, self.scope.get("subprotocols", [])
        )
        return self._websocket_connection

    def add_task(self) -> None:
        raise NotImplementedError

    async def send(self, data) -> None:
        # TODO:
        # - Validation on data and that it is formatted properly and is valid
        await self._send(data)

    async def receive(self) -> ASGIMessage:
        return await self._receive()
