import asyncio
import logging

from collections import deque, namedtuple

import pytest
import uvicorn

from sanic import Sanic
from sanic.application.state import Mode
from sanic.asgi import MockTransport
from sanic.exceptions import BadRequest, Forbidden, ServiceUnavailable
from sanic.request import Request
from sanic.response import json, text
from sanic.server.websockets.connection import WebSocketConnection
from sanic.signals import RESERVED_NAMESPACES


@pytest.fixture
def message_stack():
    return deque()


@pytest.fixture
def receive(message_stack):
    async def _receive():
        return message_stack.popleft()

    return _receive


@pytest.fixture
def send(message_stack):
    async def _send(message):
        message_stack.append(message)

    return _send


@pytest.fixture
def transport(message_stack, receive, send):
    return MockTransport({}, receive, send)


@pytest.fixture
def protocol(transport):
    return transport.get_protocol()


def test_listeners_triggered(caplog):
    app = Sanic("app")
    before_server_start = False
    after_server_start = False
    before_server_stop = False
    after_server_stop = False

    @app.listener("before_server_start")
    def do_before_server_start(*args, **kwargs):
        nonlocal before_server_start
        before_server_start = True

    @app.listener("after_server_start")
    def do_after_server_start(*args, **kwargs):
        nonlocal after_server_start
        after_server_start = True

    @app.listener("before_server_stop")
    def do_before_server_stop(*args, **kwargs):
        nonlocal before_server_stop
        before_server_stop = True

    @app.listener("after_server_stop")
    def do_after_server_stop(*args, **kwargs):
        nonlocal after_server_stop
        after_server_stop = True

    @app.route("/")
    def handler(request):
        return text("...")

    class CustomServer(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(app=app, loop="asyncio", limit_max_requests=0)
    server = CustomServer(config=config)

    start_message = (
        'You have set a listener for "before_server_start" in ASGI mode. '
        "It will be executed as early as possible, but not before the ASGI "
        "server is started."
    )
    stop_message = (
        'You have set a listener for "after_server_stop" in ASGI mode. '
        "It will be executed as late as possible, but not after the ASGI "
        "server is stopped."
    )

    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) not in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) not in caplog.record_tuples

    all_tasks = asyncio.all_tasks(asyncio.get_event_loop())
    for task in all_tasks:
        task.cancel()

    assert before_server_start
    assert after_server_start
    assert before_server_stop
    assert after_server_stop

    app.state.mode = Mode.DEBUG
    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) not in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) not in caplog.record_tuples

    app.state.verbosity = 2
    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) in caplog.record_tuples


def test_listeners_triggered_async(app, caplog):
    before_server_start = False
    after_server_start = False
    before_server_stop = False
    after_server_stop = False

    @app.listener("before_server_start")
    async def do_before_server_start(*args, **kwargs):
        nonlocal before_server_start
        before_server_start = True

    @app.listener("after_server_start")
    async def do_after_server_start(*args, **kwargs):
        nonlocal after_server_start
        after_server_start = True

    @app.listener("before_server_stop")
    async def do_before_server_stop(*args, **kwargs):
        nonlocal before_server_stop
        before_server_stop = True

    @app.listener("after_server_stop")
    async def do_after_server_stop(*args, **kwargs):
        nonlocal after_server_stop
        after_server_stop = True

    @app.route("/")
    def handler(request):
        return text("...")

    class CustomServer(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(app=app, loop="asyncio", limit_max_requests=0)
    server = CustomServer(config=config)

    start_message = (
        'You have set a listener for "before_server_start" in ASGI mode. '
        "It will be executed as early as possible, but not before the ASGI "
        "server is started."
    )
    stop_message = (
        'You have set a listener for "after_server_stop" in ASGI mode. '
        "It will be executed as late as possible, but not after the ASGI "
        "server is stopped."
    )

    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) not in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) not in caplog.record_tuples

    all_tasks = asyncio.all_tasks(asyncio.get_event_loop())
    for task in all_tasks:
        task.cancel()

    assert before_server_start
    assert after_server_start
    assert before_server_stop
    assert after_server_stop

    app.state.mode = Mode.DEBUG
    app.state.verbosity = 0
    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) not in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) not in caplog.record_tuples

    app.state.verbosity = 2
    with caplog.at_level(logging.DEBUG):
        server.run()

    assert (
        "sanic.root",
        logging.DEBUG,
        start_message,
    ) in caplog.record_tuples
    assert (
        "sanic.root",
        logging.DEBUG,
        stop_message,
    ) in caplog.record_tuples


