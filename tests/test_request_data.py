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
        return json({ 'user': request.get('user'), 'sidekick': request.get('sidekick') })

    request, response = app.test_client.get('/')

    response_json = loads(response.text)
    assert response_json['user'] == 'sanic'
    assert response_json.get('sidekick') is None
