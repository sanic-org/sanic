import asyncio
import inspect
import os

import pytest

from sanic.app import Sanic
from sanic.blueprints import Blueprint
from sanic.constants import HTTP_METHODS
from sanic.exceptions import BadRequest, NotFound, SanicException, ServerError
from sanic.request import Request
from sanic.response import json, text


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_bp(app: Sanic):
    bp = Blueprint("test_text")

    @bp.route("/")
    def handler(request):
        return text("Hello")

    app.blueprint(bp)
    request, response = app.test_client.get("/")

    assert response.text == "Hello"


def test_bp_app_access(app: Sanic):
    bp = Blueprint("test")

    with pytest.raises(
        SanicException,
        match="<Blueprint test> has not yet been registered to an app",
    ):
        bp.apps

    app.blueprint(bp)

    assert app in bp.apps


@pytest.fixture(scope="module")
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, "static")
    return static_directory


def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), "rb") as file:
        return file.read()


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_versioned_routes_get(app, method):
    bp = Blueprint("test_text")

    method = method.lower()

    func = getattr(bp, method)
    if callable(func):

        @func(f"/{method}", version=1)
        def handler(request):
            return text("OK")

    else:
        raise Exception(f"{func} is not callable")

    app.blueprint(bp)

    client_method = getattr(app.test_client, method)

    request, response = client_method(f"/v1/{method}")
    assert response.status == 200


def test_bp_strict_slash(app: Sanic):
    bp = Blueprint("test_text")

    @bp.get("/get", strict_slashes=True)
    def get_handler(request):
        return text("OK")

    @bp.post("/post/", strict_slashes=True)
    def post_handler(request):
        return text("OK")

    app.blueprint(bp)

    request, response = app.test_client.get("/get")
    assert response.text == "OK"
    assert response.json is None

    request, response = app.test_client.get("/get/")
    assert response.status == 404

    request, response = app.test_client.post("/post/")
    assert response.text == "OK"

    request, response = app.test_client.post("/post")
    assert response.status == 404


def test_bp_strict_slash_default_value(app: Sanic):
    bp = Blueprint("test_text", strict_slashes=True)

    @bp.get("/get")
    def get_handler(request):
        return text("OK")

    @bp.post("/post/")
    def post_handler(request):
        return text("OK")

    app.blueprint(bp)

    request, response = app.test_client.get("/get/")
    assert response.status == 404

    request, response = app.test_client.post("/post")
    assert response.status == 404


def test_bp_strict_slash_without_passing_default_value(app: Sanic):
    bp = Blueprint("test_text")

    @bp.get("/get")
    def get_handler(request):
        return text("OK")

    @bp.post("/post/")
    def post_handler(request):
        return text("OK")

    app.blueprint(bp)

    request, response = app.test_client.get("/get/")
    assert response.text == "OK"

    request, response = app.test_client.post("/post")
    assert response.text == "OK"


def test_bp_strict_slash_default_value_can_be_overwritten(app: Sanic):
    bp = Blueprint("test_text", strict_slashes=True)

    @bp.get("/get", strict_slashes=False)
    def get_handler(request):
        return text("OK")

    @bp.post("/post/", strict_slashes=False)
    def post_handler(request):
        return text("OK")

    app.blueprint(bp)

    request, response = app.test_client.get("/get/")
    assert response.text == "OK"

    request, response = app.test_client.post("/post")
    assert response.text == "OK"


def test_bp_with_url_prefix(app: Sanic):
    bp = Blueprint("test_text", url_prefix="/test1")

    @bp.route("/")
    def handler(request):
        return text("Hello")

    app.blueprint(bp)
    request, response = app.test_client.get("/test1/")

    assert response.text == "Hello"


