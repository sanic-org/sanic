import asyncio
import logging
import sys

from inspect import isawaitable
from os import environ
from unittest.mock import patch

import pytest

from sanic import Sanic
from sanic.exceptions import SanicException
from sanic.response import text


def uvloop_installed():
    try:
        import uvloop  # noqa

        return True
    except ImportError:
        return False


def test_app_loop_running(app):
    @app.get("/test")
    async def handler(request):
        assert isinstance(app.loop, asyncio.AbstractEventLoop)
        return text("pass")

    request, response = app.test_client.get("/test")
    assert response.text == "pass"


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="requires python3.7 or higher"
)
def test_create_asyncio_server(app):
    if not uvloop_installed():
        loop = asyncio.get_event_loop()
        asyncio_srv_coro = app.create_server(return_asyncio_server=True)
        assert isawaitable(asyncio_srv_coro)
        srv = loop.run_until_complete(asyncio_srv_coro)
        assert srv.is_serving() is True


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="requires python3.7 or higher"
)
def test_asyncio_server_no_start_serving(app):
    if not uvloop_installed():
        loop = asyncio.get_event_loop()
        asyncio_srv_coro = app.create_server(
            port=43123,
            return_asyncio_server=True,
            asyncio_server_kwargs=dict(start_serving=False),
        )
        srv = loop.run_until_complete(asyncio_srv_coro)
        assert srv.is_serving() is False


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="requires python3.7 or higher"
)
def test_asyncio_server_start_serving(app):
    if not uvloop_installed():
        loop = asyncio.get_event_loop()
        asyncio_srv_coro = app.create_server(
            port=43124,
            return_asyncio_server=True,
            asyncio_server_kwargs=dict(start_serving=False),
        )
        srv = loop.run_until_complete(asyncio_srv_coro)
        assert srv.is_serving() is False
        loop.run_until_complete(srv.start_serving())
        assert srv.is_serving() is True
        wait_close = srv.close()
        loop.run_until_complete(wait_close)
        # Looks like we can't easily test `serve_forever()`


def test_app_loop_not_running(app):
    with pytest.raises(SanicException) as excinfo:
        app.loop

    assert str(excinfo.value) == (
        "Loop can only be retrieved after the app has started "
        "running. Not supported with `create_server` function"
    )


def test_app_run_raise_type_error(app):

    with pytest.raises(TypeError) as excinfo:
        app.run(loop="loop")

    assert str(excinfo.value) == (
        "loop is not a valid argument. To use an existing loop, "
        "change to create_server().\nSee more: "
        "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
        "#asynchronous-support"
    )


def test_app_route_raise_value_error(app):

    with pytest.raises(ValueError) as excinfo:

        @app.route("/test")
        async def handler():
            return text("test")

    assert (
        str(excinfo.value)
        == "Required parameter `request` missing in the handler() route?"
    )


def test_app_handle_request_handler_is_none(app, monkeypatch):
    def mockreturn(*args, **kwargs):
        return None, [], {}, "", "", None

    # Not sure how to make app.router.get() return None, so use mock here.
    monkeypatch.setattr(app.router, "get", mockreturn)

    @app.get("/test")
    def handler(request):
        return text("test")

    _, response = app.test_client.get("/test")

    assert (
        "'None' was returned while requesting a handler from the router"
        in response.text
    )


@pytest.mark.parametrize("websocket_enabled", [True, False])
@pytest.mark.parametrize("enable", [True, False])
def test_app_enable_websocket(app, websocket_enabled, enable):
    app.websocket_enabled = websocket_enabled
    app.enable_websocket(enable=enable)

    assert app.websocket_enabled == enable

    @app.websocket("/ws")
    async def handler(request, ws):
        await ws.send("test")

    assert app.websocket_enabled == True


