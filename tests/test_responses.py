from json import loads as json_loads, JSONDecodeError
from random import choice

from sanic import Sanic
from sanic.utils import sanic_endpoint_test


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
        raise ValueError(
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
