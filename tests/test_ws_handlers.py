from typing import Any, Callable, Coroutine

import pytest

from websockets.client import WebSocketClientProtocol

from sanic import Request, Sanic, Websocket


MimicClientType = Callable[[WebSocketClientProtocol], Coroutine[None, None, Any]]


@pytest.fixture
def simple_ws_mimic_client():
    async def client_mimic(ws: WebSocketClientProtocol):
        await ws.send("test 1")
        await ws.recv()
        await ws.send("test 2")
        await ws.recv()

    return client_mimic


def signalapp(app):
    @app.signal("websocket.handler.before")
    async def ws_before(request: Request, websocket: Websocket):
        app.ctx.seq.append("before")
        print("before")
        await websocket.send("before: " + await websocket.recv())
        print("before2")

    @app.signal("websocket.handler.after")
    async def ws_after(request: Request, websocket: Websocket):
        app.ctx.seq.append("after")
        await websocket.send("after: " + await websocket.recv())
        await websocket.recv()

    @app.signal("websocket.handler.exception")
    async def ws_exception(
        request: Request, websocket: Websocket, exception: Exception
    ):
        app.ctx.seq.append("exception")
        await websocket.send(f"exception: {exception}")
        await websocket.recv()

    @app.websocket("/ws")
    async def ws_handler(request: Request, ws: Websocket):
        app.ctx.seq.append("ws")

    @app.websocket("/wserror")
    async def ws_error(request: Request, ws: Websocket):
        print("wserr")
        app.ctx.seq.append("wserror")
        raise Exception(await ws.recv())
        print("wserr2")


def test_ws_handler(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    @app.websocket("/ws")
    async def ws_echo_handler(request: Request, ws: Websocket):
        while True:
            msg = await ws.recv()
            await ws.send(msg)

    _, ws_proxy = app.test_client.websocket("/ws", mimic=simple_ws_mimic_client)
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

    _, ws_proxy = app.test_client.websocket("/ws", mimic=simple_ws_mimic_client)
    assert ws_proxy.client_sent == ["test 1", "test 2", ""]
    assert ws_proxy.client_received == ["test 1", "test 2"]


@pytest.mark.parametrize("proxy", ["", "proxy", "servername"])
def test_request_url(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
    proxy: str,
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

    app.config.FORWARDED_SECRET = proxy
    app.config.SERVER_NAME = "https://example.com" if proxy == "servername" else ""
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


def test_ws_signals(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    signalapp(app)

    app.ctx.seq = []
    _, ws_proxy = app.test_client.websocket("/ws", mimic=simple_ws_mimic_client)
    assert ws_proxy.client_received == ["before: test 1", "after: test 2"]
    assert app.ctx.seq == ["before", "ws", "after"]


def test_ws_signals_exception(
    app: Sanic,
    simple_ws_mimic_client: MimicClientType,
):
    signalapp(app)

    app.ctx.seq = []
    _, ws_proxy = app.test_client.websocket("/wserror", mimic=simple_ws_mimic_client)
    assert ws_proxy.client_received == ["before: test 1", "exception: test 2"]
    assert app.ctx.seq == ["before", "wserror", "exception"]
