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
from sanic.helpers import Default
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic.response import text
from sanic.router import Route


@pytest.fixture(autouse=True)
def clear_app_registry():
    Sanic._app_registry = {}


def test_app_loop_running(app: Sanic):
    @app.get("/test")
    async def handler(request):
        assert isinstance(app.loop, asyncio.AbstractEventLoop)
        return text("pass")

    request, response = app.test_client.get("/test")
    assert response.text == "pass"


def test_create_asyncio_server(app: Sanic):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(return_asyncio_server=True)
    assert isawaitable(asyncio_srv_coro)
    srv = loop.run_until_complete(asyncio_srv_coro)
    assert srv.is_serving() is True


def test_asyncio_server_no_start_serving(app: Sanic):
    loop = asyncio.get_event_loop()
    asyncio_srv_coro = app.create_server(
        port=43123,
        return_asyncio_server=True,
        asyncio_server_kwargs=dict(start_serving=False),
    )
    srv = loop.run_until_complete(asyncio_srv_coro)
    assert srv.is_serving() is False


def test_asyncio_server_start_serving(app: Sanic):
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


def test_create_server_main(app: Sanic, caplog):
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


def test_create_server_no_startup(app: Sanic):
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


def test_create_server_main_convenience(app: Sanic, caplog):
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


def test_app_loop_not_running(app: Sanic):
    with pytest.raises(SanicException) as excinfo:
        app.loop

    assert str(excinfo.value) == (
        "Loop can only be retrieved after the app has started "
        "running. Not supported with `create_server` function"
    )


def test_app_run_raise_type_error(app: Sanic):

    with pytest.raises(TypeError) as excinfo:
        app.run(loop="loop")

    assert str(excinfo.value) == (
        "loop is not a valid argument. To use an existing loop, "
        "change to create_server().\nSee more: "
        "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
        "#asynchronous-support"
    )


def test_app_route_raise_value_error(app: Sanic):

    with pytest.raises(ValueError) as excinfo:

        @app.route("/test")
        async def handler():
            return text("test")

    assert (
        str(excinfo.value)
        == "Required parameter `request` missing in the handler() route?"
    )


def test_app_handle_request_handler_is_none(app: Sanic, monkeypatch):
    app.config.TOUCHUP = False
    route = Mock(spec=Route)
    route.extra.request_middleware = []
    route.extra.response_middleware = []

    def mockreturn(*args, **kwargs):
        return route, None, {}

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
def test_app_enable_websocket(app: Sanic, websocket_enabled, enable):
    app.websocket_enabled = websocket_enabled
    app.enable_websocket(enable=enable)

    assert app.websocket_enabled == enable

    @app.websocket("/ws")
    async def handler(request, ws):
        await ws.send("test")

    assert app.websocket_enabled is True


@patch("sanic.mixins.startup.WebSocketProtocol")
def test_app_websocket_parameters(websocket_protocol_mock, app: Sanic):
    app.config.WEBSOCKET_MAX_SIZE = 44
    app.config.WEBSOCKET_PING_TIMEOUT = 48
    app.config.WEBSOCKET_PING_INTERVAL = 50

    @app.websocket("/ws")
    async def handler(request, ws):
        await ws.send("test")

    try:
        # This will fail because WebSocketProtocol is mocked and only the
        # call kwargs matter
        app.test_client.get("/ws")
    except Exception:
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


def test_handle_request_with_nested_exception(app: Sanic, monkeypatch):

    err_msg = "Mock Exception"

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


def test_handle_request_with_nested_exception_debug(app: Sanic, monkeypatch):

    err_msg = "Mock Exception"

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
        f"Error while handling error: {err_msg}\n"
        "Stack: Traceback (most recent call last):\n"
    )


def test_handle_request_with_nested_sanic_exception(
    app: Sanic, monkeypatch, caplog
):
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
    assert len(Sanic._app_registry) == 0
    instance = Sanic("test")
    assert len(Sanic._app_registry) == 1
    assert Sanic._app_registry["test"] is instance
    Sanic.unregister_app(instance)
    assert len(Sanic._app_registry) == 0


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
        SanicException,
        match="Sanic app name 'does-not-exist' not found.\n"
            "App instantiation must occur outside "
            "if __name__ == '__main__' "
            "block or by using an AppLoader.\nSee "
            "https://sanic.dev/en/guide/deployment/app-loader.html"
            " for more details."
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


def test_app_set_attribute_warning(app: Sanic):
    message = (
        "Setting variables on Sanic instances is not allowed. You should "
        "change your Sanic instance to use instance.ctx.foo instead."
    )
    with pytest.raises(AttributeError, match=message):
        app.foo = 1


def test_app_set_context(app: Sanic):
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


