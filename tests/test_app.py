import asyncio
import logging
import re

from collections import Counter
from inspect import isawaitable
from os import environ
from unittest.mock import Mock, patch

import pytest

import sanic

from sanic import Sanic
from sanic.compat import OS_IS_WINDOWS
from sanic.config import Config
from sanic.exceptions import SanicException
from sanic.helpers import _default
from sanic.response import text


@pytest.fixture(autouse=True)
def clear_app_registry():
    Sanic._app_registry = {}


def test_app_loop_running(app):
    @app.get("/test")
    async def handler(request):
        assert isinstance(app.loop, asyncio.AbstractEventLoop)
        return text("pass")

    request, response = app.test_client.get("/test")
    assert response.text == "pass"


def test_create_asyncio_server(app):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(return_asyncio_server=True)
    assert isawaitable(asyncio_srv_coro)
    srv = loop.run_until_complete(asyncio_srv_coro)
    assert srv.is_serving() is True


def test_asyncio_server_no_start_serving(app):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(
        port=43123,
        return_asyncio_server=True,
        asyncio_server_kwargs=dict(start_serving=False),
    )
    srv = loop.run_until_complete(asyncio_srv_coro)
    assert srv.is_serving() is False


def test_asyncio_server_start_serving(app):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(
        port=43124,
        return_asyncio_server=True,
        asyncio_server_kwargs=dict(start_serving=False),
    )
    srv = loop.run_until_complete(asyncio_srv_coro)
    assert srv.is_serving() is False
    loop.run_until_complete(srv.startup())
    loop.run_until_complete(srv.start_serving())
    assert srv.is_serving() is True
    wait_close = srv.close()
    loop.run_until_complete(wait_close)
    # Looks like we can't easily test `serve_forever()`


def test_create_server_main(app, caplog):
    app.listener("main_process_start")(lambda *_: ...)
    loop = asyncio.get_event_loop()
    with caplog.at_level(logging.INFO):
        asyncio_srv_coro = app.create_server(return_asyncio_server=True)
        loop.run_until_complete(asyncio_srv_coro)
    assert (
        "sanic.root",
        30,
        "Listener events for the main process are not available with "
        "create_server()",
    ) in caplog.record_tuples


def test_create_server_no_startup(app):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(
        port=43124,
        return_asyncio_server=True,
        asyncio_server_kwargs=dict(start_serving=False),
    )
    srv = loop.run_until_complete(asyncio_srv_coro)
    message = (
        "Cannot run Sanic server without first running await server.startup()"
    )
    with pytest.raises(SanicException, match=message):
        loop.run_until_complete(srv.start_serving())


def test_create_server_main_convenience(app, caplog):
    app.main_process_start(lambda *_: ...)
    loop = asyncio.get_event_loop()
    with caplog.at_level(logging.INFO):
        asyncio_srv_coro = app.create_server(return_asyncio_server=True)
        loop.run_until_complete(asyncio_srv_coro)
    assert (
        "sanic.root",
        30,
        "Listener events for the main process are not available with "
        "create_server()",
    ) in caplog.record_tuples


def test_create_server_init(app, caplog):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(return_asyncio_server=True)
    server = loop.run_until_complete(asyncio_srv_coro)

    message = (
        "AsyncioServer.init has been deprecated and will be removed in v22.6. "
        "Use Sanic.state.is_started instead."
    )
    with pytest.warns(DeprecationWarning, match=message):
        server.init


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
        return Mock(), None, {}

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
        "sanic.error",
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
    with pytest.raises(
        SanicException, match="Registered app must be an instance of Sanic"
    ):
        Sanic.register_app(1)


def test_app_registry_name_reuse():
    Sanic("test")
    Sanic.test_mode = False
    with pytest.raises(
        SanicException, match='Sanic app name "test" already in use.'
    ):
        Sanic("test")
    Sanic.test_mode = True
    Sanic("test")


def test_app_registry_retrieval():
    instance = Sanic("test")
    assert Sanic.get_app("test") is instance


def test_app_registry_retrieval_from_multiple():
    instance = Sanic("test")
    Sanic("something_else")
    assert Sanic.get_app("test") is instance


def test_get_app_does_not_exist():
    with pytest.raises(
        SanicException, match='Sanic app name "does-not-exist" not found.'
    ):
        Sanic.get_app("does-not-exist")


def test_get_app_does_not_exist_force_create():
    assert isinstance(
        Sanic.get_app("does-not-exist", force_create=True), Sanic
    )


def test_get_app_default():
    instance = Sanic("test")
    assert Sanic.get_app() is instance


def test_get_app_no_default():
    with pytest.raises(
        SanicException, match="No Sanic apps have been registered."
    ):
        Sanic.get_app()


def test_get_app_default_ambiguous():
    Sanic("test1")
    Sanic("test2")
    with pytest.raises(
        SanicException,
        match=re.escape(
            'Multiple Sanic apps found, use Sanic.get_app("app_name")'
        ),
    ):
        Sanic.get_app()


def test_app_no_registry():
    Sanic("no-register", register=False)
    with pytest.raises(
        SanicException, match='Sanic app name "no-register" not found.'
    ):
        Sanic.get_app("no-register")


