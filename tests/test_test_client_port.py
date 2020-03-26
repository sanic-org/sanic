from sanic.response import json, text
from sanic.testing import PORT, SanicTestClient


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


def test_test_client_port_default(app):
    @app.get("/get")
    def handler(request):
        return json(request.transport.get_extra_info("sockname")[1])

    test_client = SanicTestClient(app)
    assert test_client.port == PORT  # Can be None before request

    request, response = test_client.get("/get")
    assert test_client.port > 0
    assert response.json == test_client.port
