from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.utils import HOST, PORT
from unittest.mock import MagicMock
import pytest
import asyncio


async def stop(app):
    await asyncio.sleep(0.2)
    app.stop()


def test_register_system_signals():
    """Test if sanic register system signals"""
    app = Sanic('test_register_system_signals')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    loop = asyncio.new_event_loop()
    loop.add_signal_handler = MagicMock()
    asyncio.ensure_future(stop(app), loop=loop)
    app.run(HOST, PORT, loop=loop)
    assert loop.add_signal_handler.called == True


def test_dont_register_system_signals():
    """Test if sanic don't register system signals"""
    app = Sanic('test_register_system_signals')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    loop = asyncio.new_event_loop()
    loop.add_signal_handler = MagicMock()
    asyncio.ensure_future(stop(app), loop=loop)
    app.run(HOST, PORT, loop=loop, register_sys_signals=False)
    assert loop.add_signal_handler.called == False
