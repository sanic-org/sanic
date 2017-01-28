from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.utils import HOST, PORT
from unittest.mock import MagicMock
import pytest
import asyncio
from queue import Queue


async def stop(app, loop):
    await asyncio.sleep(0.1)
    app.stop()

calledq = Queue()

def set_loop(app, loop):
    loop.add_signal_handler = MagicMock()

def after(app, loop):
    calledq.put(loop.add_signal_handler.called)

def test_register_system_signals():
    """Test if sanic register system signals"""
    app = Sanic('test_register_system_signals')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    app.run(HOST, PORT,
            before_start=set_loop,
            after_start=stop,
            after_stop=after)
    assert calledq.get() == True


def test_dont_register_system_signals():
    """Test if sanic don't register system signals"""
    app = Sanic('test_register_system_signals')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    app.run(HOST, PORT,
            before_start=set_loop,
            after_start=stop,
            after_stop=after,
            register_sys_signals=False)
    assert calledq.get() == False
