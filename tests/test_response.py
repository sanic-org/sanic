from random import choice
from json import loads as json_loads, JSONDecodeError

import pytest

from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.utils import sanic_endpoint_test


def test_response_body_not_a_string():
    """Test when a response body sent from the application is not a string"""
    app = Sanic('response_body_not_a_string')
    random_num = choice(range(1000))

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse(body=random_num)

    request, response = sanic_endpoint_test(app, uri='/hello')
    assert response.text == str(random_num)


def test_json():
    """Tests the smart handling of dicts for handlers"""
    app = Sanic('test_json')

    @app.route('/')
    async def handler(request):
        return {"test": True}

    request, response = sanic_endpoint_test(app)

    try:
        results = json_loads(response.text)
    except JSONDecodeError:
        pytest.fail(
            "Expected JSON response but got '{}'".format(response))

    assert results.get('test') is True


def test_text():
    """Tests the smart handling of strings for handlers"""
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        return 'Hello'

    request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'


def test_int():
    """Tests the smart handling of ints for handlers"""
    app = Sanic('test_int')
    random_int = choice(range(0, 10000))

    @app.route('/')
    async def handler(request):
        return random_int

    request, response = sanic_endpoint_test(app)

    assert response.text == str(random_int)
