import asyncio

import pytest

from sanic.exceptions import SanicException
from sanic.response import text


def test_app_loop_running(app):

    @app.get('/test')
    async def handler(request):
        assert isinstance(app.loop, asyncio.AbstractEventLoop)
        return text('pass')

    request, response = app.test_client.get('/test')
    assert response.text == 'pass'


def test_app_loop_not_running(app):
    with pytest.raises(SanicException) as excinfo:
        app.loop

    assert str(excinfo.value) == (
        'Loop can only be retrieved after the app has started '
        'running. Not supported with `create_server` function'
    )


def test_app_run_raise_type_error(app):

    with pytest.raises(TypeError) as excinfo:
        app.run(loop='loop')

    assert str(excinfo.value) == (
        'loop is not a valid argument. To use an existing loop, '
        'change to create_server().\nSee more: '
        'https://sanic.readthedocs.io/en/latest/sanic/deploying.html'
        '#asynchronous-support'
    )


def test_app_route_raise_value_error(app):

    with pytest.raises(ValueError) as excinfo:
        @app.route('/test')
        async def handler():
            return text('test')

    assert str(excinfo.value) == 'Required parameter `request` missing in the handler() route?'


def test_app_handle_request_handler_is_none(app, monkeypatch):

    def mockreturn(*args, **kwargs):
        return None, [], {}, ''

    # Not sure how to make app.router.get() return None, so use mock here.
    monkeypatch.setattr(app.router, 'get', mockreturn)

    @app.get('/test')
    def handler(request):
        return text('test')

    request, response = app.test_client.get('/test')

    assert response.text == 'Error: \'None\' was returned while requesting a handler from the router'


@pytest.mark.parametrize('websocket_enabled', [True, False])
@pytest.mark.parametrize('enable', [True, False])
def test_enable_websocket(app, websocket_enabled, enable):
    app.websocket_enabled = websocket_enabled
    app.enable_websocket(enable=enable)

    assert app.websocket_enabled == enable

    @app.websocket('/ws')
    async def handler(request, ws):
        await ws.send('test')

    assert app.websocket_enabled == True
