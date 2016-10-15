from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.request import Request
from sanic.response import json, text, HTTPResponse
from sanic.utils import sanic_endpoint_test


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_middleware_request():
    app = Sanic('test_middleware_request')

    results = []

    @app.middleware
    async def handler(request):
        results.append(request)

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'OK'
    assert type(results[0]) is Request


def test_middleware_response():
    app = Sanic('test_middleware_response')

    results = []

    @app.middleware('request')
    async def process_response(request):
        results.append(request)

    @app.middleware('response')
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'OK'
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert issubclass(type(results[2]), HTTPResponse)


def test_middleware_override_request():
    app = Sanic('test_middleware_override_request')

    @app.middleware
    async def halt_request(request):
        return text('OK')

    @app.route('/')
    async def handler(request):
        return text('FAIL')

    response = sanic_endpoint_test(app, gather_request=False)

    assert response.status == 200
    assert response.text == 'OK'


def test_middleware_override_response():
    app = Sanic('test_middleware_override_response')

    @app.middleware('response')
    async def process_response(request, response):
        return text('OK')

    @app.route('/')
    async def handler(request):
        return text('FAIL')

    request, response = sanic_endpoint_test(app)

    assert response.status == 200
    assert response.text == 'OK'
