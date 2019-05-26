from typing import Any, Awaitable, Callable, MutableMapping, Union

from multidict import CIMultiDict

from sanic.request import Request
from sanic.response import HTTPResponse, StreamingHTTPResponse
from sanic.websocket import WebSocketConnection
from sanic.server import StreamBuffer

ASGIScope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]


class MockTransport:
    def __init__(self, scope: ASGIScope) -> None:
        self.scope = scope

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


class ASGIApp:
    def __init__(self) -> None:
        self.ws = None

    @classmethod
    async def create(
        cls, sanic_app, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> "ASGIApp":
        instance = cls()
        instance.sanic_app = sanic_app
        instance.receive = receive
        instance.send = send

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

        transport = MockTransport(scope)

        if scope["type"] == "http":
            version = scope["http_version"]
            method = scope["method"]
        elif scope["type"] == "websocket":
            version = "1.1"
            method = "GET"

            instance.ws = transport.create_websocket_connection(send, receive)
            await instance.ws.accept()
        else:
            pass
            # TODO:
            # - close connection

        instance.request = Request(
            url_bytes, headers, version, method, transport, sanic_app
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
            message = await self.receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        return body

    async def stream_body(self) -> None:
        """
        Read and stream the body in chunks from an incoming ASGI message.
        """
        more_body = True

        while more_body:
            message = await self.receive()
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
        if isinstance(response, StreamingHTTPResponse):
            raise NotImplementedError("Not supported")

        headers = [
            (str(name).encode("latin-1"), str(value).encode("latin-1"))
            for name, value in response.headers.items()
        ]
        if "content-length" not in response.headers:
            headers += [
                (b"content-length", str(len(response.body)).encode("latin-1"))
            ]

        await self.send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": headers,
            }
        )
        await self.send(
            {
                "type": "http.response.body",
                "body": response.body,
                "more_body": False,
            }
        )
