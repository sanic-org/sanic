from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic import Blueprint
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test
from sanic.exceptions import SanicException


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

