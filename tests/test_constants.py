import pytest

from sanic import Sanic, text
from sanic.application.constants import Mode, Server, ServerStage
from sanic.constants import HTTP_METHODS, HTTPMethod


@pytest.mark.parametrize("enum", (HTTPMethod, Server, Mode))
def test_string_compat(enum):
    for key in enum.__members__.keys():
        assert key.upper() == getattr(enum, key).upper()
        assert key.lower() == getattr(enum, key).lower()


def test_http_methods():
    for value in HTTPMethod.__members__.values():
        assert value in HTTP_METHODS


def test_server_stage():
    assert ServerStage.SERVING > ServerStage.PARTIAL > ServerStage.STOPPED


def test_use_in_routes(app: Sanic):
    @app.route("/", methods=[HTTPMethod.GET, HTTPMethod.POST])
    def handler(_):
        return text("It works")

    _, response = app.test_client.get("/")
    assert response.status == 200
    assert response.text == "It works"

    _, response = app.test_client.post("/")
    assert response.status == 200
    assert response.text == "It works"
