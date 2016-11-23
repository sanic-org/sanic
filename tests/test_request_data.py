from sanic import Sanic
from sanic.response import json
from sanic.utils import sanic_endpoint_test
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

    request, response = sanic_endpoint_test(app)

    response_json = loads(response.text)
    assert response_json['user'] == 'sanic'
    assert response_json.get('sidekick') is None
