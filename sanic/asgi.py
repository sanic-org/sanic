import asyncio
import warnings

from inspect import isawaitable
from typing import Any, Awaitable, Callable, MutableMapping, Optional, Union
from urllib.parse import quote

import sanic.app  # noqa

from sanic.compat import Header
from sanic.exceptions import InvalidUsage, ServerError
from sanic.request import Request
from sanic.server import ConnInfo
from sanic.websocket import WebSocketConnection


ASGIScope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]


class MockProtocol:
    def __init__(self, transport: "MockTransport", loop):
        self.transport = transport
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


class MockTransport:
    _protocol: Optional[MockProtocol]

    def __init__(
        self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self._protocol = None
        self.loop = None

    def get_protocol(self) -> MockProtocol:
        if not self._protocol:
            self._protocol = MockProtocol(self, self.loop)
        return self._protocol

    def get_extra_info(self, info: str) -> Union[str, bool, None]:
        if info == "peername":
            return self.scope.get("client")
        elif info == "sslcontext":
            return self.scope.get("scheme") in ["https", "wss"]
        return None

    def get_websocket_connection(self) -> WebSocketConnection:
        try:
            return self._websocket_connection
        except AttributeError:
            raise InvalidUsage("Improper websocket connection.")

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


class Lifespan:
    def __init__(self, asgi_app: "ASGIApp") -> None:
        self.asgi_app = asgi_app

        if "before_server_start" in self.asgi_app.sanic_app.listeners:
            warnings.warn(
                'You have set a listener for "before_server_start" '
                "in ASGI mode. "
                "It will be executed as early as possible, but not before "
                "the ASGI server is started."
            )
        if "after_server_stop" in self.asgi_app.sanic_app.listeners:
            warnings.warn(
                'You have set a listener for "after_server_stop" '
                "in ASGI mode. "
                "It will be executed as late as possible, but not after "
                "the ASGI server is stopped."
            )

    async def startup(self) -> None:
        """
        Gather the listeners to fire on server start.
        Because we are using a third-party server and not Sanic server, we do
        not have access to fire anything BEFORE the server starts.
        Therefore, we fire before_server_start and after_server_start
        in sequence since the ASGI lifespan protocol only supports a single
        startup event.
        """
        listeners = self.asgi_app.sanic_app.listeners.get(
            "before_server_start", []
        ) + self.asgi_app.sanic_app.listeners.get("after_server_start", [])

        for handler in listeners:
            response = handler(
                self.asgi_app.sanic_app, self.asgi_app.sanic_app.loop
            )
            if response and isawaitable(response):
                await response

    async def shutdown(self) -> None:
        """
        Gather the listeners to fire on server stop.
        Because we are using a third-party server and not Sanic server, we do
        not have access to fire anything AFTER the server stops.
        Therefore, we fire before_server_stop and after_server_stop
        in sequence since the ASGI lifespan protocol only supports a single
        shutdown event.
        """
        listeners = self.asgi_app.sanic_app.listeners.get(
            "before_server_stop", []
        ) + self.asgi_app.sanic_app.listeners.get("after_server_stop", [])

        for handler in listeners:
            response = handler(
                self.asgi_app.sanic_app, self.asgi_app.sanic_app.loop
            )
            if response and isawaitable(response):
                await response

    async def __call__(
        self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> None:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await self.startup()
            await send({"type": "lifespan.startup.complete"})

        message = await receive()
        if message["type"] == "lifespan.shutdown":
            await self.shutdown()
            await send({"type": "lifespan.shutdown.complete"})


class ASGIApp:
    sanic_app: "sanic.app.Sanic"
    request: Request
    transport: MockTransport
    lifespan: Lifespan
    ws: Optional[WebSocketConnection]

    def __init__(self) -> None:
        self.ws = None

    @classmethod
    async def create(
        cls, sanic_app, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> "ASGIApp":
        instance = cls()
        instance.sanic_app = sanic_app
        instance.transport = MockTransport(scope, receive, send)
        instance.transport.loop = sanic_app.loop
        setattr(instance.transport, "add_task", sanic_app.loop.create_task)

        headers = Header(
            [
                (key.decode("latin-1"), value.decode("latin-1"))
                for key, value in scope.get("headers", [])
            ]
        )
        instance.lifespan = Lifespan(instance)

        if scope["type"] == "lifespan":
            await instance.lifespan(scope, receive, send)
        else:
            path = (
                scope["path"][1:]
                if scope["path"].startswith("/")
                else scope["path"]
            )
            url = "/".join([scope.get("root_path", ""), quote(path)])
            url_bytes = url.encode("latin-1")
            url_bytes += b"?" + scope["query_string"]

            if scope["type"] == "http":
                version = scope["http_version"]
                method = scope["method"]
            elif scope["type"] == "websocket":
                version = "1.1"
                method = "GET"

                instance.ws = instance.transport.create_websocket_connection(
                    send, receive
                )
                await instance.ws.accept()
            else:
                raise ServerError("Received unknown ASGI scope")

            request_class = sanic_app.request_class or Request
            instance.request = request_class(
                url_bytes,
                headers,
                version,
                method,
                instance.transport,
                sanic_app,
            )
            instance.request.stream = instance
            instance.request_body = True
            instance.request.conn_info = ConnInfo(instance.transport)

        return instance

    async def read(self) -> Optional[bytes]:
        """
        Read and stream the body in chunks from an incoming ASGI message.
        """
        message = await self.transport.receive()
        if not message.get("more_body", False):
            self.request_body = False
            return None
        return message.get("body", b"")

    async def __aiter__(self):
        while self.request_body:
            data = await self.read()
            if data:
                yield data

    def respond(self, response):
        response.stream, self.response = self, response
        return response

    async def send(self, data, end_stream):
        if self.response:
            response, self.response = self.response, None
            await self.transport.send(
                {
                    "type": "http.response.start",
                    "status": response.status,
                    "headers": response.processed_headers,
                }
            )
            response_body = getattr(response, "body", None)
            if response_body:
                data = response_body + data if data else response_body
        await self.transport.send(
            {
                "type": "http.response.body",
                "body": data.encode() if hasattr(data, "encode") else data,
                "more_body": not end_stream,
            }
        )

    _asgi_single_callable = True  # We conform to ASGI 3.0 single-callable

    async def __call__(self) -> None:
        """
        Handle the incoming request.
        """
        await self.sanic_app.handle_request(self.request)
