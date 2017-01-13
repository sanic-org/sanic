import pytest
from bs4 import BeautifulSoup

from sanic import Sanic
from sanic.response import text
from sanic.exceptions import InvalidUsage, ServerError, NotFound
from sanic.utils import sanic_endpoint_test


class SanicExceptionTestException(Exception):
    pass


@pytest.fixture(scope='module')
def exception_app():
    app = Sanic('test_exceptions')

    @app.route('/')
    def handler(request):
        return text('OK')

    @app.route('/error')
    def handler_error(request):
        raise ServerError("OK")

    @app.route('/404')
    def handler_404(request):
        raise NotFound("OK")

    @app.route('/invalid')
    def handler_invalid(request):
        raise InvalidUsage("OK")

    @app.route('/divide_by_zero')
    def handle_unhandled_exception(request):
        1 / 0

    @app.route('/error_in_error_handler_handler')
    def custom_error_handler(request):
        raise SanicExceptionTestException('Dummy message!')

    @app.exception(SanicExceptionTestException)
    def error_in_error_handler_handler(request, exception):
        1 / 0

    return app


def test_no_exception(exception_app):
    """Test that a route works without an exception"""
    request, response = sanic_endpoint_test(exception_app)
    assert response.status == 200
    assert response.text == 'OK'


def test_server_error_exception(exception_app):
    """Test the built-in ServerError exception works"""
    request, response = sanic_endpoint_test(exception_app, uri='/error')
    assert response.status == 500


def test_invalid_usage_exception(exception_app):
    """Test the built-in InvalidUsage exception works"""
    request, response = sanic_endpoint_test(exception_app, uri='/invalid')
    assert response.status == 400


def test_not_found_exception(exception_app):
    """Test the built-in NotFound exception works"""
    request, response = sanic_endpoint_test(exception_app, uri='/404')
    assert response.status == 404


def test_handled_unhandled_exception(exception_app):
    """Test that an exception not built into sanic is handled"""
    request, response = sanic_endpoint_test(
        exception_app, uri='/divide_by_zero')
    assert response.status == 500
    soup = BeautifulSoup(response.body, 'html.parser')
    assert soup.h1.text == 'Internal Server Error'

    message = " ".join(soup.p.text.split())
    assert message == (
        "The server encountered an internal error and "
        "cannot complete your request.")


def test_exception_in_exception_handler(exception_app):
    """Test that an exception thrown in an error handler is handled"""
    request, response = sanic_endpoint_test(
        exception_app, uri='/error_in_error_handler_handler')
    assert response.status == 500
    assert response.body == b'An error occurred while handling an error'
