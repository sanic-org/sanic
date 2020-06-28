import asyncio

import httpx

from sanic import Sanic
from sanic.response import text
from sanic.testing import SanicTestClient


class DelayableHTTPConnection(httpx.dispatch.connection.HTTPConnection):
    def __init__(self, *args, **kwargs):
        self._request_delay = None
        if "request_delay" in kwargs:
            self._request_delay = kwargs.pop("request_delay")
        super().__init__(*args, **kwargs)

    async def send(self, request, timeout=None):

        if self.connection is None:
            self.connection = await self.connect(timeout=timeout)

        if self._request_delay:
            await asyncio.sleep(self._request_delay)

        response = await self.connection.send(request, timeout=timeout)

        return response


class DelayableSanicConnectionPool(
    httpx.dispatch.connection_pool.ConnectionPool
):
    def __init__(self, request_delay=None, *args, **kwargs):
        self._request_delay = request_delay
        super().__init__(*args, **kwargs)

    async def acquire_connection(self, origin, timeout=None):
        connection = self.pop_connection(origin)

        if connection is None:
            pool_timeout = None if timeout is None else timeout.pool_timeout

            await self.max_connections.acquire(timeout=pool_timeout)
            connection = DelayableHTTPConnection(
                origin,
                ssl=self.ssl,
                backend=self.backend,
                release_func=self.release_connection,
                uds=self.uds,
                request_delay=self._request_delay,
            )

        self.active_connections.add(connection)

        return connection


class DelayableSanicSession(httpx.AsyncClient):
    def __init__(self, request_delay=None, *args, **kwargs) -> None:
        dispatch = DelayableSanicConnectionPool(request_delay=request_delay)
        super().__init__(dispatch=dispatch, *args, **kwargs)


class DelayableSanicTestClient(SanicTestClient):
    def __init__(self, app, request_delay=None):
        super().__init__(app)
        self._request_delay = request_delay
        self._loop = None

    def get_new_session(self):
        return DelayableSanicSession(request_delay=self._request_delay)


request_timeout_default_app = Sanic("test_request_timeout_default")
request_no_timeout_app = Sanic("test_request_no_timeout")
request_timeout_default_app.config.REQUEST_TIMEOUT = 0.6
request_no_timeout_app.config.REQUEST_TIMEOUT = 0.6


@request_timeout_default_app.route("/1")
async def handler1(request):
    return text("OK")


@request_no_timeout_app.route("/1")
async def handler2(request):
    return text("OK")


@request_timeout_default_app.websocket("/ws1")
async def ws_handler1(request, ws):
    await ws.send("OK")


def test_default_server_error_request_timeout():
    client = DelayableSanicTestClient(request_timeout_default_app, 2)
    request, response = client.get("/1")
    assert response.status == 408
    assert "Request Timeout" in response.text


def test_default_server_error_request_dont_timeout():
    client = DelayableSanicTestClient(request_no_timeout_app, 0.2)
    request, response = client.get("/1")
    assert response.status == 200
    assert response.text == "OK"


def test_default_server_error_websocket_request_timeout():

    headers = {
        "Upgrade": "websocket",
        "Connection": "upgrade",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version": "13",
    }

    client = DelayableSanicTestClient(request_timeout_default_app, 2)
    request, response = client.get("/ws1", headers=headers)

    assert response.status == 408
    assert "Request Timeout" in response.text
