import pytest

from sanic import Sanic
from sanic.errorpages import HTMLRenderer, exception_response
from sanic.exceptions import NotFound, SanicException
from sanic.request import Request
from sanic.response import HTTPResponse, html, json, text


@pytest.fixture
def app():
    app = Sanic("error_page_testing")

    @app.route("/error", methods=["GET", "POST"])
    def err(request):
        raise Exception("something went wrong")

    return app


@pytest.fixture
def fake_request(app):
    return Request(b"/foobar", {}, "1.1", "GET", None, app)


@pytest.mark.parametrize(
    "fallback,content_type, exception, status",
    (
        (None, "text/html; charset=utf-8", Exception, 500),
        ("html", "text/html; charset=utf-8", Exception, 500),
        ("auto", "text/html; charset=utf-8", Exception, 500),
        ("text", "text/plain; charset=utf-8", Exception, 500),
        ("json", "application/json", Exception, 500),
        (None, "text/html; charset=utf-8", NotFound, 404),
        ("html", "text/html; charset=utf-8", NotFound, 404),
        ("auto", "text/html; charset=utf-8", NotFound, 404),
        ("text", "text/plain; charset=utf-8", NotFound, 404),
        ("json", "application/json", NotFound, 404),
    ),
)
def test_should_return_html_valid_setting(
    fake_request, fallback, content_type, exception, status
):
    if fallback:
        fake_request.app.config.FALLBACK_ERROR_FORMAT = fallback

    try:
        raise exception("bad stuff")
    except Exception as e:
        response = exception_response(
            fake_request,
            e,
            True,
            base=HTMLRenderer,
            fallback=fake_request.app.config.FALLBACK_ERROR_FORMAT,
        )

    assert isinstance(response, HTTPResponse)
    assert response.status == status
    assert response.content_type == content_type


def test_auto_fallback_with_data(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/html; charset=utf-8"

    _, response = app.test_client.post("/error", json={"foo": "bar"})
    assert response.status == 500
    assert response.content_type == "application/json"

    _, response = app.test_client.post("/error", data={"foo": "bar"})
    assert response.status == 500
    assert response.content_type == "text/html; charset=utf-8"


def test_auto_fallback_with_content_type(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get(
        "/error", headers={"content-type": "application/json"}
    )
    assert response.status == 500
    assert response.content_type == "application/json"

    _, response = app.test_client.get(
        "/error", headers={"content-type": "text/plain"}
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_route_error_format_set_on_auto(app):
    @app.get("/text")
    def text_response(request):
        return text(request.route.ctx.error_format)

    @app.get("/json")
    def json_response(request):
        return json({"format": request.route.ctx.error_format})

    @app.get("/html")
    def html_response(request):
        return html(request.route.ctx.error_format)

    _, response = app.test_client.get("/text")
    assert response.text == "text"

    _, response = app.test_client.get("/json")
    assert response.json["format"] == "json"

    _, response = app.test_client.get("/html")
    assert response.text == "html"


def test_route_error_response_from_auto_route(app):
    @app.get("/text")
    def text_response(request):
        raise Exception("oops")
        return text("Never gonna see this")

    @app.get("/json")
    def json_response(request):
        raise Exception("oops")
        return json({"message": "Never gonna see this"})

    @app.get("/html")
    def html_response(request):
        raise Exception("oops")
        return html("<h1>Never gonna see this</h1>")

    _, response = app.test_client.get("/text")
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.get("/json")
    assert response.content_type == "application/json"

    _, response = app.test_client.get("/html")
    assert response.content_type == "text/html; charset=utf-8"


def test_route_error_response_from_explicit_format(app):
    @app.get("/text", error_format="json")
    def text_response(request):
        raise Exception("oops")
        return text("Never gonna see this")

    @app.get("/json", error_format="text")
    def json_response(request):
        raise Exception("oops")
        return json({"message": "Never gonna see this"})

    _, response = app.test_client.get("/text")
    assert response.content_type == "application/json"

    _, response = app.test_client.get("/json")
    assert response.content_type == "text/plain; charset=utf-8"


def test_unknown_fallback_format(app):
    with pytest.raises(SanicException, match="Unknown format: bad"):
        app.config.FALLBACK_ERROR_FORMAT = "bad"


def test_route_error_format_unknown(app):
    with pytest.raises(SanicException, match="Unknown format: bad"):

        @app.get("/text", error_format="bad")
        def handler(request):
            ...
