import asyncio

from typing import cast

import httpcore
import httpx

from httpcore._async.base import (
    AsyncByteStream,
    AsyncHTTPTransport,
    ConnectionState,
    NewConnectionRequired,
)
from httpcore._async.connection import AsyncHTTPConnection
from httpcore._async.connection_pool import ResponseByteStream
from httpcore._exceptions import LocalProtocolError, UnsupportedProtocol
from httpcore._types import TimeoutDict
from httpcore._utils import url_to_origin

from sanic import Sanic
from sanic.response import text
from sanic.testing import SanicTestClient


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
