import asyncio
import signal

from contextlib import closing
from socket import socket

import pytest

from sanic_testing.testing import HOST, PORT

from sanic.exceptions import BadRequest, SanicException


AVAILABLE_LISTENERS = [
    "before_server_start",
    "after_server_start",
    "before_server_stop",
    "after_server_stop",
]


def create_listener(listener_name, in_list):
    async def _listener(app, loop):
        print(f"DEBUG MESSAGE FOR PYTEST for {listener_name}")
        in_list.insert(0, app.name + listener_name)

    return _listener


def create_listener_no_loop(listener_name, in_list):
    async def _listener(app):
        print(f"DEBUG MESSAGE FOR PYTEST for {listener_name}")
        in_list.insert(0, app.name + listener_name)

    return _listener


def start_stop_app(random_name_app, **run_kwargs):
    @random_name_app.after_server_start
    async def shutdown(app):
        await asyncio.sleep(1.1)
        app.stop()

    try:
        random_name_app.run(HOST, PORT, single_process=True, **run_kwargs)
    except KeyboardInterrupt:
        pass


@pytest.mark.parametrize("listener_name", AVAILABLE_LISTENERS)
def test_single_listener(app, listener_name):
    """Test that listeners on their own work"""
    output = []
    # Register listener
    app.listener(listener_name)(create_listener(listener_name, output))
    start_stop_app(app)
    assert app.name + listener_name == output.pop()


@pytest.mark.parametrize("listener_name", AVAILABLE_LISTENERS)
def test_single_listener_no_loop(app, listener_name):
    """Test that listeners on their own work"""
    output = []
    # Register listener
    app.listener(listener_name)(create_listener_no_loop(listener_name, output))
    start_stop_app(app)
    assert app.name + listener_name == output.pop()


@pytest.mark.parametrize("listener_name", AVAILABLE_LISTENERS)
def test_register_listener(app, listener_name):
    """
    Test that listeners on their own work with
    app.register_listener method
    """
    output = []
    # Register listener
    listener = create_listener(listener_name, output)
    app.register_listener(listener, event=listener_name)
    start_stop_app(app)
    assert app.name + listener_name == output.pop()


def test_all_listeners(app):
    output = []
    for listener_name in AVAILABLE_LISTENERS:
        listener = create_listener(listener_name, output)
        app.listener(listener_name)(listener)
    start_stop_app(app)
    for listener_name in AVAILABLE_LISTENERS:
        assert app.name + listener_name == output.pop()


def test_all_listeners_as_convenience(app):
    output = []
    for listener_name in AVAILABLE_LISTENERS:
        listener = create_listener(listener_name, output)
        method = getattr(app, listener_name)
        method(listener)
    start_stop_app(app)
    for listener_name in AVAILABLE_LISTENERS:
        assert app.name + listener_name == output.pop()


@pytest.mark.asyncio
async def test_trigger_before_events_create_server(app):
    class MySanicDb:
        pass

    @app.listener("before_server_start")
    async def init_db(app, loop):
        app.ctx.db = MySanicDb()

    srv = await app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )
    await srv.startup()
    await srv.before_start()

    assert hasattr(app.ctx, "db")
    assert isinstance(app.ctx.db, MySanicDb)


@pytest.mark.asyncio
async def test_trigger_before_events_create_server_missing_event(app):
    class MySanicDb:
        pass

    with pytest.raises(BadRequest):

        @app.listener
        async def init_db(app, loop):
            app.ctx.db = MySanicDb()

    assert not hasattr(app.ctx, "db")


def test_create_server_trigger_events(app):
    """Test if create_server can trigger server events"""

    def stop_on_alarm(signum, frame):
        raise KeyboardInterrupt("...")

    flag1 = False
    flag2 = False
    flag3 = False

    async def stop(app, loop):
        nonlocal flag1
        flag1 = True

    async def before_stop(app, loop):
        nonlocal flag2
        flag2 = True

    async def after_stop(app, loop):
        nonlocal flag3
        flag3 = True

    app.listener("after_server_start")(stop)
    app.listener("before_server_stop")(before_stop)
    app.listener("after_server_stop")(after_stop)

    loop = asyncio.get_event_loop()

    # Use random port for tests

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(1)
    with closing(socket()) as sock:
        sock.bind(("127.0.0.1", 0))

        serv_coro = app.create_server(
            return_asyncio_server=True, sock=sock, debug=True
        )
        serv_task = asyncio.ensure_future(serv_coro, loop=loop)
        server = loop.run_until_complete(serv_task)
        loop.run_until_complete(server.startup())
        loop.run_until_complete(server.after_start())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()
        finally:
            # Run the on_stop function if provided
            loop.run_until_complete(server.before_stop())

            # Wait for server to close
            close_task = server.close()
            loop.run_until_complete(close_task)

            # Complete all tasks on the loop
            for connection in server.connections:
                connection.close_if_idle()
            loop.run_until_complete(server.after_stop())
        assert flag1 and flag2 and flag3


@pytest.mark.asyncio
async def test_missing_startup_raises_exception(app):
    @app.listener("before_server_start")
    async def init_db(app, loop):
        ...

    srv = await app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )

    with pytest.raises(SanicException):
        await srv.before_start()


def test_reload_listeners_attached(app):
    async def dummy(*_):
        ...

    app.reload_process_start(dummy)
    app.reload_process_stop(dummy)
    app.listener("reload_process_start")(dummy)
    app.listener("reload_process_stop")(dummy)

    assert len(app.listeners.get("reload_process_start")) == 2
    assert len(app.listeners.get("reload_process_stop")) == 2