def test_non_default_uvloop_config_raises_warning(app):
    app.config.USE_UVLOOP = True

    class CustomServer(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(app=app, loop="asyncio", limit_max_requests=0)
    server = CustomServer(config=config)

    with pytest.warns(UserWarning) as records:
        server.run()

    all_tasks = asyncio.all_tasks(asyncio.get_event_loop())
    for task in all_tasks:
        task.cancel()

    msg = ""
    for record in records:
        _msg = str(record.message)
        if _msg.startswith("You have set the USE_UVLOOP configuration"):
            msg = _msg
            break

    assert msg == (
        "You have set the USE_UVLOOP configuration option, but Sanic "
        "cannot control the event loop when running in ASGI mode."
        "This option will be ignored."
    )


@pytest.mark.asyncio
async def test_mockprotocol_events(protocol):
    assert protocol._not_paused.is_set()
    protocol.pause_writing()
    assert not protocol._not_paused.is_set()
    protocol.resume_writing()
    assert protocol._not_paused.is_set()


@pytest.mark.asyncio
async def test_protocol_push_data(protocol, message_stack):
    text = b"hello"

    await protocol.push_data(text)
    await protocol.complete()

    assert len(message_stack) == 2

    message = message_stack.popleft()
    assert message["type"] == "http.response.body"
    assert message["more_body"]
    assert message["body"] == text

    message = message_stack.popleft()
    assert message["type"] == "http.response.body"
    assert not message["more_body"]
    assert message["body"] == b""


@pytest.mark.asyncio
async def test_websocket_send(send, receive, message_stack):
    text_string = "hello"
    text_bytes = b"hello"

    ws = WebSocketConnection(send, receive)
    await ws.send(text_string)
    await ws.send(text_bytes)

    assert len(message_stack) == 2

    message = message_stack.popleft()
    assert message["type"] == "websocket.send"
    assert message["text"] == text_string
    assert "bytes" not in message

    message = message_stack.popleft()
    assert message["type"] == "websocket.send"
    assert message["bytes"] == text_bytes
    assert "text" not in message


@pytest.mark.asyncio
async def test_websocket_receive(send, receive, message_stack):
    msg = {"text": "hello", "type": "websocket.receive"}
    message_stack.append(msg)

    ws = WebSocketConnection(send, receive)
    text = await ws.receive()

    assert text == msg["text"]


@pytest.mark.asyncio
async def test_websocket_accept_with_no_subprotocols(
    send, receive, message_stack
):
    ws = WebSocketConnection(send, receive)
    await ws.accept()

    assert len(message_stack) == 1

    message = message_stack.popleft()
    assert message["type"] == "websocket.accept"
    assert message["subprotocol"] is None
    assert "bytes" not in message


@pytest.mark.asyncio
async def test_websocket_accept_with_subprotocol(send, receive, message_stack):
    subprotocols = ["graphql-ws"]

    ws = WebSocketConnection(send, receive, subprotocols)
    await ws.accept(subprotocols)

    assert len(message_stack) == 1

    message = message_stack.popleft()
    assert message["type"] == "websocket.accept"
    assert message["subprotocol"] == "graphql-ws"
    assert "bytes" not in message


@pytest.mark.asyncio
async def test_websocket_accept_with_multiple_subprotocols(
    send, receive, message_stack
):
    subprotocols = ["graphql-ws", "hello", "world"]

    ws = WebSocketConnection(send, receive, subprotocols)
    await ws.accept(["hello", "world"])

    assert len(message_stack) == 1

    message = message_stack.popleft()
    assert message["type"] == "websocket.accept"
    assert message["subprotocol"] == "hello"
    assert "bytes" not in message


def test_improper_websocket_connection(transport, send, receive):
    with pytest.raises(BadRequest):
        transport.get_websocket_connection()

    transport.create_websocket_connection(send, receive)
    connection = transport.get_websocket_connection()
    assert isinstance(connection, WebSocketConnection)


@pytest.mark.asyncio
async def test_request_class_regular(app):
    @app.get("/regular")
    def regular_request(request):
        return text(request.__class__.__name__)

    _, response = await app.asgi_client.get("/regular")
    assert response.body == b"Request"


@pytest.mark.asyncio
async def test_request_class_custom():
    class MyCustomRequest(Request):
        pass

    app = Sanic(name="Test", request_class=MyCustomRequest)

    @app.get("/custom")
    def custom_request(request):
        return text(request.__class__.__name__)

    _, response = await app.asgi_client.get("/custom")
    assert response.body == b"MyCustomRequest"


@pytest.mark.asyncio
async def test_cookie_customization(app):
    @app.get("/cookie")
    def get_cookie(request):
        response = text("There's a cookie up in this response")
        response.cookies["test"] = "Cookie1"
        response.cookies["test"]["httponly"] = True

        response.cookies["c2"] = "Cookie2"
        response.cookies["c2"]["httponly"] = False

        return response

    _, response = await app.asgi_client.get("/cookie")

    CookieDef = namedtuple("CookieDef", ("value", "httponly"))
    Cookie = namedtuple("Cookie", ("domain", "path", "value", "httponly"))
    cookie_map = {
        "test": CookieDef("Cookie1", True),
        "c2": CookieDef("Cookie2", False),
    }

    cookies = {
        c.name: Cookie(c.domain, c.path, c.value, "HttpOnly" in c._rest.keys())
        for c in response.cookies.jar
    }

    for name, definition in cookie_map.items():
        cookie = cookies.get(name)
        assert cookie
        assert cookie.value == definition.value
        assert cookie.domain == "mockserver.local"
        assert cookie.path == "/"
        assert cookie.httponly == definition.httponly


@pytest.mark.asyncio
async def test_content_type(app):
    @app.get("/json")
    def send_json(request):
        return json({"foo": "bar"})

    @app.get("/text")
    def send_text(request):
        return text("foobar")

    @app.get("/custom")
    def send_custom(request):
        return text("foobar", content_type="somethingelse")

    _, response = await app.asgi_client.get("/json")
    assert response.headers.get("content-type") == "application/json"

    _, response = await app.asgi_client.get("/text")
    assert response.headers.get("content-type") == "text/plain; charset=utf-8"

    _, response = await app.asgi_client.get("/custom")
    assert response.headers.get("content-type") == "somethingelse"


@pytest.mark.asyncio
async def test_request_handle_exception(app):
    @app.get("/error-prone")
    def _request(request):
        raise ServiceUnavailable(message="Service unavailable")

    _, response = await app.asgi_client.get("/wrong-path")
    assert response.status_code == 404

    _, response = await app.asgi_client.get("/error-prone")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_request_exception_suppressed_by_middleware(app):
    @app.get("/error-prone")
    def _request(request):
        raise ServiceUnavailable(message="Service unavailable")

    @app.on_request
    def forbidden(request):
        raise Forbidden(message="forbidden")

    _, response = await app.asgi_client.get("/wrong-path")
    assert response.status_code == 403

    _, response = await app.asgi_client.get("/error-prone")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_signals_triggered(app):
    @app.get("/test_signals_triggered")
    async def _request(request):
        return text("test_signals_triggered")

    signals_triggered = []
    signals_expected = [
        # "http.lifecycle.begin",
        # "http.lifecycle.read_head",
        "http.lifecycle.request",
        "http.lifecycle.handle",
        "http.routing.before",
        "http.routing.after",
        "http.handler.before",
        "http.handler.after",
        "http.lifecycle.response",
        # "http.lifecycle.send",
        # "http.lifecycle.complete",
    ]

    def signal_handler(signal):
        return lambda *a, **kw: signals_triggered.append(signal)

    for signal in RESERVED_NAMESPACES["http"]:
        app.signal(signal)(signal_handler(signal))

    _, response = await app.asgi_client.get("/test_signals_triggered")
    assert response.status_code == 200
    assert response.text == "test_signals_triggered"
    assert signals_triggered == signals_expected


@pytest.mark.asyncio
async def test_asgi_serve_location(app):
    @app.get("/")
    def _request(request: Request):
        return text(request.app.serve_location)

    _, response = await app.asgi_client.get("/")
    assert response.text == "http://<ASGI>"
