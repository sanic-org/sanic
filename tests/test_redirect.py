from urllib.parse import quote, unquote

import pytest

from sanic.response import redirect, text


@pytest.fixture
def redirect_app(app):
    @app.route("/redirect_init")
    async def redirect_init(request):
        return redirect("/redirect_target")

    @app.route("/redirect_init_with_301")
    async def redirect_init_with_301(request):
        return redirect("/redirect_target", status=301)

    @app.route("/redirect_target")
    async def redirect_target(request):
        return text("OK")

    @app.route("/1")
    def handler1(request):
        return redirect("/2")

    @app.route("/2")
    def handler2(request):
        return redirect("/3")

    @app.route("/3")
    def handler3(request):
        return text("OK")

    @app.route("/redirect_with_header_injection")
    async def redirect_with_header_injection(request):
        return redirect("/unsafe\ntest-header: test-value\n\ntest-body")

    return app


def test_redirect_default_302(redirect_app):
    """
    We expect a 302 default status code and the headers to be set.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_init", allow_redirects=False
    )

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_redirect_headers_none(redirect_app):
    request, response = redirect_app.test_client.get(
        uri="/redirect_init", headers=None, allow_redirects=False
    )

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"


def test_redirect_with_301(redirect_app):
    """
    Test redirection with a different status code.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_init_with_301", allow_redirects=False
    )

    assert response.status == 301
    assert response.headers["Location"] == "/redirect_target"


def test_get_then_redirect_follow_redirect(redirect_app):
    """
    With `allow_redirects` we expect a 200.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_init", allow_redirects=True
    )

    assert response.status == 200
    assert response.text == "OK"


def test_chained_redirect(redirect_app):
    """Test test_client is working for redirection"""
    request, response = redirect_app.test_client.get("/1")
    assert request.url.endswith("/1")
    assert response.status == 200
    assert response.text == "OK"
    try:
        assert response.url.endswith("/3")
    except AttributeError:
        assert response.url.path.endswith("/3")


def test_redirect_with_header_injection(redirect_app):
    """
    Test redirection to a URL with header and body injections.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_with_header_injection", allow_redirects=False
    )

    assert response.status == 302
    assert "test-header" not in response.headers
    assert not response.text.startswith("test-body")


@pytest.mark.parametrize(
    "test_str",
    [
        "sanic-test",
        "sanictest",
        "sanic test",
    ],
)
def test_redirect_with_params(app, test_str):
    use_in_uri = quote(test_str)

    @app.route("/api/v1/test/<test>/")
    async def init_handler(request, test):
        return redirect(f"/api/v2/test/{use_in_uri}/")

    @app.route("/api/v2/test/<test>/", unquote=True)
    async def target_handler(request, test):
        assert test == test_str
        return text("OK")

    _, response = app.test_client.get(f"/api/v1/test/{use_in_uri}/")
    assert response.status == 200

    assert response.body == b"OK"
