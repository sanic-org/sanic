import pytest

from sanic import Sanic
from sanic.response import text, redirect


@pytest.fixture
def redirect_app():
    app = Sanic('test_redirection')

    @app.route('/redirect_init')
    async def redirect_init(request):
        return redirect("/redirect_target")

    @app.route('/redirect_init_with_301')
    async def redirect_init_with_301(request):
        return redirect("/redirect_target", status=301)

    @app.route('/redirect_target')
    async def redirect_target(request):
        return text('OK')

    @app.route('/1')
    def handler(request):
        return redirect('/2')

    @app.route('/2')
    def handler(request):
        return redirect('/3')

    @app.route('/3')
    def handler(request):
        return text('OK')

    return app


def test_redirect_default_302(redirect_app):
    """
    We expect a 302 default status code and the headers to be set.
    """
    request, response = redirect_app.test_client.get(
        '/redirect_init',
        allow_redirects=False)

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"
    assert response.headers["Content-Type"] == 'text/html; charset=utf-8'


def test_redirect_headers_none(redirect_app):
    request, response = redirect_app.test_client.get(
        uri="/redirect_init",
        headers=None,
        allow_redirects=False)

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"


def test_redirect_with_301(redirect_app):
    """
    Test redirection with a different status code.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_init_with_301",
        allow_redirects=False)

    assert response.status == 301
    assert response.headers["Location"] == "/redirect_target"


def test_get_then_redirect_follow_redirect(redirect_app):
    """
    With `allow_redirects` we expect a 200.
    """
    request, response = redirect_app.test_client.get(
        "/redirect_init",
        allow_redirects=True)

    assert response.status == 200
    assert response.text == 'OK'


def test_chained_redirect(redirect_app):
    """Test test_client is working for redirection"""
    request, response = redirect_app.test_client.get('/1')
    assert request.url.endswith('/1')
    assert response.status == 200
    assert response.text == 'OK'
    assert response.url.endswith('/3')
