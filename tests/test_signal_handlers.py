import asyncio
import os
import signal

from queue import Queue
from unittest.mock import MagicMock

import pytest

from sanic.compat import ctrlc_workaround_for_windows
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


@pytest.mark.skipif(
    os.name == "nt", reason="May hang CI on py38/windows"
)
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


@pytest.mark.skipif(
    os.name == "nt", reason="May hang CI on py38/windows"
)
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


@pytest.mark.skipif(
    os.name == "nt", reason="windows cannot SIGINT processes"
)

def test_windows_workaround():
    """Test Windows workaround (on any other OS)"""
    # At least some code coverage, even though this test doesn't work on
    # Windows...
    class MockApp:
        def __init__(self):
            self.stopped = False

        def stop(self):
            self.stopped = True

        def add_task(self, func):
            loop = asyncio.get_event_loop()
            self.stay_active_task = loop.create_task(func(self))

    async def atest():
        app = MockApp()
        ctrlc_workaround_for_windows(app)
        await asyncio.sleep(0.1)
        assert not app.stopped
        # First Ctrl+C: should call app.stop() within 0.1 seconds
        os.kill(os.getpid(), signal.SIGINT)
        await asyncio.sleep(0.2)
        assert app.stopped
        assert app.stay_active_task.result() == None
        # Second Ctrl+C should raise
        with pytest.raises(KeyboardInterrupt):
            os.kill(os.getpid(), signal.SIGINT)
        return "OK"

    # Run in our private loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    assert loop.run_until_complete(atest()) == "OK"