def test_several_bp_with_url_prefix(app: Sanic):
    bp = Blueprint("test_text", url_prefix="/test1")
    bp2 = Blueprint("test_text2", url_prefix="/test2")

    @bp.route("/")
    def handler(request):
        return text("Hello")

    @bp2.route("/")
    def handler2(request):
        return text("Hello2")

    app.blueprint(bp)
    app.blueprint(bp2)
    request, response = app.test_client.get("/test1/")
    assert response.text == "Hello"

    request, response = app.test_client.get("/test2/")
    assert response.text == "Hello2"


def test_bp_with_host(app: Sanic):
    bp = Blueprint("test_bp_host", url_prefix="/test1", host="example.com")

    @bp.route("/")
    def handler1(request):
        return text("Hello")

    @bp.route("/", host="sub.example.com")
    def handler2(request):
        return text("Hello subdomain!")

    app.blueprint(bp)
    headers = {"Host": "example.com"}

    request, response = app.test_client.get("/test1/", headers=headers)
    assert response.text == "Hello"

    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get("/test1/", headers=headers)
    assert response.body == b"Hello subdomain!"


def test_several_bp_with_host(app: Sanic):
    bp = Blueprint(
        "test_text",
        url_prefix="/test",
        host="example.com",
        strict_slashes=True,
    )
    bp2 = Blueprint(
        "test_text2",
        url_prefix="/test",
        host="sub.example.com",
        strict_slashes=True,
    )

    @bp.route("/")
    def handler(request):
        return text("Hello")

    @bp2.route("/")
    def handler1(request):
        return text("Hello2")

    @bp2.route("/other/")
    def handler2(request):
        return text("Hello3")

    app.blueprint(bp)
    app.blueprint(bp2)

    assert bp.host == "example.com"
    headers = {"Host": "example.com"}
    request, response = app.test_client.get("/test/", headers=headers)

    assert response.text == "Hello"

    assert bp2.host == "sub.example.com"
    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get("/test/", headers=headers)

    assert response.text == "Hello2"
    request, response = app.test_client.get("/test/other/", headers=headers)
    assert response.text == "Hello3"


def test_bp_with_host_list(app: Sanic):
    bp = Blueprint(
        "test_bp_host",
        url_prefix="/test1",
        host=["example.com", "sub.example.com"],
    )

    @bp.route("/")
    def handler1(request):
        return text("Hello")

    @bp.route("/", host=["sub1.example.com"])
    def handler2(request):
        return text("Hello subdomain!")

    app.blueprint(bp)
    headers = {"Host": "example.com"}
    request, response = app.test_client.get("/test1/", headers=headers)
    assert response.text == "Hello"

    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get("/test1/", headers=headers)
    assert response.text == "Hello"

    headers = {"Host": "sub1.example.com"}
    request, response = app.test_client.get("/test1/", headers=headers)

    assert response.text == "Hello subdomain!"


def test_several_bp_with_host_list(app: Sanic):
    bp = Blueprint(
        "test_text",
        url_prefix="/test",
        host=["example.com", "sub.example.com"],
    )
    bp2 = Blueprint(
        "test_text2",
        url_prefix="/test",
        host=["sub1.example.com", "sub2.example.com"],
    )

    @bp.route("/")
    def handler(request):
        return text("Hello")

    @bp2.route("/")
    def handler1(request):
        return text("Hello2")

    @bp2.route("/other/")
    def handler2(request):
        return text("Hello3")

    app.blueprint(bp)
    app.blueprint(bp2)

    assert bp.host == ["example.com", "sub.example.com"]
    headers = {"Host": "example.com"}
    request, response = app.test_client.get("/test/", headers=headers)
    assert response.text == "Hello"

    assert bp.host == ["example.com", "sub.example.com"]
    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get("/test/", headers=headers)
    assert response.text == "Hello"

    assert bp2.host == ["sub1.example.com", "sub2.example.com"]
    headers = {"Host": "sub1.example.com"}
    request, response = app.test_client.get("/test/", headers=headers)
    assert response.text == "Hello2"
    request, response = app.test_client.get("/test/other/", headers=headers)
    assert response.text == "Hello3"

    assert bp2.host == ["sub1.example.com", "sub2.example.com"]
    headers = {"Host": "sub2.example.com"}
    request, response = app.test_client.get("/test/", headers=headers)
    assert response.text == "Hello2"
    request, response = app.test_client.get("/test/other/", headers=headers)
    assert response.text == "Hello3"


