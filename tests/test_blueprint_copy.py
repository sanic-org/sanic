from copy import deepcopy

from sanic import Blueprint, Sanic, blueprints, response
from sanic.response import text


def test_bp_copy(app: Sanic):
    bp1 = Blueprint("test1", version=1)

    @bp1.route("/page")
    def handle_request(request):
        return text("Hello world!")

    bp2 = bp1.copy(name="test2", version=2)
    assert id(bp1) != id(bp2)

    app.blueprint(bp1)
    app.blueprint(bp2)

    _, response = app.test_client.get("/v1/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v2/page")
    assert "Hello world!" in response.text
