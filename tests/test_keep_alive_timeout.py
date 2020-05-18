import asyncio
import typing
from asyncio import sleep as aio_sleep
from json import JSONDecodeError
from socket import socket

import pytest

import httpx
from sanic import Sanic, server
from sanic.exceptions import MethodNotSupported
from sanic.response import text
from sanic_testing.testing import HOST, PORT, SanicTestClient

CONFIG_FOR_TESTS = {"KEEP_ALIVE_TIMEOUT": 2, "KEEP_ALIVE": True}


class ReusableSanicDispatch(httpx._dispatch.connection_pool.ConnectionPool):
    _old_conn = None
    _to_close = set()

    async def acquire_connection(self, origin, timeout):
        connection = self.pop_connection(origin)

        if connection is None:
            pool_timeout = None if timeout is None else timeout.pool_timeout

            await self.max_connections.acquire(timeout=pool_timeout)
            connection = httpx._dispatch.connection.HTTPConnection(
                origin,
                ssl=self.ssl,
                backend=self.backend,
                release_func=self.release_connection,
                uds=self.uds,
            )

        self.active_connections.add(connection)

        if self.__class__._old_conn is not None:
            if self.__class__._old_conn != connection:
                raise RuntimeError(
                    "We got a new connection, wanted the same one!"
                )
        self.__class__._old_conn = connection

        return connection

    async def close(self) -> None:
        # Mark for closing later
        connections = list(self.keepalive_connections)
        for connection in connections:
            self.__class__._to_close.add(connection)


class ReuseableSanicTestClient(SanicTestClient):
    def __init__(self, app, loop=None):
        super().__init__(app)
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._server = None
        # self._tcp_connector = None
        self._session = None
        self._dispatch = ReusableSanicDispatch(verify=False)

    def get_new_session(self, **kwargs):
        if not self._session:
            self._session = httpx.AsyncClient(verify=False, **kwargs)
        return self._session

    async def _local_request(self, method, url, *args, **kwargs):
        raw_cookies = kwargs.pop("raw_cookies", None)
        session_kwargs = kwargs.pop('session_kwargs', {})

        if method == "websocket":
            async with websockets.connect(url, *args, **kwargs) as websocket:
                websocket.opened = websocket.open
                return websocket
        else:
            async with self.get_new_session(**session_kwargs) as session:
                try:
                    response = await getattr(session, method.lower())(
                        url, *args, **kwargs
                    )
                except NameError:
                    raise Exception(response.status_code)

                response.body = await response.aread()
                response.status = response.status_code
                response.content_type = response.headers.get("content-type")

                # response can be decoded as json after response._content
                # is set by response.aread()
                try:
                    response.json = response.json()
                except (JSONDecodeError, UnicodeDecodeError):
                    response.json = None

                if raw_cookies:
                    response.raw_cookies = {}

                    for cookie in response.cookies.jar:
                        response.raw_cookies[cookie.name] = cookie

                return response

    def _sanic_endpoint_test(
        self,
        method="get",
        uri="/",
        gather_request=True,
        debug=False,
        server_kwargs=None,
        host=None,
        *request_args,
        **request_kwargs,
    ):
        loop = self._loop
        results = [None, None]
        server_kwargs = server_kwargs or {"return_asyncio_server": True}
        request_keepalive = request_kwargs.pop(
            "request_keepalive", CONFIG_FOR_TESTS["KEEP_ALIVE_TIMEOUT"]
        )
        request_kwargs.update(
            {"session_kwargs": {"timeout": request_keepalive, "dispatch": self._dispatch}})

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
            server_kwargs = dict(
                host=host or self.host, port=self.port, **server_kwargs,
            )
            host, port = host or self.host, self.port
        else:
            sock = socket()
            sock.bind((host or self.host, 0))
            server_kwargs = dict(sock=sock, **server_kwargs)
            host, port = sock.getsockname()
            self.port = port

        if uri.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = uri
        else:
            uri = uri if uri.startswith("/") else f"/{uri}"
            scheme = "ws" if method == "websocket" else "http"
            url = f"{scheme}://{host}:{port}{uri}"
        # Tests construct URLs using PORT = None, which means random port not
        # known until this function is called, so fix that here
        url = url.replace(":None/", f":{port}/")

        @self.app.listener("after_server_start")
        async def _collect_response(*args):
            try:
                response = await self._local_request(
                    method, url, *request_args, **request_kwargs
                )
                results[-1] = response
            except Exception as e:
                # logger.exception("Exception")
                exceptions.append(e)

        if self._server is not None:
            _server = self._server
        else:
            _server_co = self.app.create_server(
                **server_kwargs
            )

            server.trigger_events(
                self.app.listeners["before_server_start"], loop
            )

            try:
                loop._stopping = False
                _server = loop.run_until_complete(_server_co)
            except Exception as e1:
                raise e1
            self._server = _server

        server.trigger_events(self.app.listeners["after_server_start"], loop)
        self.app.listeners["after_server_start"].pop()

        if exceptions:
            raise ValueError(f"Exception during request: {exceptions}")

        if gather_request:
            try:
                request, response = results
                return request, response
            except BaseException:  # noqa
                raise ValueError(
                    f"Request and response object expected, got ({results})"
                )
        else:
            try:
                return results[-1]
            except BaseException:  # noqa
                raise ValueError(f"Request object expected, got ({results})")

    def kill_server(self):
        try:
            if self._dispatch:
                self._dispatch.keepalive_connections.clear()
                connections = list(self._dispatch.keepalive_connections)
                for connection in connections:
                    self._dispatch.max_connections.release()
                    self._loop.run_until_complete(connection.close())
            if self._server:
                self._server.close()
                self._loop.run_until_complete(self._server.wait_closed())
                self._server = None

            if self._session:
                self._loop.run_until_complete(self._session.aclose())
                self._session = None

        except Exception as e:
            raise e


