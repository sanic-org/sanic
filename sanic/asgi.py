from typing import Any, Awaitable, Callable, MutableMapping, Union
import asyncio
from multidict import CIMultiDict
from functools import partial
from sanic.request import Request
from sanic.response import HTTPResponse, StreamingHTTPResponse
from sanic.websocket import WebSocketConnection
from sanic.server import StreamBuffer

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

    def pause_writing(self):
        self._not_paused.clear()

    def resume_writing(self):
        self._not_paused.set()

    async def complete(self):
        self._not_paused.set()
        await self.transport.send(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )

    @property
    def is_complete(self):
        return self._complete.is_set()

    async def push_data(self, data):
        if not self.is_complete:
            await self.transport.send(
                {"type": "http.response.body", "body": data, "more_body": True}
            )

    async def drain(self):
        print("draining")
        await self._not_paused.wait()


class MockTransport:
    def __init__(
        self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self._protocol = None
        self.loop = None

    def get_protocol(self):
        if not self._protocol:
            self._protocol = MockProtocol(self, self.loop)
        return self._protocol

    def get_extra_info(self, info: str) -> Union[str, bool]:
        if info == "peername":
            return self.scope.get("server")
        elif info == "sslcontext":
            return self.scope.get("scheme") in ["https", "wss"]

    def get_websocket_connection(self) -> WebSocketConnection:
        return self._websocket_connection

    def create_websocket_connection(
        self, send: ASGISend, receive: ASGIReceive
    ) -> WebSocketConnection:
        self._websocket_connection = WebSocketConnection(send, receive)
        return self._websocket_connection

    def add_task(self):
        raise NotImplementedError

    async def send(self, data):
        print(">> sending. more:", data.get("more_body"))
        # TODO:
        # - Validation on data and that it is formatted properly and is valid
        await self._send(data)

    async def receive(self):
        return await self._receive()


class ASGIApp:
    def __init__(self) -> None:
        self.ws = None

    @classmethod
    async def create(
        cls, sanic_app, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> "ASGIApp":
        instance = cls()
        instance.sanic_app = sanic_app
        instance.transport = MockTransport(scope, receive, send)
        instance.transport.add_task = sanic_app.loop.create_task
        instance.transport.loop = sanic_app.loop

        url_bytes = scope.get("root_path", "") + scope["path"]
        url_bytes = url_bytes.encode("latin-1")
        url_bytes += scope["query_string"]
        headers = CIMultiDict(
            [
                (key.decode("latin-1"), value.decode("latin-1"))
                for key, value in scope.get("headers", [])
            ]
        )

        instance.do_stream = (
            True if headers.get("expect") == "100-continue" else False
        )

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

        instance.request = Request(
            url_bytes, headers, version, method, instance.transport, sanic_app
        )

        if sanic_app.is_request_stream:
            instance.request.stream = StreamBuffer()

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
            # self.sanic_app.loop.create_task(self.request.stream.put(chunk))

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

    async def stream_callback(self, response: HTTPResponse) -> None:
        """
        Write the response.
        """

        headers = [
            (str(name).encode("latin-1"), str(value).encode("latin-1"))
            for name, value in response.headers.items()
        ]

        if "content-length" not in response.headers and not isinstance(
            response, StreamingHTTPResponse
        ):
            headers += [
                (b"content-length", str(len(response.body)).encode("latin-1"))
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
