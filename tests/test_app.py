import asyncio
import logging
import sys

from inspect import isawaitable

import pytest

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
def test_asyncio_server_start_serving(app):
    if not uvloop_installed():
        loop = asyncio.get_event_loop()
        asyncio_srv_coro = app.create_server(
            return_asyncio_server=True,
            asyncio_server_kwargs=dict(start_serving=False),
        )
        srv = loop.run_until_complete(asyncio_srv_coro)
        assert srv.is_serving() is False


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
        return None, [], {}, "", ""

    # Not sure how to make app.router.get() return None, so use mock here.
    monkeypatch.setattr(app.router, "get", mockreturn)

    @app.get("/test")
    def handler(request):
        return text("test")

    request, response = app.test_client.get("/test")

    assert (
        response.text
        == "Error: 'None' was returned while requesting a handler from the router"
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
        "Error while handling error: {}\nStack: Traceback (most recent call last):\n".format(
            err_msg
        )
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
    assert response.status == 500
    assert response.text == "Error: Mock SanicException"
    assert (
        "sanic.root",
        logging.ERROR,
        "Exception occurred while handling uri: 'http://127.0.0.1:42101/'",
    ) in caplog.record_tuples