def test_bp_middleware(app: Sanic):
    blueprint = Blueprint("test_bp_middleware")

    @blueprint.middleware("response")
    async def process_response(request, response):
        return text("OK")

    @app.route("/")
    async def handler(request):
        return text("FAIL")

    app.blueprint(blueprint)

    request, response = app.test_client.get("/")

    assert response.status == 200
    assert response.text == "FAIL"


def test_bp_middleware_with_route(app: Sanic):
    blueprint = Blueprint("test_bp_middleware")

    @blueprint.middleware("response")
    async def process_response(request, response):
        return text("OK")

    @app.route("/")
    async def handler(request):
        return text("FAIL")

    @blueprint.route("/bp")
    async def bp_handler(request):
        return text("FAIL")

    app.blueprint(blueprint)

    request, response = app.test_client.get("/bp")

    assert response.status == 200
    assert response.text == "OK"


def test_bp_middleware_order(app: Sanic):
    blueprint = Blueprint("test_bp_middleware_order")
    order = []

    @blueprint.middleware("request")
    def mw_1(request):
        order.append(1)

    @blueprint.middleware("request")
    def mw_2(request):
        order.append(2)

    @blueprint.middleware("request")
    def mw_3(request):
        order.append(3)

    @blueprint.middleware("response")
    def mw_4(request, response):
        order.append(6)

    @blueprint.middleware("response")
    def mw_5(request, response):
        order.append(5)

    @blueprint.middleware("response")
    def mw_6(request, response):
        order.append(4)

    @blueprint.route("/")
    def process_response(request):
        return text("OK")

    app.blueprint(blueprint)
    order.clear()
    request, response = app.test_client.get("/")

    assert response.status == 200
    assert order == [1, 2, 3, 4, 5, 6]


def test_bp_exception_handler(app: Sanic):
    blueprint = Blueprint("test_middleware")

    @blueprint.route("/1")
    def handler_1(request):
        raise BadRequest("OK")

    @blueprint.route("/2")
    def handler_2(request):
        raise ServerError("OK")

    @blueprint.route("/3")
    def handler_3(request):
        raise NotFound("OK")

    @blueprint.exception(NotFound, ServerError)
    def handler_exception(request, exception):
        return text("OK")

    app.blueprint(blueprint)

    request, response = app.test_client.get("/1")
    assert response.status == 400

    request, response = app.test_client.get("/2")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.get("/3")
    assert response.status == 200


def test_bp_exception_handler_applied(app: Sanic):
    class Error(Exception):
        pass

    handled = Blueprint("handled")
    nothandled = Blueprint("nothandled")

    @handled.exception(Error)
    def handle_error(req, e):
        return text("handled {}".format(e))

    @handled.route("/ok")
    def ok(request):
        raise Error("uh oh")

    @nothandled.route("/notok")
    def notok(request):
        raise Error("uh oh")

    app.blueprint(handled)
    app.blueprint(nothandled)

    _, response = app.test_client.get("/ok")
    assert response.status == 200
    assert response.text == "handled uh oh"

    _, response = app.test_client.get("/notok")
    assert response.status == 500


def test_bp_exception_handler_not_applied(app: Sanic):
    class Error(Exception):
        pass

    handled = Blueprint("handled")
    nothandled = Blueprint("nothandled")

    @handled.exception(Error)
    def handle_error(req, e):
        return text("handled {}".format(e))

    @nothandled.route("/notok")
    def notok(request):
        raise Error("uh oh")

    app.blueprint(handled)
    app.blueprint(nothandled)

    _, response = app.test_client.get("/notok")
    assert response.status == 500


