import asyncio

import httpcore
import httpx
import pytest

from sanic_testing.testing import SanicTestClient

from sanic import Sanic
from sanic.response import text


class DelayableHTTPConnection(httpcore._async.connection.AsyncHTTPConnection):
    async def arequest(self, *args, **kwargs):
        await asyncio.sleep(2)
        return await super().arequest(*args, **kwargs)

    async def _open_socket(self, *args, **kwargs):
        retval = await super()._open_socket(*args, **kwargs)
        if self._request_delay:
            await asyncio.sleep(self._request_delay)
        return retval


class DelayableSanicConnectionPool(httpcore.AsyncConnectionPool):
    def __init__(self, request_delay=None, *args, **kwargs):
        self._request_delay = request_delay
        super().__init__(*args, **kwargs)

    async def _add_to_pool(self, connection, timeout):
        connection.__class__ = DelayableHTTPConnection
        connection._request_delay = self._request_delay
        await super()._add_to_pool(connection, timeout)


class DelayableSanicSession(httpx.AsyncClient):
    def __init__(self, request_delay=None, *args, **kwargs) -> None:
        transport = DelayableSanicConnectionPool(request_delay=request_delay)
        super().__init__(transport=transport, *args, **kwargs)


class DelayableSanicTestClient(SanicTestClient):
    def __init__(self, app, request_delay=None):
        super().__init__(app)
        self._request_delay = request_delay
        self._loop = None

    def get_new_session(self):
        return DelayableSanicSession(request_delay=self._request_delay)


@pytest.fixture
def request_no_timeout_app():
    app = Sanic("test_request_no_timeout")
    app.config.REQUEST_TIMEOUT = 0.6

    @app.route("/1")
    async def handler2(request):
        return text("OK")

    return app


@pytest.fixture
def request_timeout_default_app():
    app = Sanic("test_request_timeout_default")
    app.config.REQUEST_TIMEOUT = 0.6

    @app.route("/1")
    async def handler1(request):
        return text("OK")

    @app.websocket("/ws1")
    async def ws_handler1(request, ws):
        await ws.send("OK")

    return app


def test_default_server_error_request_timeout(request_timeout_default_app):
    client = DelayableSanicTestClient(request_timeout_default_app, 2)
    _, response = client.get("/1")
    assert response.status == 408
    assert "Request Timeout" in response.text


def test_default_server_error_request_dont_timeout(request_no_timeout_app):
    client = DelayableSanicTestClient(request_no_timeout_app, 0.2)
    _, response = client.get("/1")
    assert response.status == 200
    assert response.text == "OK"


def test_default_server_error_websocket_request_timeout(
    request_timeout_default_app,
):

    headers = {
        "Upgrade": "websocket",
        "Connection": "upgrade",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version": "13",
    }

    client = DelayableSanicTestClient(request_timeout_default_app, 2)
    _, response = client.get("/ws1", headers=headers)

    assert response.status == 408
    assert "Request Timeout" in response.text
