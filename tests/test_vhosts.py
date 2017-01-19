from sanic import Sanic
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test


def test_vhosts():
    app = Sanic('test_vhosts')

    @app.route('/', host="example.com")
    async def handler(request):
        return text("You're at example.com!")

    @app.route('/', host="subdomain.example.com")
    async def handler(request):
        return text("You're at subdomain.example.com!")

    headers = {"Host": "example.com"}
    request, response = sanic_endpoint_test(app, headers=headers)
    assert response.text == "You're at example.com!"

    headers = {"Host": "subdomain.example.com"}
    request, response = sanic_endpoint_test(app, headers=headers)
    assert response.text == "You're at subdomain.example.com!"


def test_vhosts_with_list():
    app = Sanic('test_vhosts')

    @app.route('/', host=["hello.com", "world.com"])
    async def handler(request):
        return text("Hello, world!")

    headers = {"Host": "hello.com"}
    request, response = sanic_endpoint_test(app, headers=headers)
    assert response.text == "Hello, world!"

    headers = {"Host": "world.com"}
    request, response = sanic_endpoint_test(app, headers=headers)
    assert response.text == "Hello, world!"