def test_bp_listeners(app: Sanic):
    app.route("/")(lambda x: x)
    blueprint = Blueprint("test_middleware")

    order = []

    @blueprint.listener("before_server_start")
    def handler_1(sanic, loop):
        order.append(1)

    @blueprint.listener("after_server_start")
    def handler_2(sanic, loop):
        order.append(2)

    @blueprint.listener("after_server_start")
    def handler_3(sanic, loop):
        order.append(3)

    @blueprint.listener("before_server_stop")
    def handler_4(sanic, loop):
        order.append(5)

    @blueprint.listener("before_server_stop")
    def handler_5(sanic, loop):
        order.append(4)

    @blueprint.listener("after_server_stop")
    def handler_6(sanic, loop):
        order.append(6)

    app.blueprint(blueprint)

    request, response = app.test_client.get("/")

    assert order == [1, 2, 3, 4, 5, 6]


def test_bp_static(app: Sanic):
    current_file = inspect.getfile(inspect.currentframe())
    with open(current_file, "rb") as file:
        current_file_contents = file.read()

    blueprint = Blueprint("test_static")

    blueprint.static("/testing.file", current_file)

    app.blueprint(blueprint)

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == current_file_contents


@pytest.mark.parametrize("file_name", ["test.html"])
def test_bp_static_content_type(app, file_name):
    # This is done here, since no other test loads a file here
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, "static")

    blueprint = Blueprint("test_static")
    blueprint.static(
        "/testing.file",
        get_file_path(static_directory, file_name),
        content_type="text/html; charset=utf-8",
    )

    app.blueprint(blueprint)

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == get_file_content(static_directory, file_name)
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_bp_shorthand(app: Sanic):
    blueprint = Blueprint("test_shorhand_routes")
    ev = asyncio.Event()

    @blueprint.get("/get")
    def handler(request):
        return text("OK")

    @blueprint.put("/put")
    def put_handler(request):
        return text("OK")

    @blueprint.post("/post")
    def post_handler(request):
        return text("OK")

    @blueprint.head("/head")
    def head_handler(request):
        return text("OK")

    @blueprint.options("/options")
    def options_handler(request):
        return text("OK")

    @blueprint.patch("/patch")
    def patch_handler(request):
        return text("OK")

    @blueprint.delete("/delete")
    def delete_handler(request):
        return text("OK")

    @blueprint.websocket("/ws/", strict_slashes=True)
    async def websocket_handler(request, ws):
        ev.set()

    app.blueprint(blueprint)

    request, response = app.test_client.get("/get")
    assert response.body == b"OK"

    request, response = app.test_client.post("/get")
    assert response.status == 405

    request, response = app.test_client.put("/put")
    assert response.body == b"OK"

    request, response = app.test_client.get("/post")
    assert response.status == 405

    request, response = app.test_client.post("/post")
    assert response.body == b"OK"

    request, response = app.test_client.get("/post")
    assert response.status == 405

    request, response = app.test_client.head("/head")
    assert response.status == 200

    request, response = app.test_client.get("/head")
    assert response.status == 405

    request, response = app.test_client.options("/options")
    assert response.body == b"OK"

    request, response = app.test_client.get("/options")
    assert response.status == 405

    request, response = app.test_client.patch("/patch")
    assert response.body == b"OK"

    request, response = app.test_client.get("/patch")
    assert response.status == 405

    request, response = app.test_client.delete("/delete")
    assert response.body == b"OK"

    request, response = app.test_client.get("/delete")
    assert response.status == 405

    request, response = app.test_client.websocket("/ws/")
    assert response.opened is True
    assert ev.is_set()


