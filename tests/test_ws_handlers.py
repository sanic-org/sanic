from typing import Any, Callable, Coroutine

import pytest

from websockets.client import WebSocketClientProtocol

from sanic import Request, Sanic, Websocket


MimicClientType = Callable[
    [WebSocketClientProtocol], Coroutine[None, None, Any]
]


@pytest.fixture
def simple_ws_mimic_client():
    async def client_mimic(ws: WebSocketClientProtocol):
        await ws.send("test 1")
        await ws.recv()
        await ws.send("test 2")
        await ws.recv()

    return client_mimic


def test_ws_handler(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    @app.websocket("/ws")
    async def ws_echo_handler(request: Request, ws: Websocket):
        while True:
            msg = await ws.recv()
            await ws.send(msg)

    _, ws_proxy = app.test_client.websocket(
        "/ws", mimic=simple_ws_mimic_client
    )
    assert ws_proxy.client_sent == ["test 1", "test 2", ""]
    assert ws_proxy.client_received == ["test 1", "test 2"]


def test_ws_handler_async_for(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    @app.websocket("/ws")
    async def ws_echo_handler(request: Request, ws: Websocket):
        async for msg in ws:
            await ws.send(msg)

    _, ws_proxy = app.test_client.websocket(
        "/ws", mimic=simple_ws_mimic_client
    )
    assert ws_proxy.client_sent == ["test 1", "test 2", ""]
    assert ws_proxy.client_received == ["test 1", "test 2"]


def test_request_url(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    @app.websocket("/ws")
    async def ws_url_handler(request: Request, ws: Websocket):
        request.headers[
            "forwarded"
        ] = "for=[2001:db8::1];proto=https;host=example.com;by=proxy"

        await ws.recv()
        await ws.send(request.url)
        await ws.recv()
        await ws.send(request.url_for("ws_url_handler"))
        await ws.recv()

    for proxy in ["", "proxy", "servername"]:
        app.config.FORWARDED_SECRET = proxy
        app.config.SERVER_NAME = (
            "https://example.com" if proxy == "servername" else ""
        )
        _, ws_proxy = app.test_client.websocket(
            "/ws",
            mimic=simple_ws_mimic_client,
        )
        assert ws_proxy.client_sent == ["test 1", "test 2", ""]
        assert ws_proxy.client_received[0] == ws_proxy.client_received[1]
        if proxy:
            assert ws_proxy.client_received[0] == "wss://example.com/ws"
            assert ws_proxy.client_received[1] == "wss://example.com/ws"
        else:
            assert ws_proxy.client_received[0].startswith("ws://127.0.0.1")
            assert ws_proxy.client_received[1].startswith("ws://127.0.0.1")
