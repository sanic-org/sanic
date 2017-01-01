from random import choice

from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.utils import sanic_endpoint_test
import asyncio

try:
    import uvloop as async_loop
except ImportError:
    async_loop = asyncio


def test_server_closes_loop():
    """Test if server closes loop"""
    app = Sanic('test_server_dont_closes_loop')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    loop = async_loop.new_event_loop()
    asyncio.set_event_loop(loop)

    sanic_endpoint_test(app, uri='/hello', loop=loop)
    assert loop.is_closed() == True


def test_server_closes_loop_when_it_not_setted():
    """Test if server closes loop when it not setted but the close_loop does"""
    app = Sanic('test_server_dont_closes_loop')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    sanic_endpoint_test(app, uri='/hello', close_loop=False)

    loop = asyncio.get_event_loop()
    assert loop.is_closed() == True


def test_server_dont_closes_loop():
    """Test if server don't closes loop"""
    app = Sanic('test_server_dont_closes_loop')

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse()

    loop = async_loop.new_event_loop()
    asyncio.set_event_loop(loop)

    sanic_endpoint_test(app, uri='/hello', loop=loop, close_loop=False)
    assert loop.is_closed() == False