def test_bp_group(app: Sanic):
    deep_0 = Blueprint("deep_0", url_prefix="/deep")
    deep_1 = Blueprint("deep_1", url_prefix="/deep1")

    @deep_0.route("/")
    def handler(request):
        return text("D0_OK")

    @deep_1.route("/bottom")
    def bottom_handler(request):
        return text("D1B_OK")

    mid_0 = Blueprint.group(deep_0, deep_1, url_prefix="/mid")
    mid_1 = Blueprint("mid_tier", url_prefix="/mid1")

    @mid_1.route("/")
    def handler1(request):
        return text("M1_OK")

    top = Blueprint.group(mid_0, mid_1)

    app.blueprint(top)

    @app.route("/")
    def handler2(request):
        return text("TOP_OK")

    request, response = app.test_client.get("/")
    assert response.text == "TOP_OK"

    request, response = app.test_client.get("/mid1")
    assert response.text == "M1_OK"

    request, response = app.test_client.get("/mid/deep")
    assert response.text == "D0_OK"

    request, response = app.test_client.get("/mid/deep1/bottom")
    assert response.text == "D1B_OK"


def test_bp_group_with_default_url_prefix(app: Sanic):
    from sanic.response import json

    bp_resources = Blueprint("bp_resources")

    @bp_resources.get("/")
    def list_resources_handler(request):
        resource = {}
        return json([resource])

    bp_resource = Blueprint("bp_resource", url_prefix="/<resource_id>")

    @bp_resource.get("/")
    def get_resource_hander(request, resource_id):
        resource = {"resource_id": resource_id}
        return json(resource)

    bp_resources_group = Blueprint.group(
        bp_resources, bp_resource, url_prefix="/resources"
    )
    bp_api_v1 = Blueprint("bp_api_v1")

    @bp_api_v1.get("/info")
    def api_v1_info(request):
        return text("api_version: v1")

    bp_api_v1_group = Blueprint.group(
        bp_api_v1, bp_resources_group, url_prefix="/v1"
    )
    bp_api_group = Blueprint.group(bp_api_v1_group, url_prefix="/api")
    app.blueprint(bp_api_group)

    request, response = app.test_client.get("/api/v1/info")
    assert response.text == "api_version: v1"

    request, response = app.test_client.get("/api/v1/resources")
    assert response.json == [{}]

    from uuid import uuid4

    resource_id = str(uuid4())
    request, response = app.test_client.get(f"/api/v1/resources/{resource_id}")
    assert response.json == {"resource_id": resource_id}


def test_blueprint_middleware_with_args(app: Sanic):
    bp = Blueprint(name="with_args_bp", url_prefix="/wa")

    @bp.middleware
    def middleware_with_no_tag(request: Request):
        if request.headers.get("content-type") == "application/json":
            request.headers["accepts"] = "plain/text"
        else:
            request.headers["accepts"] = "application/json"

    @bp.route("/")
    def default_route(request):
        if request.headers.get("accepts") == "application/json":
            return json({"test": "value"})
        else:
            return text("value")

    app.blueprint(bp)

    _, response = app.test_client.get(
        "/wa", headers={"content-type": "application/json"}
    )
    assert response.text == "value"

    _, response = app.test_client.get(
        "/wa", headers={"content-type": "plain/text"}
    )
    assert response.json.get("test") == "value"


@pytest.mark.parametrize("file_name", ["test.file"])
def test_static_blueprint_name(static_file_directory, file_name):
    app = Sanic("app")
    current_file = inspect.getfile(inspect.currentframe())
    with open(current_file, "rb") as file:
        file.read()

    bp = Blueprint(name="static", url_prefix="/static", strict_slashes=False)

    bp.static(
        "/test.file/",
        get_file_path(static_file_directory, file_name),
        name="static.testing",
        strict_slashes=True,
    )

    app.blueprint(bp)

    uri = app.url_for("static", name="static.testing")
    assert uri == "/static/test.file/"

    _, response = app.test_client.get("/static/test.file")
    assert response.status == 404

    _, response = app.test_client.get("/static/test.file/")
    assert response.status == 200


