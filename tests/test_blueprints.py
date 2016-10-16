from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test
from sanic.exceptions import NotFound, ServerError, InvalidUsage


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_bp():
    app = Sanic('test_text')
    bp = Blueprint('test_text')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    app.register_blueprint(bp)
    request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'

def test_bp_with_url_prefix():
    app = Sanic('test_text')
    bp = Blueprint('test_text', url_prefix='/test1')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    app.register_blueprint(bp)
    request, response = sanic_endpoint_test(app, uri='/test1/')

    assert response.text == 'Hello'


def test_several_bp_with_url_prefix():
    app = Sanic('test_text')
    bp = Blueprint('test_text', url_prefix='/test1')
    bp2 = Blueprint('test_text2', url_prefix='/test2')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    @bp2.route('/')
    def handler2(request):
        return text('Hello2')

    app.register_blueprint(bp)
    app.register_blueprint(bp2)
    request, response = sanic_endpoint_test(app, uri='/test1/')
    assert response.text == 'Hello'

    request, response = sanic_endpoint_test(app, uri='/test2/')
    assert response.text == 'Hello2'


def test_bp_middleware():
    app = Sanic('test_middleware')
    blueprint = Blueprint('test_middleware')

    @blueprint.middleware('response')
    async def process_response(request, response):
        return text('OK')

    @app.route('/')
    async def handler(request):
        return text('FAIL')

    app.register_blueprint(blueprint)

    request, response = sanic_endpoint_test(app)

    assert response.status == 200
    assert response.text == 'OK'

def test_bp_exception_handler():
    app = Sanic('test_middleware')
    blueprint = Blueprint('test_middleware')

    @blueprint.route('/1')
    def handler_1(request):
        raise InvalidUsage("OK")

    @blueprint.route('/2')
    def handler_2(request):
        raise ServerError("OK")

    @blueprint.route('/3')
    def handler_3(request):
        raise NotFound("OK")

    @blueprint.exception(NotFound, ServerError)
    def handler_exception(request, exception):
        return text("OK")

    app.register_blueprint(blueprint)

    request, response = sanic_endpoint_test(app, uri='/1')
    assert response.status == 400


    request, response = sanic_endpoint_test(app, uri='/2')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = sanic_endpoint_test(app, uri='/3')
    assert response.status == 200