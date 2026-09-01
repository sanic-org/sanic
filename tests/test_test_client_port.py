from sanic_testing.testing import PORT, SanicTestClient

from sanic.response import json, text


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #


def test_test_client_port_none(app):
    @app.get("/get")
    def handler(request):
        return text("OK")

    test_client = SanicTestClient(app, port=None)

    request, response = test_client.get("/get")
    assert response.text == "OK"

    request, response = test_client.post("/get")
    assert response.status == 405


def test_sequential_test_client_get_requests(app):
    """The WSGI test client starts a server per request on the same port.

    Sequential requests must not fail with EADDRINUSE after the first bind.
    See: https://github.com/sanic-org/sanic/issues/3128
    """

    @app.get("/my-endpoint")
    def handler(request):
        return text("OK")

    client = SanicTestClient(app, port=None)
    _, first = client.get("/my-endpoint")
    assert first.status == 200
    assert first.text == "OK"

    _, second = client.get("/my-endpoint")
    assert second.status == 200
    assert second.text == "OK"
    assert client.port > 0


def test_test_client_port_default(app):
    @app.get("/get")
    def handler(request):
        return json(request.transport.get_extra_info("sockname")[1])

    test_client = SanicTestClient(app)
    assert test_client.port == PORT  # Can be None before request

    request, response = test_client.get("/get")
    assert test_client.port > 0
    assert response.json == test_client.port