@pytest.mark.parametrize("file_name", ["test.file"])
def test_static_blueprintp_mw(app: Sanic, static_file_directory, file_name):
    current_file = inspect.getfile(inspect.currentframe())  # type: ignore
    with open(current_file, "rb") as file:
        file.read()

    triggered = False

    bp = Blueprint(name="test_mw", url_prefix="")

    @bp.middleware("request")
    def bp_mw1(request):
        nonlocal triggered
        triggered = True

    bp.static(
        "/test.file",
        get_file_path(static_file_directory, file_name),
        strict_slashes=True,
        name="static",
    )

    app.blueprint(bp)

    uri = app.url_for("test_mw.static")
    assert uri == "/test.file"

    _, response = app.test_client.get("/test.file")
    assert triggered is True


def test_websocket_route(app: Sanic):
    event = asyncio.Event()

    async def websocket_handler(request, ws):
        assert ws.subprotocol is None
        event.set()

    bp = Blueprint(name="handler", url_prefix="/ws")
    bp.add_websocket_route(websocket_handler, "/test", name="test")

    app.blueprint(bp)

    _, response = app.test_client.websocket("/ws/test")
    assert response.opened is True
    assert event.is_set()


def test_duplicate_blueprint(app: Sanic):
    bp_name = "bp"
    bp = Blueprint(bp_name)
    bp1 = Blueprint(bp_name)

    app.blueprint(bp)

    with pytest.raises(AssertionError) as excinfo:
        app.blueprint(bp1)

    assert str(excinfo.value) == (
        f'A blueprint with the name "{bp_name}" is already registered.  '
        "Blueprint names must be unique."
    )


def test_strict_slashes_behavior_adoption():
    app = Sanic("app")
    app.strict_slashes = True
    bp = Blueprint("bp")
    bp2 = Blueprint("bp2", strict_slashes=False)

    @app.get("/test")
    def handler_test(request):
        return text("Test")

    @app.get("/f1", strict_slashes=False)
    def f1(request):
        return text("f1")

    @bp.get("/one", strict_slashes=False)
    def one(request):
        return text("one")

    @bp.get("/second")
    def second(request):
        return text("second")

    @bp2.get("/third")
    def third(request):
        return text("third")

    app.blueprint(bp)
    app.blueprint(bp2)

    assert app.test_client.get("/test")[1].status == 200
    assert app.test_client.get("/test/")[1].status == 404

    assert app.test_client.get("/one")[1].status == 200
    assert app.test_client.get("/one/")[1].status == 200

    assert app.test_client.get("/second")[1].status == 200
    assert app.test_client.get("/second/")[1].status == 404

    assert app.test_client.get("/third")[1].status == 200
    assert app.test_client.get("/third/")[1].status == 200

    assert app.test_client.get("/f1")[1].status == 200
    assert app.test_client.get("/f1/")[1].status == 200


def test_blueprint_group_versioning():
    app = Sanic(name="blueprint-group-test")

    bp1 = Blueprint(name="bp1", url_prefix="/bp1")
    bp2 = Blueprint(name="bp2", url_prefix="/bp2", version=2)

    bp3 = Blueprint(name="bp3", url_prefix="/bp3")

    @bp3.get("/r1")
    async def bp3_r1(request):
        return json({"from": "bp3/r1"})

    @bp1.get("/pre-group")
    async def pre_group(request):
        return json({"from": "bp1/pre-group"})

    group = Blueprint.group([bp1, bp2], url_prefix="/group1", version=1)

    group2 = Blueprint.group([bp3])

    @bp1.get("/r1")
    async def r1(request):
        return json({"from": "bp1/r1"})

    @bp2.get("/r2")
    async def r2(request):
        return json({"from": "bp2/r2"})

    @bp2.get("/r3", version=3)
    async def r3(request):
        return json({"from": "bp2/r3"})

    app.blueprint([group, group2])

    assert app.test_client.get("/v1/group1/bp1/r1/")[1].status == 200
    assert app.test_client.get("/v2/group1/bp2/r2")[1].status == 200
    assert app.test_client.get("/v1/group1/bp1/pre-group")[1].status == 200
    assert app.test_client.get("/v3/group1/bp2/r3")[1].status == 200
    assert app.test_client.get("/bp3/r1")[1].status == 200

    assert group.version == 1
    assert group2.strict_slashes is None