keep_alive_timeout_app_reuse = Sanic("test_ka_timeout_reuse")
keep_alive_app_client_timeout = Sanic("test_ka_client_timeout")
keep_alive_app_server_timeout = Sanic("test_ka_server_timeout")

keep_alive_timeout_app_reuse.config.update(CONFIG_FOR_TESTS)
keep_alive_app_client_timeout.config.update(CONFIG_FOR_TESTS)
keep_alive_app_server_timeout.config.update(CONFIG_FOR_TESTS)


@keep_alive_timeout_app_reuse.route("/1")
async def handler1(request):
    return text("OK")


@keep_alive_app_client_timeout.route("/1")
async def handler2(request):
    return text("OK")


@keep_alive_app_server_timeout.route("/1")
async def handler3(request):
    return text("OK")


def test_keep_alive_timeout_reuse():
    """If the server keep-alive timeout and client keep-alive timeout are
     both longer than the delay, the client _and_ server will successfully
     reuse the existing connection."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = ReuseableSanicTestClient(keep_alive_timeout_app_reuse, loop)
        headers = {"Connection": "keep-alive"}
        request, response = client.get("/1", headers=headers)
        assert response.status == 200
        assert response.text == "OK"
        # loop.run_until_complete(aio_sleep(1))
        from time import sleep
        sleep(1)
        request, response = client.get("/1")
        assert response.status == 200
        assert response.text == "OK"
    finally:
        client.kill_server()


def test_keep_alive_client_timeout():
    """If the server keep-alive timeout is longer than the client
    keep-alive timeout, client will try to create a new connection here."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = ReuseableSanicTestClient(keep_alive_app_client_timeout, loop)
        headers = {"Connection": "keep-alive"}
        try:
            request, response = client.get(
                "/1", headers=headers, request_keepalive=1
            )
            assert response.status == 200
            assert response.text == "OK"
            # await aio_sleep(2)
            from time import sleep
            sleep(2)
            exception = None
            request, response = client.get("/1", request_keepalive=1)
        except ValueError as e:
            exception = e
        assert exception is not None
        assert isinstance(exception, ValueError)
        assert "got a new connection" in exception.args[0]
    finally:
        client.kill_server()


def test_keep_alive_server_timeout():
    """If the client keep-alive timeout is longer than the server
    keep-alive timeout, the client will either a 'Connection reset' error
    _or_ a new connection. Depending on how the event-loop handles the
    broken server connection."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = ReuseableSanicTestClient(keep_alive_app_server_timeout, loop)
        headers = {"Connection": "keep-alive"}
        try:
            request, response = client.get(
                "/1", headers=headers, request_keepalive=60
            )
            assert response.status == 200
            assert response.text == "OK"
            # await aio_sleep(3)
            from time import sleep
            sleep(3)
            exception = None
            request, response = client.get("/1", request_keepalive=60)
        except ValueError as e:
            exception = e
        assert exception is not None
        assert isinstance(exception, ValueError)
        assert (
            "Connection reset" in exception.args[0]
            or "got a new connection" in exception.args[0]
        )
    finally:
        client.kill_server()
