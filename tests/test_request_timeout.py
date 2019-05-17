import asyncio

import httpcore
import requests_async as requests

from sanic import Sanic
from sanic.response import text
from sanic.testing import SanicTestClient


class DelayableSanicConnectionPool(httpcore.ConnectionPool):
    def __init__(self, request_delay=None, *args, **kwargs):
        self._request_delay = request_delay
        super().__init__(*args, **kwargs)

    async def send(
        self,
        request,
        stream=False,
        ssl=None,
        timeout=None,
    ):
        connection = await self.acquire_connection(request.url.origin)
        if connection.h11_connection is None and connection.h2_connection is None:
            await connection.connect(ssl=ssl, timeout=timeout)
        if self._request_delay:
            await asyncio.sleep(self._request_delay)
        try:
            response = await connection.send(
                request, stream=stream, ssl=ssl, timeout=timeout
            )
        except BaseException as exc:
            self.active_connections.remove(connection)
            self.max_connections.release()
            raise exc
        return response


class DelayableSanicAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, request_delay=None):
        self.pool = DelayableSanicConnectionPool(request_delay=request_delay)


class DelayableSanicSession(requests.Session):
    def __init__(self, request_delay=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        adapter = DelayableSanicAdapter(request_delay=request_delay)
        self.mount("http://", adapter)
        self.mount("https://", adapter)


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
    assert response.text == "Error: Request Timeout"


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
    assert response.text == "Error: Request Timeout"
