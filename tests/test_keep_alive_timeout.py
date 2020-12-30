import asyncio

from asyncio import sleep as aio_sleep
from json import JSONDecodeError
from os import environ

import httpcore
import httpx
import pytest

from sanic import Sanic, server
from sanic.compat import OS_IS_WINDOWS
from sanic.response import text
from sanic.testing import HOST, SanicTestClient


CONFIG_FOR_TESTS = {"KEEP_ALIVE_TIMEOUT": 2, "KEEP_ALIVE": True}

PORT = 42101  # test_keep_alive_timeout_reuse doesn't work with random port

from httpcore._async.base import ConnectionState
from httpcore._async.connection import AsyncHTTPConnection
from httpcore._types import Origin


class ReusableSanicConnectionPool(httpcore.AsyncConnectionPool):
    last_reused_connection = None

    async def _get_connection_from_pool(self, *args, **kwargs):
        conn = await super()._get_connection_from_pool(*args, **kwargs)
        self.__class__.last_reused_connection = conn
        return conn


class ResusableSanicSession(httpx.AsyncClient):
    def __init__(self, *args, **kwargs) -> None:
        transport = ReusableSanicConnectionPool()
        super().__init__(transport=transport, *args, **kwargs)


class ReuseableSanicTestClient(SanicTestClient):
    def __init__(self, app, loop=None):
        super().__init__(app)
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._server = None
        self._tcp_connector = None
        self._session = None

    def get_new_session(self):
        return ResusableSanicSession()

    # Copied from SanicTestClient, but with some changes to reuse the
    # same loop for the same app.
    def _sanic_endpoint_test(
        self,
        method="get",
        uri="/",
        gather_request=True,
        debug=False,
        server_kwargs=None,
        *request_args,
        **request_kwargs,
    ):
        loop = self._loop
        results = [None, None]
        exceptions = []
        server_kwargs = server_kwargs or {"return_asyncio_server": True}
        if gather_request:

            def _collect_request(request):
                if results[0] is None:
                    results[0] = request

            self.app.request_middleware.appendleft(_collect_request)

        if uri.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = uri
        else:
            uri = uri if uri.startswith("/") else f"/{uri}"
            scheme = "http"
            url = f"{scheme}://{HOST}:{PORT}{uri}"

        @self.app.listener("after_server_start")
        async def _collect_response(loop):
            try:
                response = await self._local_request(
                    method, url, *request_args, **request_kwargs
                )
                results[-1] = response
            except Exception as e2:
                exceptions.append(e2)

        if self._server is not None:
            _server = self._server
        else:
            _server_co = self.app.create_server(
                host=HOST, debug=debug, port=PORT, **server_kwargs
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
            self.app.request_middleware.pop()
            try:
                request, response = results
                return request, response
            except Exception:
                raise ValueError(
                    f"Request and response object expected, got ({results})"
                )
        else:
            try:
                return results[-1]
            except Exception:
                raise ValueError(f"Request object expected, got ({results})")

    def kill_server(self):
        try:
            if self._server:
                self._server.close()
                self._loop.run_until_complete(self._server.wait_closed())
                self._server = None

            if self._session:
                self._loop.run_until_complete(self._session.aclose())
                self._session = None

        except Exception as e3:
            raise e3

    # Copied from SanicTestClient, but with some changes to reuse the
    # same TCPConnection and the sane ClientSession more than once.
    # Note, you cannot use the same session if you are in a _different_
    # loop, so the changes above are required too.
    async def _local_request(self, method, url, *args, **kwargs):
        raw_cookies = kwargs.pop("raw_cookies", None)
        request_keepalive = kwargs.pop(
            "request_keepalive", CONFIG_FOR_TESTS["KEEP_ALIVE_TIMEOUT"]
        )
        if not self._session:
            self._session = self.get_new_session()
        try:
            response = await getattr(self._session, method.lower())(
                url, timeout=request_keepalive, *args, **kwargs
            )
        except NameError:
            raise Exception(response.status_code)

        try:
            response.json = response.json()
        except (JSONDecodeError, UnicodeDecodeError):
            response.json = None

        response.body = await response.aread()
        response.status = response.status_code
        response.content_type = response.headers.get("content-type")

        if raw_cookies:
            response.raw_cookies = {}
            for cookie in response.cookies:
                response.raw_cookies[cookie.name] = cookie

        return response


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


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
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
        loop.run_until_complete(aio_sleep(1))
        request, response = client.get("/1")
        assert response.status == 200
        assert response.text == "OK"
        assert ReusableSanicConnectionPool.last_reused_connection
    finally:
        client.kill_server()


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_keep_alive_client_timeout():
    """If the server keep-alive timeout is longer than the client
    keep-alive timeout, client will try to create a new connection here."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = ReuseableSanicTestClient(keep_alive_app_client_timeout, loop)
        headers = {"Connection": "keep-alive"}
        request, response = client.get(
            "/1", headers=headers, request_keepalive=1
        )
        assert response.status == 200
        assert response.text == "OK"
        loop.run_until_complete(aio_sleep(2))
        exception = None
        request, response = client.get("/1", request_keepalive=1)
        assert ReusableSanicConnectionPool.last_reused_connection is None
    finally:
        client.kill_server()


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
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
        request, response = client.get(
            "/1", headers=headers, request_keepalive=60
        )
        assert response.status == 200
        assert response.text == "OK"
        loop.run_until_complete(aio_sleep(3))
        exception = None
        request, response = client.get("/1", request_keepalive=60)
        assert ReusableSanicConnectionPool.last_reused_connection is None
    finally:
        client.kill_server()
