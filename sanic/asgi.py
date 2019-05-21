from sanic.request import Request
from multidict import CIMultiDict
from sanic.response import StreamingHTTPResponse


class MockTransport:
    def __init__(self, scope):
        self.scope = scope

    def get_extra_info(self, info):
        if info == "peername":
            return self.scope.get("server")
        elif info == "sslcontext":
            return self.scope.get("scheme") in ["https", "wss"]


class ASGIApp:
    def __init__(self, sanic_app, scope, receive, send):
        self.sanic_app = sanic_app
        self.receive = receive
        self.send = send
        url_bytes = scope.get("root_path", "") + scope["path"]
        url_bytes = url_bytes.encode("latin-1")
        url_bytes += scope["query_string"]
        headers = CIMultiDict(
            [
                (key.decode("latin-1"), value.decode("latin-1"))
                for key, value in scope.get("headers", [])
            ]
        )
        version = scope["http_version"]
        method = scope["method"]
        self.request = Request(
            url_bytes,
            headers,
            version,
            method,
            MockTransport(scope),
            sanic_app,
        )

    async def read_body(self):
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

    async def __call__(self):
        """
        Handle the incoming request.
        """
        self.request.body = await self.read_body()
        handler = self.sanic_app.handle_request
        await handler(self.request, None, self.stream_callback)

    async def stream_callback(self, response):
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
