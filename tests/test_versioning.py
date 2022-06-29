import pytest

from sanic import Blueprint, text


@pytest.fixture
def handler():
    def handler(_):
        return text("Done.")

    return handler


def test_route(app, handler):
    app.route("/", version=1)(handler)

    _, response = app.test_client.get("/v1")
    assert response.status == 200


def test_bp(app, handler):
    bp = Blueprint("Test", version=1)
    bp.route("/")(handler)
    app.blueprint(bp)

    _, response = app.test_client.get("/v1")
    assert response.status == 200


def test_bp_use_route(app, handler):
    bp = Blueprint("Test", version=1)
    bp.route("/", version=1.1)(handler)
    app.blueprint(bp)

    _, response = app.test_client.get("/v1.1")
    assert response.status == 200


def test_bp_group(app, handler):
    bp = Blueprint("Test")
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1)
    app.blueprint(group)

    _, response = app.test_client.get("/v1")
    assert response.status == 200


def test_bp_group_use_bp(app, handler):
    bp = Blueprint("Test", version=1.1)
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1)
    app.blueprint(group)

    _, response = app.test_client.get("/v1.1")
    assert response.status == 200


def test_bp_group_use_registration(app, handler):
    bp = Blueprint("Test", version=1.1)
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1)
    app.blueprint(group, version=1.2)

    _, response = app.test_client.get("/v1.2")
    assert response.status == 200


def test_bp_group_use_route(app, handler):
    bp = Blueprint("Test", version=1.1)
    bp.route("/", version=1.3)(handler)
    group = Blueprint.group(bp, version=1)
    app.blueprint(group, version=1.2)

    _, response = app.test_client.get("/v1.3")
    assert response.status == 200


def test_version_prefix_route(app, handler):
    app.route("/", version=1, version_prefix="/api/v")(handler)

    _, response = app.test_client.get("/api/v1")
    assert response.status == 200


def test_version_prefix_bp(app, handler):
    bp = Blueprint("Test", version=1, version_prefix="/api/v")
    bp.route("/")(handler)
    app.blueprint(bp)

    _, response = app.test_client.get("/api/v1")
    assert response.status == 200


def test_version_prefix_bp_use_route(app, handler):
    bp = Blueprint("Test", version=1, version_prefix="/ignore/v")
    bp.route("/", version=1.1, version_prefix="/api/v")(handler)
    app.blueprint(bp)

    _, response = app.test_client.get("/api/v1.1")
    assert response.status == 200


def test_version_prefix_bp_group(app, handler):
    bp = Blueprint("Test")
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1, version_prefix="/api/v")
    app.blueprint(group)

    _, response = app.test_client.get("/api/v1")
    assert response.status == 200


def test_version_prefix_bp_group_use_bp(app, handler):
    bp = Blueprint("Test", version=1.1, version_prefix="/api/v")
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1, version_prefix="/ignore/v")
    app.blueprint(group)

    _, response = app.test_client.get("/api/v1.1")
    assert response.status == 200


def test_version_prefix_bp_group_use_registration(app, handler):
    bp = Blueprint("Test", version=1.1, version_prefix="/alsoignore/v")
    bp.route("/")(handler)
    group = Blueprint.group(bp, version=1, version_prefix="/ignore/v")
    app.blueprint(group, version=1.2, version_prefix="/api/v")

    _, response = app.test_client.get("/api/v1.2")
    assert response.status == 200


def test_version_prefix_bp_group_use_route(app, handler):
    bp = Blueprint("Test", version=1.1, version_prefix="/alsoignore/v")
    bp.route("/", version=1.3, version_prefix="/api/v")(handler)
    group = Blueprint.group(bp, version=1, version_prefix="/ignore/v")
    app.blueprint(group, version=1.2, version_prefix="/stillignoring/v")

    _, response = app.test_client.get("/api/v1.3")
    assert response.status == 200
