from sanic import Sanic
from sanic.response import text
from sanic.exceptions import InvalidUsage, ServerError, NotFound
from sanic.utils import sanic_endpoint_test

exception_handler_app = Sanic('test_exception_handler')


@exception_handler_app.route('/1')
def handler_1(request):
    raise InvalidUsage("OK")


@exception_handler_app.route('/2')
def handler_2(request):
    raise ServerError("OK")


@exception_handler_app.route('/3')
def handler_3(request):
    raise NotFound("OK")


@exception_handler_app.exception(NotFound, ServerError)
def handler_exception(request, exception):
    return text("OK")


def test_invalid_usage_exception_handler():
    request, response = sanic_endpoint_test(exception_handler_app, uri='/1')
    assert response.status == 400


def test_server_error_exception_handler():
    request, response = sanic_endpoint_test(exception_handler_app, uri='/2')
    assert response.status == 200
    assert response.text == 'OK'


def test_not_found_exception_handler():
    request, response = sanic_endpoint_test(exception_handler_app, uri='/3')
    assert response.status == 200


def test_text_exception__handler():
    request, response = sanic_endpoint_test(
        exception_handler_app, uri='/random')
    assert response.status == 200
    assert response.text == 'OK'
