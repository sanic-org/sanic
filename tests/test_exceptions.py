import logging

import pytest

from bs4 import BeautifulSoup

from sanic import Sanic
from sanic.exceptions import (
    BadRequest,
    ContentRangeError,
    ExpectationFailed,
    Forbidden,
    HeaderExpectationFailed,
    InvalidUsage,
    MethodNotAllowed,
    MethodNotSupported,
    NotFound,
    RangeNotSatisfiable,
    SanicException,
    ServerError,
    Unauthorized,
)
from sanic.response import text


def dl_to_dict(soup, css_class):
    keys, values = [], []
    for dl in soup.find_all("dl", {"class": css_class}):
        for dt in dl.find_all("dt"):
            keys.append(dt.text.strip())
        for dd in dl.find_all("dd"):
            values.append(dd.text.strip())
    return dict(zip(keys, values))


class SanicExceptionTestException(Exception):
    pass


@pytest.fixture(scope="module")
def exception_app():
    app = Sanic("test_exceptions")
    app.config.FALLBACK_ERROR_FORMAT = "html"

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
        raise BadRequest("OK")

    @app.route("/abort/401")
    def handler_401_error(request):
        raise SanicException(status_code=401)

    @app.route("/abort")
    def handler_500_error(request):
        raise SanicException(status_code=500)

    @app.route("/abort/message")
    def handler_abort_message(request):
        raise SanicException(message="Custom Message", status_code=500)

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
    """Test the built-in BadRequest exception works"""
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


def test_sanic_exception(exception_app):
    """Test sanic exceptions are handled"""
    request, response = exception_app.test_client.get("/abort/401")
    assert response.status == 401

    request, response = exception_app.test_client.get("/abort")
    assert response.status == 500
    # check fallback message
    assert "Internal Server Error" in response.text

    request, response = exception_app.test_client.get("/abort/message")
    assert response.status == 500
    assert "Custom Message" in response.text


def test_custom_exception_default_message(exception_app):
    class TeaError(SanicException):
        message = "Tempest in a teapot"
        status_code = 418

    exception_app.router.reset()

    @exception_app.get("/tempest")
    def tempest(_):
        raise TeaError

    _, response = exception_app.test_client.get("/tempest", debug=True)
    assert response.status == 418
    assert b"Tempest in a teapot" in response.body


def test_exception_in_ws_logged(caplog):
    app = Sanic("Test")

    @app.websocket("/feed")
    async def feed(request, ws):
        raise Exception("...")

    with caplog.at_level(logging.INFO):
        app.test_client.websocket("/feed")

    for record in caplog.record_tuples:
        if record[2].startswith("Exception occurred"):
            break

    assert record[0] == "sanic.error"
    assert record[1] == logging.ERROR
    assert "Exception occurred while handling uri:" in record[2]


@pytest.mark.parametrize("debug", (True, False))
def test_contextual_exception_context(debug):
    app = Sanic("Test")

    class TeapotError(SanicException):
        status_code = 418
        message = "Sorry, I cannot brew coffee"

    def fail():
        raise TeapotError(context={"foo": "bar"})

    app.post("/coffee/json", error_format="json")(lambda _: fail())
    app.post("/coffee/html", error_format="html")(lambda _: fail())
    app.post("/coffee/text", error_format="text")(lambda _: fail())

    _, response = app.test_client.post("/coffee/json", debug=debug)
    assert response.status == 418
    assert response.json["message"] == "Sorry, I cannot brew coffee"
    assert response.json["context"] == {"foo": "bar"}

    _, response = app.test_client.post("/coffee/html", debug=debug)
    soup = BeautifulSoup(response.body, "html.parser")
    dl = dl_to_dict(soup, "context")
    assert response.status == 418
    assert "Sorry, I cannot brew coffee" in soup.find("p").text
    assert dl == {"foo": "bar"}

    _, response = app.test_client.post("/coffee/text", debug=debug)
    lines = list(map(lambda x: x.decode(), response.body.split(b"\n")))
    idx = lines.index("Context") + 1
    assert response.status == 418
    assert lines[2] == "Sorry, I cannot brew coffee"
    assert lines[idx] == '    foo: "bar"'


@pytest.mark.parametrize("debug", (True, False))
def test_contextual_exception_extra(debug):
    app = Sanic("Test")

    class TeapotError(SanicException):
        status_code = 418

        @property
        def message(self):
            return f"Found {self.extra['foo']}"

    def fail():
        raise TeapotError(extra={"foo": "bar"})

    app.post("/coffee/json", error_format="json")(lambda _: fail())
    app.post("/coffee/html", error_format="html")(lambda _: fail())
    app.post("/coffee/text", error_format="text")(lambda _: fail())

    _, response = app.test_client.post("/coffee/json", debug=debug)
    assert response.status == 418
    assert response.json["message"] == "Found bar"
    if debug:
        assert response.json["extra"] == {"foo": "bar"}
    else:
        assert "extra" not in response.json

    _, response = app.test_client.post("/coffee/html", debug=debug)
    soup = BeautifulSoup(response.body, "html.parser")
    dl = dl_to_dict(soup, "extra")
    assert response.status == 418
    assert "Found bar" in soup.find("p").text
    if debug:
        assert dl == {"foo": "bar"}
    else:
        assert not dl

    _, response = app.test_client.post("/coffee/text", debug=debug)
    lines = list(map(lambda x: x.decode(), response.body.split(b"\n")))
    assert response.status == 418
    assert lines[2] == "Found bar"
    if debug:
        idx = lines.index("Extra") + 1
        assert lines[idx] == '    foo: "bar"'
    else:
        assert "Extra" not in lines


@pytest.mark.parametrize("override", (True, False))
def test_contextual_exception_functional_message(override):
    app = Sanic("Test")

    class TeapotError(SanicException):
        status_code = 418

        @property
        def message(self):
            return f"Received foo={self.context['foo']}"

    @app.post("/coffee", error_format="json")
    async def make_coffee(_):
        error_args = {"context": {"foo": "bar"}}
        if override:
            error_args["message"] = "override"
        raise TeapotError(**error_args)

    _, response = app.test_client.post("/coffee", debug=True)
    error_message = "override" if override else "Received foo=bar"
    assert response.status == 418
    assert response.json["message"] == error_message
    assert response.json["context"] == {"foo": "bar"}


def test_exception_aliases():
    assert InvalidUsage is BadRequest
    assert MethodNotSupported is MethodNotAllowed
    assert ContentRangeError is RangeNotSatisfiable
    assert HeaderExpectationFailed is ExpectationFailed