@patch("sanic.app.WebSocketProtocol")
def test_app_websocket_parameters(websocket_protocol_mock, app):
    app.config.WEBSOCKET_MAX_SIZE = 44
    app.config.WEBSOCKET_MAX_QUEUE = 45
    app.config.WEBSOCKET_READ_LIMIT = 46
    app.config.WEBSOCKET_WRITE_LIMIT = 47
    app.config.WEBSOCKET_PING_TIMEOUT = 48
    app.config.WEBSOCKET_PING_INTERVAL = 50

    @app.websocket("/ws")
    async def handler(request, ws):
        await ws.send("test")

    try:
        # This will fail because WebSocketProtocol is mocked and only the call kwargs matter
        app.test_client.get("/ws")
    except:
        pass

    websocket_protocol_call_args = websocket_protocol_mock.call_args
    ws_kwargs = websocket_protocol_call_args[1]
    assert ws_kwargs["websocket_max_size"] == app.config.WEBSOCKET_MAX_SIZE
    assert ws_kwargs["websocket_max_queue"] == app.config.WEBSOCKET_MAX_QUEUE
    assert ws_kwargs["websocket_read_limit"] == app.config.WEBSOCKET_READ_LIMIT
    assert (
        ws_kwargs["websocket_write_limit"] == app.config.WEBSOCKET_WRITE_LIMIT
    )
    assert (
        ws_kwargs["websocket_ping_timeout"]
        == app.config.WEBSOCKET_PING_TIMEOUT
    )
    assert (
        ws_kwargs["websocket_ping_interval"]
        == app.config.WEBSOCKET_PING_INTERVAL
    )


def test_handle_request_with_nested_exception(app, monkeypatch):

    err_msg = "Mock Exception"

    # Not sure how to raise an exception in app.error_handler.response(), use mock here
    def mock_error_handler_response(*args, **kwargs):
        raise Exception(err_msg)

    monkeypatch.setattr(
        app.error_handler, "response", mock_error_handler_response
    )

    @app.get("/")
    def handler(request):
        raise Exception

    request, response = app.test_client.get("/")
    assert response.status == 500
    assert response.text == "An error occurred while handling an error"


def test_handle_request_with_nested_exception_debug(app, monkeypatch):

    err_msg = "Mock Exception"

    # Not sure how to raise an exception in app.error_handler.response(), use mock here
    def mock_error_handler_response(*args, **kwargs):
        raise Exception(err_msg)

    monkeypatch.setattr(
        app.error_handler, "response", mock_error_handler_response
    )

    @app.get("/")
    def handler(request):
        raise Exception

    request, response = app.test_client.get("/", debug=True)
    assert response.status == 500
    assert response.text.startswith(
        f"Error while handling error: {err_msg}\nStack: Traceback (most recent call last):\n"
    )


def test_handle_request_with_nested_sanic_exception(app, monkeypatch, caplog):

    # Not sure how to raise an exception in app.error_handler.response(), use mock here
    def mock_error_handler_response(*args, **kwargs):
        raise SanicException("Mock SanicException")

    monkeypatch.setattr(
        app.error_handler, "response", mock_error_handler_response
    )

    @app.get("/")
    def handler(request):
        raise Exception

    with caplog.at_level(logging.ERROR):
        request, response = app.test_client.get("/")
    port = request.server_port
    assert port > 0
    assert response.status == 500
    assert "Mock SanicException" in response.text
    assert (
        "sanic.root",
        logging.ERROR,
        f"Exception occurred while handling uri: 'http://127.0.0.1:{port}/'",
    ) in caplog.record_tuples


def test_app_name_required():
    with pytest.raises(SanicException):
        Sanic()


def test_app_has_test_mode_sync():
    app = Sanic("test")

    @app.get("/")
    def handler(request):
        assert request.app.test_mode
        return text("test")

    _, response = app.test_client.get("/")
    assert response.status == 200


def test_app_registry():
    instance = Sanic("test")
    assert Sanic._app_registry["test"] is instance


def test_app_registry_wrong_type():
    with pytest.raises(SanicException):
        Sanic.register_app(1)


def test_app_registry_name_reuse():
    Sanic("test")
    Sanic.test_mode = False
    with pytest.raises(SanicException):
        Sanic("test")
    Sanic.test_mode = True
    Sanic("test")


def test_app_registry_retrieval():
    instance = Sanic("test")
    assert Sanic.get_app("test") is instance


def test_get_app_does_not_exist():
    with pytest.raises(SanicException):
        Sanic.get_app("does-not-exist")


def test_get_app_does_not_exist_force_create():
    assert isinstance(
        Sanic.get_app("does-not-exist", force_create=True), Sanic
    )


def test_app_no_registry():
    Sanic("no-register", register=False)
    with pytest.raises(SanicException):
        Sanic.get_app("no-register")


def test_app_no_registry_env():
    environ["SANIC_REGISTER"] = "False"
    Sanic("no-register")
    with pytest.raises(SanicException):
        Sanic.get_app("no-register")
    del environ["SANIC_REGISTER"]
