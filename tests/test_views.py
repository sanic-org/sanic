import pytest as pytest

from sanic import Sanic
from sanic.response import text, HTTPResponse
from sanic.views import HTTPMethodView
from sanic.blueprints import Blueprint
from sanic.request import Request
from sanic.utils import sanic_endpoint_test
from sanic.constants import HTTP_METHODS


@pytest.mark.parametrize('method', HTTP_METHODS)
def test_methods(method):
    app = Sanic('test_methods')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am GET method')

        def post(self, request):
            return text('I am POST method')

        def put(self, request):
            return text('I am PUT method')

        def head(self, request):
            return text('I am HEAD method')

        def options(self, request):
            return text('I am OPTIONS method')

        def patch(self, request):
            return text('I am PATCH method')

        def delete(self, request):
            return text('I am DELETE method')

    app.add_route(DummyView.as_view(), '/')

    request, response = sanic_endpoint_test(app, method=method)
    assert response.text == 'I am {} method'.format(method)


def test_unexisting_methods():
    app = Sanic('test_unexisting_methods')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView.as_view(), '/')
    request, response = sanic_endpoint_test(app, method="get")
    assert response.text == 'I am get method'
    request, response = sanic_endpoint_test(app, method="post")
    assert response.text == 'Error: Method POST not allowed for URL /'


def test_argument_methods():
    app = Sanic('test_argument_methods')

    class DummyView(HTTPMethodView):

        def get(self, request, my_param_here):
            return text('I am get method with %s' % my_param_here)

    app.add_route(DummyView.as_view(), '/<my_param_here>')

    request, response = sanic_endpoint_test(app, uri='/test123')

    assert response.text == 'I am get method with test123'


def test_with_bp():
    app = Sanic('test_with_bp')
    bp = Blueprint('test_text')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    bp.add_route(DummyView.as_view(), '/')

    app.blueprint(bp)
    request, response = sanic_endpoint_test(app)

    assert response.text == 'I am get method'


def test_with_bp_with_url_prefix():
    app = Sanic('test_with_bp_with_url_prefix')
    bp = Blueprint('test_text', url_prefix='/test1')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    bp.add_route(DummyView.as_view(), '/')

    app.blueprint(bp)
    request, response = sanic_endpoint_test(app, uri='/test1/')

    assert response.text == 'I am get method'


def test_with_middleware():
    app = Sanic('test_with_middleware')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView.as_view(), '/')

    results = []

    @app.middleware
    async def handler(request):
        results.append(request)

    request, response = sanic_endpoint_test(app)

    assert response.text == 'I am get method'
    assert type(results[0]) is Request


def test_with_middleware_response():
    app = Sanic('test_with_middleware_response')

    results = []

    @app.middleware('request')
    async def process_response(request):
        results.append(request)

    @app.middleware('response')
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView.as_view(), '/')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'I am get method'
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert isinstance(results[2], HTTPResponse)


def test_with_custom_class_methods():
    app = Sanic('test_with_custom_class_methods')

    class DummyView(HTTPMethodView):
        global_var = 0

        def _iternal_method(self):
            self.global_var += 10

        def get(self, request):
            self._iternal_method()
            return text('I am get method and global var is {}'.format(self.global_var))

    app.add_route(DummyView.as_view(), '/')
    request, response = sanic_endpoint_test(app, method="get")
    assert response.text == 'I am get method and global var is 10'


def test_with_decorator():
    app = Sanic('test_with_decorator')

    results = []

    def stupid_decorator(view):
        def decorator(*args, **kwargs):
            results.append(1)
            return view(*args, **kwargs)
        return decorator

    class DummyView(HTTPMethodView):
        decorators = [stupid_decorator]

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView.as_view(), '/')
    request, response = sanic_endpoint_test(app, method="get")
    assert response.text == 'I am get method'
    assert results[0] == 1
