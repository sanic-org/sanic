import random

from sanic import Sanic
from sanic.response import json
from ujson import loads


def test_storage():
    app = Sanic('test_text')

    @app.middleware('request')
    def store(request):
        request['user'] = 'sanic'
        request['sidekick'] = 'tails'
        del request['sidekick']

    @app.route('/')
    def handler(request):
        return json({'user': request.get('user'), 'sidekick': request.get('sidekick')})

    request, response = app.test_client.get('/')

    response_json = loads(response.text)
    assert response_json['user'] == 'sanic'
    assert response_json.get('sidekick') is None


def test_app_injection():
    app = Sanic('test_app_injection')
    expected = random.choice(range(0, 100))

    @app.listener('after_server_start')
    async def inject_data(app, loop):
        app.injected = expected

    @app.get('/')
    async def handler(request):
        return json({'injected': request.app.injected})

    request, response = app.test_client.get('/')

    response_json = loads(response.text)
    assert response_json['injected'] == expected
