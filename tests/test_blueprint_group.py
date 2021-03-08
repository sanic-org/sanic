from pytest import raises

from sanic.app import Sanic
from sanic.blueprint_group import BlueprintGroup
from sanic.blueprints import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, text


MIDDLEWARE_INVOKE_COUNTER = {"request": 0, "response": 0}

AUTH = "dGVzdDp0ZXN0Cg=="


def test_bp_group_indexing(app: Sanic):
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")

    group = Blueprint.group(blueprint_1, blueprint_2)
    assert group[0] == blueprint_1

    with raises(expected_exception=IndexError) as e:
        _ = group[3]


def test_bp_group_with_additional_route_params(app: Sanic):
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")

    @blueprint_1.route(
        "/request_path", methods=frozenset({"PUT", "POST"}), version=2
    )
    def blueprint_1_v2_method_with_put_and_post(request: Request):
        if request.method == "PUT":
            return text("PUT_OK")
        elif request.method == "POST":
            return text("POST_OK")

    @blueprint_2.route(
        "/route/<param>", methods=frozenset({"DELETE", "PATCH"}), name="test"
    )
    def blueprint_2_named_method(request: Request, param):
        if request.method == "DELETE":
            return text(f"DELETE_{param}")
        elif request.method == "PATCH":
            return text(f"PATCH_{param}")

    blueprint_group = Blueprint.group(
        blueprint_1, blueprint_2, url_prefix="/api"
    )

    @blueprint_group.middleware("request")
    def authenticate_request(request: Request):
        global AUTH
        auth = request.headers.get("authorization")
        if auth:
            # Dummy auth check. We can have anything here and it's fine.
            if AUTH not in auth:
                return text("Unauthorized", status=401)
        else:
            return text("Unauthorized", status=401)

    @blueprint_group.middleware("response")
    def enhance_response_middleware(request: Request, response: HTTPResponse):
        response.headers.add("x-test-middleware", "value")

    app.blueprint(blueprint_group)

    header = {"authorization": " ".join(["Basic", AUTH])}
    _, response = app.test_client.put(
        "/v2/api/bp1/request_path", headers=header
    )
    assert response.text == "PUT_OK"
    assert response.headers.get("x-test-middleware") == "value"

    _, response = app.test_client.post(
        "/v2/api/bp1/request_path", headers=header
    )
    assert response.text == "POST_OK"

    _, response = app.test_client.delete("/api/bp2/route/bp2", headers=header)
    assert response.text == "DELETE_bp2"

    _, response = app.test_client.patch("/api/bp2/route/bp2", headers=header)
    assert response.text == "PATCH_bp2"

    _, response = app.test_client.put("/v2/api/bp1/request_path")
    assert response.status == 401


def test_bp_group(app: Sanic):
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")

    @blueprint_1.route("/")
    def blueprint_1_default_route(request):
        return text("BP1_OK")

    @blueprint_2.route("/")
    def blueprint_2_default_route(request):
        return text("BP2_OK")

    blueprint_group_1 = Blueprint.group(
        blueprint_1, blueprint_2, url_prefix="/bp"
    )

    blueprint_3 = Blueprint("blueprint_3", url_prefix="/bp3")

    @blueprint_group_1.middleware("request")
    def blueprint_group_1_middleware(request):
        global MIDDLEWARE_INVOKE_COUNTER
        MIDDLEWARE_INVOKE_COUNTER["request"] += 1

    @blueprint_group_1.middleware
    def blueprint_group_1_middleware_not_called(request):
        global MIDDLEWARE_INVOKE_COUNTER
        MIDDLEWARE_INVOKE_COUNTER["request"] += 1

    @blueprint_3.route("/")
    def blueprint_3_default_route(request):
        return text("BP3_OK")

    blueprint_group_2 = Blueprint.group(
        blueprint_group_1, blueprint_3, url_prefix="/api"
    )

    @blueprint_group_2.middleware("response")
    def blueprint_group_2_middleware(request, response):
        global MIDDLEWARE_INVOKE_COUNTER
        MIDDLEWARE_INVOKE_COUNTER["response"] += 1

    app.blueprint(blueprint_group_2)

    @app.route("/")
    def app_default_route(request):
        return text("APP_OK")

    _, response = app.test_client.get("/")
    assert response.text == "APP_OK"

    _, response = app.test_client.get("/api/bp/bp1")
    assert response.text == "BP1_OK"

    _, response = app.test_client.get("/api/bp/bp2")
    assert response.text == "BP2_OK"

    _, response = app.test_client.get("/api/bp3")
    assert response.text == "BP3_OK"

    assert MIDDLEWARE_INVOKE_COUNTER["response"] == 3
    assert MIDDLEWARE_INVOKE_COUNTER["request"] == 4


def test_bp_group_list_operations(app: Sanic):
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")

    @blueprint_1.route("/")
    def blueprint_1_default_route(request):
        return text("BP1_OK")

    @blueprint_2.route("/")
    def blueprint_2_default_route(request):
        return text("BP2_OK")

    blueprint_group_1 = Blueprint.group(
        blueprint_1, blueprint_2, url_prefix="/bp"
    )

    blueprint_3 = Blueprint("blueprint_2", url_prefix="/bp3")

    @blueprint_3.route("/second")
    def blueprint_3_second_route(request):
        return text("BP3_OK")

    assert len(blueprint_group_1) == 2

    blueprint_group_1.append(blueprint_3)
    assert len(blueprint_group_1) == 3

    del blueprint_group_1[2]
    assert len(blueprint_group_1) == 2

    blueprint_group_1[1] = blueprint_3
    assert len(blueprint_group_1) == 2

    assert blueprint_group_1.url_prefix == "/bp"


def test_bp_group_as_list():
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")
    blueprint_group_1 = Blueprint.group([blueprint_1, blueprint_2])
    assert len(blueprint_group_1) == 2


def test_bp_group_as_nested_group():
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")
    blueprint_group_1 = Blueprint.group(
        Blueprint.group(blueprint_1, blueprint_2)
    )
    assert len(blueprint_group_1) == 2


def test_blueprint_group_insert():
    blueprint_1 = Blueprint(
        "blueprint_1", url_prefix="/bp1", strict_slashes=True, version=1
    )
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")
    blueprint_3 = Blueprint("blueprint_3", url_prefix=None)
    group = BlueprintGroup(
        url_prefix="/test", version=1.3, strict_slashes=False
    )
    group.insert(0, blueprint_1)
    group.insert(0, blueprint_2)
    group.insert(0, blueprint_3)
    assert group.blueprints[1].strict_slashes is False
    assert group.blueprints[2].strict_slashes is True
    assert group.blueprints[0].url_prefix == "/test"
