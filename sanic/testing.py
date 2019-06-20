import asyncio
import types
import typing

from json import JSONDecodeError
from socket import socket
from urllib.parse import unquote, urlsplit

import httpcore
import requests_async as requests
import websockets

from sanic.asgi import ASGIApp
from sanic.exceptions import MethodNotSupported
from sanic.log import logger
from sanic.response import text


ASGI_HOST = "mockserver"
HOST = "127.0.0.1"
PORT = 42101


class SanicTestClient:
    def __init__(self, app, port=PORT):
        """Use port=None to bind to a random port"""
        self.app = app
        self.port = port

    def get_new_session(self):
        return requests.Session()

    async def _local_request(self, method, url, *args, **kwargs):
        logger.info(url)
        raw_cookies = kwargs.pop("raw_cookies", None)

        if method == "websocket":
            async with websockets.connect(url, *args, **kwargs) as websocket:
                websocket.opened = websocket.open
                return websocket
        else:
            async with self.get_new_session() as session:

                try:
                    response = await getattr(session, method.lower())(
                        url, verify=False, *args, **kwargs
                    )
                except NameError:
                    raise Exception(response.status_code)

                try:
                    response.json = response.json()
                except (JSONDecodeError, UnicodeDecodeError):
                    response.json = None

                response.body = await response.read()
                response.status = response.status_code
                response.content_type = response.headers.get("content-type")

                if raw_cookies:
                    response.raw_cookies = {}
                    for cookie in response.cookies:
                        response.raw_cookies[cookie.name] = cookie

                return response

    def _sanic_endpoint_test(
        self,
        method="get",
        uri="/",
        gather_request=True,
        debug=False,
        server_kwargs={"auto_reload": False},
        *request_args,
        **request_kwargs,
    ):
        results = [None, None]
        exceptions = []

        if gather_request:

            def _collect_request(request):
                if results[0] is None:
                    results[0] = request

            self.app.request_middleware.appendleft(_collect_request)

        @self.app.exception(MethodNotSupported)
        async def error_handler(request, exception):
            if request.method in ["HEAD", "PATCH", "PUT", "DELETE"]:
                return text(
                    "", exception.status_code, headers=exception.headers
                )
            else:
                return self.app.error_handler.default(request, exception)

        if self.port:
            server_kwargs = dict(host=HOST, port=self.port, **server_kwargs)
            host, port = HOST, self.port
        else:
            sock = socket()
            sock.bind((HOST, 0))
            server_kwargs = dict(sock=sock, **server_kwargs)
            host, port = sock.getsockname()

        if uri.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = uri
        else:
            uri = uri if uri.startswith("/") else "/{uri}".format(uri=uri)
            scheme = "ws" if method == "websocket" else "http"
            url = "{scheme}://{host}:{port}{uri}".format(
                scheme=scheme, host=host, port=port, uri=uri
            )

        @self.app.listener("after_server_start")
        async def _collect_response(sanic, loop):
            try:
                response = await self._local_request(
                    method, url, *request_args, **request_kwargs
                )
                results[-1] = response
            except Exception as e:
                logger.exception("Exception")
                exceptions.append(e)
            self.app.stop()

        self.app.run(debug=debug, **server_kwargs)
        self.app.listeners["after_server_start"].pop()

        if exceptions:
            raise ValueError("Exception during request: {}".format(exceptions))

        if gather_request:
            try:
                request, response = results
                return request, response
            except BaseException:  # noqa
                raise ValueError(
                    "Request and response object expected, got ({})".format(
                        results
                    )
                )
        else:
            try:
                return results[-1]
            except BaseException:  # noqa
                raise ValueError(
                    "Request object expected, got ({})".format(results)
                )

    def get(self, *args, **kwargs):
        return self._sanic_endpoint_test("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._sanic_endpoint_test("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._sanic_endpoint_test("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._sanic_endpoint_test("delete", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._sanic_endpoint_test("patch", *args, **kwargs)

    def options(self, *args, **kwargs):
        return self._sanic_endpoint_test("options", *args, **kwargs)

    def head(self, *args, **kwargs):
        return self._sanic_endpoint_test("head", *args, **kwargs)

    def websocket(self, *args, **kwargs):
        return self._sanic_endpoint_test("websocket", *args, **kwargs)


class SanicASGIAdapter(requests.asgi.ASGIAdapter):  # noqa
    async def send(  # type: ignore
        self,
        request: requests.PreparedRequest,
        gather_return: bool = False,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> requests.Response:
        """This method is taken MOSTLY verbatim from requests-asyn. The
        difference is the capturing of a response on the ASGI call and then
        returning it on the response object. This is implemented to achieve:

        request, response = await app.asgi_client.get("/")

        You can see the original code here:
        https://github.com/encode/requests-async/blob/614f40f77f19e6c6da8a212ae799107b0384dbf9/requests_async/asgi.py#L51"""  # noqa
        scheme, netloc, path, query, fragment = urlsplit(
            request.url
        )  # type: ignore

        default_port = {"http": 80, "ws": 80, "https": 443, "wss": 443}[scheme]

        if ":" in netloc:
            host, port_string = netloc.split(":", 1)
            port = int(port_string)
        else:
            host = netloc
            port = default_port

        # Include the 'host' header.
        if "host" in request.headers:
            headers = []  # type: typing.List[typing.Tuple[bytes, bytes]]
        elif port == default_port:
            headers = [(b"host", host.encode())]
        else:
            headers = [(b"host", (f"{host}:{port}").encode())]

        # Include other request headers.
        headers += [
            (key.lower().encode(), value.encode())
            for key, value in request.headers.items()
        ]

        no_response = False
        if scheme in {"ws", "wss"}:
            subprotocol = request.headers.get("sec-websocket-protocol", None)
            if subprotocol is None:
                subprotocols = []  # type: typing.Sequence[str]
            else:
                subprotocols = [
                    value.strip() for value in subprotocol.split(",")
                ]

            scope = {
                "type": "websocket",
                "path": unquote(path),
                "root_path": "",
                "scheme": scheme,
                "query_string": query.encode(),
                "headers": headers,
                "client": ["testclient", 50000],
                "server": [host, port],
                "subprotocols": subprotocols,
            }
            no_response = True

        else:
            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": request.method,
                "path": unquote(path),
                "root_path": "",
                "scheme": scheme,
                "query_string": query.encode(),
                "headers": headers,
                "client": ["testclient", 50000],
                "server": [host, port],
                "extensions": {"http.response.template": {}},
            }

        async def receive():
            nonlocal request_complete, response_complete

            if request_complete:
                while not response_complete:
                    await asyncio.sleep(0.0001)
                return {"type": "http.disconnect"}

            body = request.body
            if isinstance(body, str):
                body_bytes = body.encode("utf-8")  # type: bytes
            elif body is None:
                body_bytes = b""
            elif isinstance(body, types.GeneratorType):
                try:
                    chunk = body.send(None)
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    return {
                        "type": "http.request",
                        "body": chunk,
                        "more_body": True,
                    }
                except StopIteration:
                    request_complete = True
                    return {"type": "http.request", "body": b""}
            else:
                body_bytes = body

            request_complete = True
            return {"type": "http.request", "body": body_bytes}

        async def send(message) -> None:
            nonlocal raw_kwargs, response_started, response_complete, template, context  # noqa

            if message["type"] == "http.response.start":
                assert (
                    not response_started
                ), 'Received multiple "http.response.start" messages.'
                raw_kwargs["status_code"] = message["status"]
                raw_kwargs["headers"] = message["headers"]
                response_started = True
            elif message["type"] == "http.response.body":
                assert response_started, (
                    'Received "http.response.body" '
                    'without "http.response.start".'
                )
                assert (
                    not response_complete
                ), 'Received "http.response.body" after response completed.'
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                if request.method != "HEAD":
                    raw_kwargs["content"] += body
                if not more_body:
                    response_complete = True
            elif message["type"] == "http.response.template":
                template = message["template"]
                context = message["context"]

        request_complete = False
        response_started = False
        response_complete = False
        raw_kwargs = {"content": b""}  # type: typing.Dict[str, typing.Any]
        template = None
        context = None
        return_value = None

        try:
            return_value = await self.app(scope, receive, send)
        except BaseException as exc:
            if not self.suppress_exceptions:
                raise exc from None

        if no_response:
            response_started = True
            raw_kwargs = {"status_code": 204, "headers": []}

        if not self.suppress_exceptions:
            assert response_started, "TestClient did not receive any response."
        elif not response_started:
            raw_kwargs = {"status_code": 500, "headers": []}

        raw = httpcore.Response(**raw_kwargs)
        response = self.build_response(request, raw)
        if template is not None:
            response.template = template
            response.context = context

        if gather_return:
            response.return_value = return_value
        return response


class TestASGIApp(ASGIApp):
    async def __call__(self):
        await super().__call__()
        return self.request


async def app_call_with_return(self, scope, receive, send):
    asgi_app = await TestASGIApp.create(self, scope, receive, send)
    return await asgi_app()


class SanicASGITestClient(requests.ASGISession):
    def __init__(
        self,
        app,
        base_url: str = "http://{}".format(ASGI_HOST),
        suppress_exceptions: bool = False,
    ) -> None:
        app.__class__.__call__ = app_call_with_return
        app.asgi = True
        super().__init__(app)

        adapter = SanicASGIAdapter(
            app, suppress_exceptions=suppress_exceptions
        )
        self.mount("http://", adapter)
        self.mount("https://", adapter)
        self.mount("ws://", adapter)
        self.mount("wss://", adapter)
        self.headers.update({"user-agent": "testclient"})
        self.app = app
        self.base_url = base_url

    async def request(self, method, url, gather_request=True, *args, **kwargs):

        self.gather_request = gather_request
        response = await super().request(method, url, *args, **kwargs)
        response.status = response.status_code
        response.body = response.content
        response.content_type = response.headers.get("content-type")

        if hasattr(response, "return_value"):
            request = response.return_value
            del response.return_value
            return request, response

        return response

    def merge_environment_settings(self, *args, **kwargs):
        settings = super().merge_environment_settings(*args, **kwargs)
        settings.update({"gather_return": self.gather_request})
        return settings

    async def websocket(self, uri, subprotocols=None, *args, **kwargs):
        if uri.startswith(("ws:", "wss:")):
            url = uri
        else:
            uri = uri if uri.startswith("/") else "/{uri}".format(uri=uri)
            url = "ws://testserver{uri}".format(uri=uri)

            headers = kwargs.get("headers", {})
            headers.setdefault("connection", "upgrade")
            headers.setdefault("sec-websocket-key", "testserver==")
            headers.setdefault("sec-websocket-version", "13")
            if subprotocols is not None:
                headers.setdefault(
                    "sec-websocket-protocol", ", ".join(subprotocols)
                )
            kwargs["headers"] = headers

            return await self.request("websocket", url, **kwargs)
