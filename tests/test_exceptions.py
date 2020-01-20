import pytest

from bs4 import BeautifulSoup

from sanic import Sanic
from sanic.exceptions import (
    Forbidden,
    InvalidUsage,
    NotFound,
    ServerError,
    Unauthorized,
    abort,
)
from sanic.response import text


class SanicExceptionTestException(Exception):
    pass


@pytest.fixture(scope="module")
def exception_app():
    app = Sanic("test_exceptions")

    @app.route("/")
    def handler(request):
        return text("OK")

    @app.route("/error")
    def handler_error(request):
        raise ServerError("OK")

    @app.route("/404")
    def handler_404(request):
        raise NotFound("OK")

    @app.route("/403")
    def handler_403(request):
        raise Forbidden("Forbidden")

    @app.route("/401")
    def handler_401(request):
        raise Unauthorized("Unauthorized")

    @app.route("/401/basic")
    def handler_401_basic(request):
        raise Unauthorized("Unauthorized", scheme="Basic", realm="Sanic")

    @app.route("/401/digest")
    def handler_401_digest(request):
        raise Unauthorized(
            "Unauthorized",
            scheme="Digest",
            realm="Sanic",
            qop="auth, auth-int",
            algorithm="MD5",
            nonce="abcdef",
            opaque="zyxwvu",
        )

    @app.route("/401/bearer")
    def handler_401_bearer(request):
        raise Unauthorized("Unauthorized", scheme="Bearer")

    @app.route("/invalid")
    def handler_invalid(request):
        raise InvalidUsage("OK")

    @app.route("/abort/401")
    def handler_401_error(request):
        abort(401)

    @app.route("/abort")
    def handler_500_error(request):
        abort(500)
        return text("OK")

    @app.route("/abort/message")
    def handler_abort_message(request):
        abort(500, message="Abort")

    @app.route("/divide_by_zero")
    def handle_unhandled_exception(request):
        _ = 1 / 0

    @app.route("/error_in_error_handler_handler")
    def custom_error_handler(request):
        raise SanicExceptionTestException("Dummy message!")

    @app.exception(SanicExceptionTestException)
    def error_in_error_handler_handler(request, exception):
        _ = 1 / 0

    return app


def test_catch_exception_list(app):
    @app.exception([SanicExceptionTestException, NotFound])
    def exception_list(request, exception):
        return text("ok")

    @app.route("/")
    def exception(request):
        raise SanicExceptionTestException("You won't see me")

    request, response = app.test_client.get("/random")
    assert response.text == "ok"

    request, response = app.test_client.get("/")
    assert response.text == "ok"


def test_no_exception(exception_app):
    """Test that a route works without an exception"""
    request, response = exception_app.test_client.get("/")
    assert response.status == 200
    assert response.text == "OK"


def test_server_error_exception(exception_app):
    """Test the built-in ServerError exception works"""
    request, response = exception_app.test_client.get("/error")
    assert response.status == 500


def test_invalid_usage_exception(exception_app):
    """Test the built-in InvalidUsage exception works"""
    request, response = exception_app.test_client.get("/invalid")
    assert response.status == 400


def test_not_found_exception(exception_app):
    """Test the built-in NotFound exception works"""
    request, response = exception_app.test_client.get("/404")
    assert response.status == 404


def test_forbidden_exception(exception_app):
    """Test the built-in Forbidden exception"""
    request, response = exception_app.test_client.get("/403")
    assert response.status == 403


def test_unauthorized_exception(exception_app):
    """Test the built-in Unauthorized exception"""
    request, response = exception_app.test_client.get("/401")
    assert response.status == 401

    request, response = exception_app.test_client.get("/401/basic")
    assert response.status == 401
    assert response.headers.get("WWW-Authenticate") is not None
    assert response.headers.get("WWW-Authenticate") == 'Basic realm="Sanic"'

    request, response = exception_app.test_client.get("/401/digest")
    assert response.status == 401

    auth_header = response.headers.get("WWW-Authenticate")
    assert auth_header is not None
    assert auth_header.startswith("Digest")
    assert 'qop="auth, auth-int"' in auth_header
    assert 'algorithm="MD5"' in auth_header
    assert 'nonce="abcdef"' in auth_header
    assert 'opaque="zyxwvu"' in auth_header

    request, response = exception_app.test_client.get("/401/bearer")
    assert response.status == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_handled_unhandled_exception(exception_app):
    """Test that an exception not built into sanic is handled"""
    request, response = exception_app.test_client.get("/divide_by_zero")
    assert response.status == 500
    soup = BeautifulSoup(response.body, "html.parser")
    assert "Internal Server Error" in soup.h1.text

    message = " ".join(soup.p.text.split())
    assert message == (
        "The server encountered an internal error and "
        "cannot complete your request."
    )


def test_exception_in_exception_handler(exception_app):
    """Test that an exception thrown in an error handler is handled"""
    request, response = exception_app.test_client.get(
        "/error_in_error_handler_handler"
    )
    assert response.status == 500
    assert response.body == b"An error occurred while handling an error"


def test_exception_in_exception_handler_debug_off(exception_app):
    """Test that an exception thrown in an error handler is handled"""
    request, response = exception_app.test_client.get(
        "/error_in_error_handler_handler", debug=False
    )
    assert response.status == 500
    assert response.body == b"An error occurred while handling an error"


def test_exception_in_exception_handler_debug_on(exception_app):
    """Test that an exception thrown in an error handler is handled"""
    request, response = exception_app.test_client.get(
        "/error_in_error_handler_handler", debug=True
    )
    assert response.status == 500
    assert response.body.startswith(b"Exception raised in exception ")


def test_abort(exception_app):
    """Test the abort function"""
    request, response = exception_app.test_client.get("/abort/401")
    assert response.status == 401

    request, response = exception_app.test_client.get("/abort")
    assert response.status == 500

    request, response = exception_app.test_client.get("/abort/message")
    assert response.status == 500
    assert "Abort" in response.text
