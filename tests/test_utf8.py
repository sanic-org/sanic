from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #

def test_utf8_query_string():
    app = Sanic('test_utf8_query_string')

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = sanic_endpoint_test(app, params=[("utf8", '✓')])
    assert request.args.get('utf8') == '✓'


def test_utf8_response():
    app = Sanic('test_utf8_response')

    @app.route('/')
    async def handler(request):
        return text('✓')

    request, response = sanic_endpoint_test(app)
    assert response.text == '✓'


def skip_test_utf8_route():
    app = Sanic('skip_test_utf8_route')

    @app.route('/')
    async def handler(request):
        return text('OK')

    # UTF-8 Paths are not supported
    request, response = sanic_endpoint_test(app, route='/✓', uri='/✓')
    assert response.text == 'OK'


def test_utf8_post_json():
    app = Sanic('test_utf8_post_json')

    @app.route('/')
    async def handler(request):
        return text('OK')

    payload = {'test': '✓'}
    headers = {'content-type': 'application/json'}

    request, response = sanic_endpoint_test(app, data=json_dumps(payload), headers=headers)

    assert request.json.get('test') == '✓'
    assert response.text == 'OK'