@pytest.mark.parametrize("use", (False, True))
def test_uvloop_config(app: Sanic, monkeypatch, use):
    @app.get("/test")
    def handler(request):
        return text("ok")

    try_use_uvloop = Mock()
    monkeypatch.setattr(sanic.mixins.startup, "try_use_uvloop", try_use_uvloop)

    # Default config
    app.test_client.get("/test")
    if OS_IS_WINDOWS:
        try_use_uvloop.assert_not_called()
    else:
        try_use_uvloop.assert_called_once()

    try_use_uvloop.reset_mock()
    app.config["USE_UVLOOP"] = use
    app.test_client.get("/test")

    if use:
        try_use_uvloop.assert_called_once()
    else:
        try_use_uvloop.assert_not_called()


def test_uvloop_cannot_never_called_with_create_server(caplog, monkeypatch):
    apps = (Sanic("default-uvloop"), Sanic("no-uvloop"), Sanic("yes-uvloop"))

    apps[1].config.USE_UVLOOP = False
    apps[2].config.USE_UVLOOP = True

    try_use_uvloop = Mock()
    monkeypatch.setattr(sanic.mixins.startup, "try_use_uvloop", try_use_uvloop)

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
    modified = sum(
        1 for app in apps if not isinstance(app.config.USE_UVLOOP, Default)
    )

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

    assert counter[(logging.WARNING, message)] == 3


def test_cannot_run_fast_and_workers(app: Sanic):
    message = "You cannot use both fast=True and workers=X"
    with pytest.raises(RuntimeError, match=message):
        app.run(fast=True, workers=4)


def test_no_workers(app: Sanic):
    with pytest.raises(RuntimeError, match="Cannot serve with no workers"):
        app.run(workers=0)


@pytest.mark.parametrize(
    "extra",
    (
        {"fast": True},
        {"workers": 2},
        {"auto_reload": True},
    ),
)
def test_cannot_run_single_process_and_workers_or_auto_reload(
    app: Sanic, extra
):
    message = (
        "Single process cannot be run with multiple workers or auto-reload"
    )
    with pytest.raises(RuntimeError, match=message):
        app.run(single_process=True, **extra)


def test_cannot_run_single_process_and_legacy(app: Sanic):
    message = "Cannot run single process and legacy mode"
    with pytest.raises(RuntimeError, match=message):
        app.run(single_process=True, legacy=True)


def test_cannot_run_without_sys_signals_with_workers(app: Sanic):
    message = (
        "Cannot run Sanic.serve with register_sys_signals=False. "
        "Use either Sanic.serve_single or Sanic.serve_legacy."
    )
    with pytest.raises(RuntimeError, match=message):
        app.run(register_sys_signals=False, single_process=False, legacy=False)


def test_default_configure_logging():
    with patch("sanic.app.logging") as mock:
        Sanic("Test")

    mock.config.dictConfig.assert_called_with(LOGGING_CONFIG_DEFAULTS)


def test_custom_configure_logging():
    with patch("sanic.app.logging") as mock:
        Sanic("Test", log_config={"foo": "bar"})

    mock.config.dictConfig.assert_called_with({"foo": "bar"})


def test_disable_configure_logging():
    with patch("sanic.app.logging") as mock:
        Sanic("Test", configure_logging=False)

    mock.config.dictConfig.assert_not_called()


@pytest.mark.parametrize("inspector", (True, False))
def test_inspector(inspector):
    app = Sanic("Test", inspector=inspector)
    assert app.config.INSPECTOR is inspector


def test_build_endpoint_name():
    app = Sanic("Test")
    name = app._build_endpoint_name("foo", "bar")
    assert name == "Test.foo.bar"


def test_manager_in_main_process_only(app: Sanic):
    message = "Can only access the manager from the main process"

    with pytest.raises(SanicException, match=message):
        app.manager

    app._manager = 1
    environ["SANIC_WORKER_PROCESS"] = "ok"

    with pytest.raises(SanicException, match=message):
        app.manager

    del environ["SANIC_WORKER_PROCESS"]

    assert app.manager == 1


def test_inspector_in_main_process_only(app: Sanic):
    message = "Can only access the inspector from the main process"

    with pytest.raises(SanicException, match=message):
        app.inspector

    app._inspector = 1
    environ["SANIC_WORKER_PROCESS"] = "ok"

    with pytest.raises(SanicException, match=message):
        app.inspector

    del environ["SANIC_WORKER_PROCESS"]

    assert app.inspector == 1


def test_stop_trigger_terminate(app: Sanic):
    app.multiplexer = Mock()

    app.stop()

    app.multiplexer.terminate.assert_called_once()
    app.multiplexer.reset_mock()
    assert len(Sanic._app_registry) == 1
    Sanic._app_registry.clear()

    app.stop(terminate=True)

    app.multiplexer.terminate.assert_called_once()
    app.multiplexer.reset_mock()
    assert len(Sanic._app_registry) == 0
    Sanic._app_registry.clear()

    app.stop(unregister=False)
    app.multiplexer.terminate.assert_called_once()
