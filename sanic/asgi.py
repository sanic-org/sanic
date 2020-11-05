import asyncio
import warnings

from inspect import isawaitable
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import quote

import sanic.app  # noqa

from sanic.compat import Header
from sanic.exceptions import InvalidUsage, ServerError
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse, StreamingHTTPResponse
from sanic.server import ConnInfo, StreamBuffer
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
            return self.scope.get("server")
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
            if isawaitable(response):
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
            if isawaitable(response):
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
    do_stream: bool
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
        instance.do_stream = (
            True if headers.get("expect") == "100-continue" else False
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
                pass
                # TODO:
                # - close connection

            request_class = sanic_app.request_class or Request
            instance.request = request_class(
                url_bytes,
                headers,
                version,
                method,
                instance.transport,
                sanic_app,
            )
            instance.request.conn_info = ConnInfo(instance.transport)

            if sanic_app.is_request_stream:
                is_stream_handler = sanic_app.router.is_stream_handler(
                    instance.request
                )
                if is_stream_handler:
                    instance.request.stream = StreamBuffer(
                        sanic_app.config.REQUEST_BUFFER_QUEUE_SIZE
                    )
                    instance.do_stream = True

        return instance

    async def read_body(self) -> bytes:
        """
        Read and return the entire body from an incoming ASGI message.
        """
        body = b""
        more_body = True
        while more_body:
            message = await self.transport.receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        return body

    async def stream_body(self) -> None:
        """
        Read and stream the body in chunks from an incoming ASGI message.
        """
        more_body = True

        while more_body:
            message = await self.transport.receive()
            chunk = message.get("body", b"")
            await self.request.stream.put(chunk)

            more_body = message.get("more_body", False)

        await self.request.stream.put(None)

    async def __call__(self) -> None:
        """
        Handle the incoming request.
        """
        if not self.do_stream:
            self.request.body = await self.read_body()
        else:
            self.sanic_app.loop.create_task(self.stream_body())

        handler = self.sanic_app.handle_request
        callback = None if self.ws else self.stream_callback
        await handler(self.request, None, callback)

    _asgi_single_callable = True  # We conform to ASGI 3.0 single-callable

    async def stream_callback(
        self, response: Union[HTTPResponse, StreamingHTTPResponse]
    ) -> None:
        """
        Write the response.
        """
        headers: List[Tuple[bytes, bytes]] = []
        cookies: Dict[str, str] = {}
        content_length: List[str] = []
        try:
            content_length = response.headers.popall("content-length", [])
            cookies = {
                v.key: v
                for _, v in list(
                    filter(
                        lambda item: item[0].lower() == "set-cookie",
                        response.headers.items(),
                    )
                )
            }
            headers += [
                (str(name).encode("latin-1"), str(value).encode("latin-1"))
                for name, value in response.headers.items()
                if name.lower() not in ["set-cookie"]
            ]
        except AttributeError:
            logger.error(
                "Invalid response object for url %s, "
                "Expected Type: HTTPResponse, Actual Type: %s",
                self.request.url,
                type(response),
            )
            exception = ServerError("Invalid response type")
            response = self.sanic_app.error_handler.response(
                self.request, exception
            )
            headers = [
                (str(name).encode("latin-1"), str(value).encode("latin-1"))
                for name, value in response.headers.items()
                if name not in (b"Set-Cookie",)
            ]

        response.asgi = True
        is_streaming = isinstance(response, StreamingHTTPResponse)
        if is_streaming and getattr(response, "chunked", False):
            # disable sanic chunking, this is done at the ASGI-server level
            setattr(response, "chunked", False)
            # content-length header is removed to signal to the ASGI-server
            # to use automatic-chunking if it supports it
        elif len(content_length) > 0:
            headers += [
                (b"content-length", str(content_length[0]).encode("latin-1"))
            ]
        elif not is_streaming:
            headers += [
                (
                    b"content-length",
                    str(len(getattr(response, "body", b""))).encode("latin-1"),
                )
            ]

        if "content-type" not in response.headers:
            headers += [
                (b"content-type", str(response.content_type).encode("latin-1"))
            ]

        if response.cookies:
            cookies.update(
                {
                    v.key: v
                    for _, v in response.cookies.items()
                    if v.key not in cookies.keys()
                }
            )

        headers += [
            (b"set-cookie", cookie.encode("utf-8"))
            for k, cookie in cookies.items()
        ]

        await self.transport.send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": headers,
            }
        )

        if isinstance(response, StreamingHTTPResponse):
            response.protocol = self.transport.get_protocol()
            await response.stream()
            await response.protocol.complete()

        else:
            await self.transport.send(
                {
                    "type": "http.response.body",
                    "body": response.body,
                    "more_body": False,
                }
            )
