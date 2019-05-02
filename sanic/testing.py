from json import JSONDecodeError
from socket import socket

import requests_async as requests
import websockets

from sanic.exceptions import MethodNotSupported
from sanic.log import logger
from sanic.response import text


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
        **request_kwargs
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
            except BaseException:
                raise ValueError(
                    "Request and response object expected, got ({})".format(
                        results
                    )
                )
        else:
            try:
                return results[-1]
            except BaseException:
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