def test_blueprint_group_strict_slashes():
    app = Sanic(name="blueprint-group-test")
    bp1 = Blueprint(name="bp1", url_prefix=None, strict_slashes=False)

    bp2 = Blueprint(
        name="bp2", version=3, url_prefix="/bp2", strict_slashes=None
    )

    bp3 = Blueprint(
        name="bp3", version=None, url_prefix="/bp3/", strict_slashes=None
    )

    @bp1.get("/r1")
    async def bp1_r1(request):
        return json({"from": "bp1/r1"})

    @bp2.get("/r1")
    async def bp2_r1(request):
        return json({"from": "bp2/r1"})

    @bp2.get("/r2/")
    async def bp2_r2(request):
        return json({"from": "bp2/r2"})

    @bp3.get("/r1")
    async def bp3_r1(request):
        return json({"from": "bp3/r1"})

    group = Blueprint.group(
        [bp1, bp2],
        url_prefix="/slash-check/",
        version=1.3,
        strict_slashes=True,
    )

    group2 = Blueprint.group(
        [bp3], url_prefix="/other-prefix/", version="v2", strict_slashes=False
    )

    app.blueprint(group)
    app.blueprint(group2)

    assert app.test_client.get("/v1.3/slash-check/r1")[1].status == 200
    assert app.test_client.get("/v1.3/slash-check/r1/")[1].status == 200
    assert app.test_client.get("/v3/slash-check/bp2/r1")[1].status == 200
    assert app.test_client.get("/v3/slash-check/bp2/r1/")[1].status == 404
    assert app.test_client.get("/v3/slash-check/bp2/r2")[1].status == 404
    assert app.test_client.get("/v3/slash-check/bp2/r2/")[1].status == 200
    assert app.test_client.get("/v2/other-prefix/bp3/r1")[1].status == 200


def test_blueprint_registered_multiple_apps():
    app1 = Sanic("app1")
    app2 = Sanic("app2")
    bp = Blueprint("bp")

    @bp.get("/")
    async def handler(request):
        return text(request.route.name)

    app1.blueprint(bp)
    app2.blueprint(bp)

    for app in (app1, app2):
        _, response = app.test_client.get("/")
        assert response.text == f"{app.name}.bp.handler"


def test_bp_set_attribute_warning():
    bp = Blueprint("bp")
    message = (
        "Setting variables on Blueprint instances is not allowed. You should "
        "change your Blueprint instance to use instance.ctx.foo instead."
    )
    with pytest.raises(AttributeError, match=message):
        bp.foo = 1


def test_early_registration(app: Sanic):
    assert len(app.router.routes) == 0

    bp = Blueprint("bp")

    @bp.get("/one")
    async def one(_):
        return text("one")

    app.blueprint(bp)

    assert len(app.router.routes) == 1

    @bp.get("/two")
    async def two(_):
        return text("two")

    @bp.get("/three")
    async def three(_):
        return text("three")

    assert len(app.router.routes) == 3

    for path in ("one", "two", "three"):
        _, response = app.test_client.get(f"/{path}")
        assert response.text == path


def test_remove_double_slashes_defined_on_bp(app: Sanic):
    bp = Blueprint("bp", url_prefix="/foo/", strict_slashes=True)

    @bp.get("/")
    async def handler(_):
        ...

    app.blueprint(bp)
    app.router.finalize()

    assert app.router.routes[0].path == "foo/"


def test_remove_double_slashes_defined_on_register(app: Sanic):
    bp = Blueprint("bp")

    @bp.get("/")
    async def index(_):
        ...

    app.blueprint(bp, url_prefix="/foo/", strict_slashes=True)
    app.router.finalize()

    assert app.router.routes[0].path == "foo/"