def test_app_no_registry_deprecation_message():
    with pytest.warns(DeprecationWarning) as records:
        Sanic("no-register", register=False)
        Sanic("yes-register", register=True)

    message = (
        "[DEPRECATION v22.6] The register argument is deprecated and will "
        "stop working in v22.6. After v22.6 all apps will be added to the "
        "Sanic app registry."
    )

    assert len(records) == 2
    for record in records:
        assert record.message.args[0] == message


def test_app_no_registry_env():
    environ["SANIC_REGISTER"] = "False"
    Sanic("no-register")
    with pytest.raises(
        SanicException, match='Sanic app name "no-register" not found.'
    ):
        Sanic.get_app("no-register")
    del environ["SANIC_REGISTER"]


def test_app_set_attribute_warning(app):
    message = (
        "Setting variables on Sanic instances is not allowed. You should "
        "change your Sanic instance to use instance.ctx.foo instead."
    )
    with pytest.raises(AttributeError, match=message):
        app.foo = 1


def test_app_set_context(app):
    app.ctx.foo = 1

    retrieved = Sanic.get_app(app.name)
    assert retrieved.ctx.foo == 1


def test_subclass_initialisation():
    class CustomSanic(Sanic):
        pass

    CustomSanic("test_subclass_initialisation")


def test_bad_custom_config():
    with pytest.raises(
        SanicException,
        match=(
            "When instantiating Sanic with config, you cannot also pass "
            "env_prefix"
        ),
    ):
        Sanic("test", config=1, env_prefix=1)


def test_custom_config():
    class CustomConfig(Config):
        ...

    config = CustomConfig()
    app = Sanic("custom", config=config)

    assert app.config == config


def test_custom_context():
    class CustomContext:
        ...

    ctx = CustomContext()
    app = Sanic("custom", ctx=ctx)

    assert app.ctx == ctx


def test_uvloop_config(app, monkeypatch):
    @app.get("/test")
    def handler(request):
        return text("ok")

    try_use_uvloop = Mock()
    monkeypatch.setattr(sanic.app, "try_use_uvloop", try_use_uvloop)

    # Default config
    app.test_client.get("/test")
    if OS_IS_WINDOWS:
        try_use_uvloop.assert_not_called()
    else:
        try_use_uvloop.assert_called_once()

    try_use_uvloop.reset_mock()
    app.config["USE_UVLOOP"] = False
    app.test_client.get("/test")
    try_use_uvloop.assert_not_called()

    try_use_uvloop.reset_mock()
    app.config["USE_UVLOOP"] = True
    app.test_client.get("/test")
    try_use_uvloop.assert_called_once()


def test_uvloop_cannot_never_called_with_create_server(caplog, monkeypatch):
    apps = (Sanic("default-uvloop"), Sanic("no-uvloop"), Sanic("yes-uvloop"))

    apps[1].config.USE_UVLOOP = False
    apps[2].config.USE_UVLOOP = True

    try_use_uvloop = Mock()
    monkeypatch.setattr(sanic.app, "try_use_uvloop", try_use_uvloop)

    loop = asyncio.get_event_loop()

    with caplog.at_level(logging.WARNING):
        for app in apps:
            srv_coro = app.create_server(
                return_asyncio_server=True,
                asyncio_server_kwargs=dict(start_serving=False),
            )
            loop.run_until_complete(srv_coro)

    try_use_uvloop.assert_not_called()  # Check it didn't try to change policy

    message = (
        "You are trying to change the uvloop configuration, but "
        "this is only effective when using the run(...) method. "
        "When using the create_server(...) method Sanic will use "
        "the already existing loop."
    )

    counter = Counter([(r[1], r[2]) for r in caplog.record_tuples])
    modified = sum(1 for app in apps if app.config.USE_UVLOOP is not _default)

    assert counter[(logging.WARNING, message)] == modified


def test_multiple_uvloop_configs_display_warning(caplog):
    Sanic._uvloop_setting = None  # Reset the setting (changed in prev tests)

    default_uvloop = Sanic("default-uvloop")
    no_uvloop = Sanic("no-uvloop")
    yes_uvloop = Sanic("yes-uvloop")

    no_uvloop.config.USE_UVLOOP = False
    yes_uvloop.config.USE_UVLOOP = True

    loop = asyncio.get_event_loop()

    with caplog.at_level(logging.WARNING):
        for app in (default_uvloop, no_uvloop, yes_uvloop):
            srv_coro = app.create_server(
                return_asyncio_server=True,
                asyncio_server_kwargs=dict(start_serving=False),
            )
            srv = loop.run_until_complete(srv_coro)
            loop.run_until_complete(srv.startup())

    message = (
        "It looks like you're running several apps with different "
        "uvloop settings. This is not supported and may lead to "
        "unintended behaviour."
    )

    counter = Counter([(r[1], r[2]) for r in caplog.record_tuples])

    assert counter[(logging.WARNING, message)] == 2


def test_cannot_run_fast_and_workers(app):
    message = "You cannot use both fast=True and workers=X"
    with pytest.raises(RuntimeError, match=message):
        app.run(fast=True, workers=4)
