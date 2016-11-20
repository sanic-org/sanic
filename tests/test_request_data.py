from sanic import Sanic
from sanic.response import json
from sanic.utils import sanic_endpoint_test
from ujson import loads


def test_storage():
    app = Sanic('test_text')

    @app.middleware('request')
    def store(request):
        request['a'] = 'test'
        request['b'] = 'zest'
        del request['b']

    @app.route('/')
    def handler(request):
        return json({ 'a': request.get('a'), 'b': request.get('b') })

    request, response = sanic_endpoint_test(app)

    response_json = loads(response.text)
    assert response_json['a'] == 'test'
    assert response_json.get('b') is None