from sanic import Sanic
from sanic.response import text
from sanic.exceptions import InvalidUsage, ServerError, NotFound
from sanic.utils import sanic_endpoint_test

# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

exception_app = Sanic('test_exceptions')


@exception_app.route('/')
def handler(request):
    return text('OK')


@exception_app.route('/error')
def handler_error(request):
    raise ServerError("OK")


@exception_app.route('/404')
def handler_404(request):
    raise NotFound("OK")


@exception_app.route('/invalid')
def handler_invalid(request):
    raise InvalidUsage("OK")


def test_no_exception():
    request, response = sanic_endpoint_test(exception_app)
    assert response.status == 200
    assert response.text == 'OK'


def test_server_error_exception():
    request, response = sanic_endpoint_test(exception_app, uri='/error')
    assert response.status == 500


def test_invalid_usage_exception():
    request, response = sanic_endpoint_test(exception_app, uri='/invalid')
    assert response.status == 400


def test_not_found_exception():
    request, response = sanic_endpoint_test(exception_app, uri='/404')
    assert response.status == 404
