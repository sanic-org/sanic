from copy import deepcopy

from sanic import Blueprint, Sanic, blueprints, response
from sanic.response import text


def test_bp_copy(app: Sanic):
    bp1 = Blueprint("test_bp1", version=1)

    @bp1.route("/page")
    def handle_request(request):
        return text("Hello world!")

    bp2 = bp1.copy(name="test_bp2", version=2)
    assert id(bp1) != id(bp2)

    app.blueprint(bp1)
    app.blueprint(bp2)
    bp3 = bp1.copy(name="test_bp3", version=3, with_registration=True)
    bp4 = bp1.copy(name="test_bp4", version=4, with_ctx=True)
    bp5 = bp1.copy(name="test_bp5", version=5, with_registration=False)
    app.blueprint(bp5)

    _, response = app.test_client.get("/v1/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v2/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v3/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v4/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v5/page")
    assert "Hello world!" in response.text
