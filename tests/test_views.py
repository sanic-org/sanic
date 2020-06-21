import pytest as pytest

from sanic.blueprints import Blueprint
from sanic.constants import HTTP_METHODS
from sanic.exceptions import InvalidUsage
from sanic.request import Request
from sanic.response import HTTPResponse, text
from sanic.views import CompositionView, HTTPMethodView


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_methods(app, method):
    class DummyView(HTTPMethodView):
        async def get(self, request):
            return text("", headers={"method": "GET"})

        def post(self, request):
            return text("", headers={"method": "POST"})

        async def put(self, request):
            return text("", headers={"method": "PUT"})

        def head(self, request):
            return text("", headers={"method": "HEAD"})

        def options(self, request):
            return text("", headers={"method": "OPTIONS"})

        async def patch(self, request):
            return text("", headers={"method": "PATCH"})

        def delete(self, request):
            return text("", headers={"method": "DELETE"})

    app.add_route(DummyView.as_view(), "/")

    request, response = getattr(app.test_client, method.lower())("/")
    assert response.headers["method"] == method


def test_unexisting_methods(app):
    class DummyView(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

    app.add_route(DummyView.as_view(), "/")
    request, response = app.test_client.get("/")
    assert response.text == "I am get method"
    request, response = app.test_client.post("/")
    assert "Method POST not allowed for URL /" in response.text


def test_argument_methods(app):
    class DummyView(HTTPMethodView):
        def get(self, request, my_param_here):
            return text("I am get method with %s" % my_param_here)

    app.add_route(DummyView.as_view(), "/<my_param_here>")

    request, response = app.test_client.get("/test123")

    assert response.text == "I am get method with test123"


def test_with_bp(app):
    bp = Blueprint("test_text")

    class DummyView(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

    bp.add_route(DummyView.as_view(), "/")

    app.blueprint(bp)
    request, response = app.test_client.get("/")

    assert response.text == "I am get method"


def test_with_bp_with_url_prefix(app):
    bp = Blueprint("test_text", url_prefix="/test1")

    class DummyView(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

    bp.add_route(DummyView.as_view(), "/")

    app.blueprint(bp)
    request, response = app.test_client.get("/test1/")

    assert response.text == "I am get method"


def test_with_middleware(app):
    class DummyView(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

    app.add_route(DummyView.as_view(), "/")

    results = []

    @app.middleware
    async def handler(request):
        results.append(request)

    request, response = app.test_client.get("/")

    assert response.text == "I am get method"
    assert type(results[0]) is Request


def test_with_middleware_response(app):
    results = []

    @app.middleware("request")
    async def process_request(request):
        results.append(request)

    @app.middleware("response")
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    class DummyView(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

    app.add_route(DummyView.as_view(), "/")

    request, response = app.test_client.get("/")

    assert response.text == "I am get method"
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert isinstance(results[2], HTTPResponse)


def test_with_custom_class_methods(app):
    class DummyView(HTTPMethodView):
        global_var = 0

        def _iternal_method(self):
            self.global_var += 10

        def get(self, request):
            self._iternal_method()
            return text(
                f"I am get method and global var " f"is {self.global_var}"
            )

    app.add_route(DummyView.as_view(), "/")
    request, response = app.test_client.get("/")
    assert response.text == "I am get method and global var is 10"


def test_with_decorator(app):
    results = []

    def stupid_decorator(view):
        def decorator(*args, **kwargs):
            results.append(1)
            return view(*args, **kwargs)

        return decorator

    class DummyView(HTTPMethodView):
        decorators = [stupid_decorator]

        def get(self, request):
            return text("I am get method")

    app.add_route(DummyView.as_view(), "/")
    request, response = app.test_client.get("/")
    assert response.text == "I am get method"
    assert results[0] == 1


def test_composition_view_rejects_incorrect_methods():
    def foo(request):
        return text("Foo")

    view = CompositionView()

    with pytest.raises(InvalidUsage) as e:
        view.add(["GET", "FOO"], foo)

    assert str(e.value) == "FOO is not a valid HTTP method."


def test_composition_view_rejects_duplicate_methods():
    def foo(request):
        return text("Foo")

    view = CompositionView()

    with pytest.raises(InvalidUsage) as e:
        view.add(["GET", "POST", "GET"], foo)

    assert str(e.value) == "Method GET is already registered."


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_composition_view_runs_methods_as_expected(app, method):
    view = CompositionView()

    def first(request):
        return text("first method")

    view.add(["GET", "POST", "PUT"], first)
    view.add(["DELETE", "PATCH"], lambda x: text("second method"))

    app.add_route(view, "/")

    if method in ["GET", "POST", "PUT"]:
        request, response = getattr(app.test_client, method.lower())("/")
        assert response.text == "first method"

        response = view(request)
        assert response.body.decode() == "first method"

    if method in ["DELETE", "PATCH"]:
        request, response = getattr(app.test_client, method.lower())("/")
        assert response.text == "second method"

        response = view(request)
        assert response.body.decode() == "second method"


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_composition_view_rejects_invalid_methods(app, method):
    view = CompositionView()
    view.add(["GET", "POST", "PUT"], lambda x: text("first method"))

    app.add_route(view, "/")

    if method in ["GET", "POST", "PUT"]:
        request, response = getattr(app.test_client, method.lower())("/")
        assert response.status == 200
        assert response.text == "first method"

    if method in ["DELETE", "PATCH"]:
        request, response = getattr(app.test_client, method.lower())("/")
        assert response.status == 405
