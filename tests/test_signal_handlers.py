import asyncio
import os
import signal

from queue import Queue
from unittest.mock import MagicMock

from sanic.response import HTTPResponse
from sanic.testing import HOST, PORT


async def stop(app, loop):
    await asyncio.sleep(0.1)
    app.stop()


calledq = Queue()


def set_loop(app, loop):
    global mock
    mock = MagicMock()
    if os.name == "nt":
        signal.signal = mock
    else:
        loop.add_signal_handler = mock


def after(app, loop):
    calledq.put(mock.called)


def test_register_system_signals(app):
    """Test if sanic register system signals"""

    @app.route("/hello")
    async def hello_route(request):
        return HTTPResponse()

    app.listener("after_server_start")(stop)
    app.listener("before_server_start")(set_loop)
    app.listener("after_server_stop")(after)

    app.run(HOST, PORT)
    assert calledq.get() is True


def test_dont_register_system_signals(app):
    """Test if sanic don't register system signals"""

    @app.route("/hello")
    async def hello_route(request):
        return HTTPResponse()

    app.listener("after_server_start")(stop)
    app.listener("before_server_start")(set_loop)
    app.listener("after_server_stop")(after)

    app.run(HOST, PORT, register_sys_signals=False)
    assert calledq.get() is False
