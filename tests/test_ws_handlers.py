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
