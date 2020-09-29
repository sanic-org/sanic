import pytest

from sanic import Sanic
from sanic.errorpages import exception_response
from sanic.exceptions import NotFound
from sanic.request import Request
from sanic.response import HTTPResponse


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
        response = exception_response(fake_request, e, True)

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
