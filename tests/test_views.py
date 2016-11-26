from sanic import Sanic
from sanic.response import text, HTTPResponse
from sanic.views import HTTPMethodView
from sanic.blueprints import Blueprint
from sanic.request import Request
from sanic.utils import sanic_endpoint_test


def test_methods():
    app = Sanic('test_methods')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

        def post(self, request):
            return text('I am post method')

        def put(self, request):
            return text('I am put method')

        def patch(self, request):
            return text('I am patch method')

        def delete(self, request):
            return text('I am delete method')

    app.add_route(DummyView(), '/')

    request, response = sanic_endpoint_test(app, method="get")
    assert response.text == 'I am get method'
    request, response = sanic_endpoint_test(app, method="post")
    assert response.text == 'I am post method'
    request, response = sanic_endpoint_test(app, method="put")
    assert response.text == 'I am put method'
    request, response = sanic_endpoint_test(app, method="patch")
    assert response.text == 'I am patch method'
    request, response = sanic_endpoint_test(app, method="delete")
    assert response.text == 'I am delete method'


def test_unexisting_methods():
    app = Sanic('test_unexisting_methods')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView(), '/')
    request, response = sanic_endpoint_test(app, method="get")
    assert response.text == 'I am get method'
    request, response = sanic_endpoint_test(app, method="post")
    assert response.text == 'Error: Method POST not allowed for URL /'


def test_argument_methods():
    app = Sanic('test_argument_methods')

    class DummyView(HTTPMethodView):

        def get(self, request, my_param_here):
            return text('I am get method with %s' % my_param_here)

    app.add_route(DummyView(), '/<my_param_here>')

    request, response = sanic_endpoint_test(app, uri='/test123')

    assert response.text == 'I am get method with test123'


def test_with_bp():
    app = Sanic('test_with_bp')
    bp = Blueprint('test_text')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    bp.add_route(DummyView(), '/')

    app.blueprint(bp)
    request, response = sanic_endpoint_test(app)

    assert response.text == 'I am get method'


def test_with_bp_with_url_prefix():
    app = Sanic('test_with_bp_with_url_prefix')
    bp = Blueprint('test_text', url_prefix='/test1')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    bp.add_route(DummyView(), '/')

    app.blueprint(bp)
    request, response = sanic_endpoint_test(app, uri='/test1/')

    assert response.text == 'I am get method'


def test_with_middleware():
    app = Sanic('test_with_middleware')

    class DummyView(HTTPMethodView):

        def get(self, request):
            return text('I am get method')

    app.add_route(DummyView(), '/')

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

    app.add_route(DummyView(), '/')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'I am get method'
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert issubclass(type(results[2]), HTTPResponse)
