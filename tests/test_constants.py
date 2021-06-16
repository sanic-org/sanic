from crypt import methods

from sanic import text
from sanic.constants import HTTP_METHODS, HTTPMethod


def test_string_compat():
    assert "GET" == HTTPMethod.GET
    assert "GET" in HTTP_METHODS
    assert "get" == HTTPMethod.GET
    assert "get" in HTTP_METHODS


def test_use_in_routes(app):
    @app.route("/", methods=[HTTPMethod.GET, HTTPMethod.POST])
    def handler(_):
        return text("It works")

    _, response = app.test_client.get("/")
    assert response.status == 200
    assert response.text == "It works"

    _, response = app.test_client.post("/")
    assert response.status == 200
    assert response.text == "It works"
