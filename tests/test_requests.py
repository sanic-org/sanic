from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text, redirect
from sanic.utils import sanic_endpoint_test
from sanic.exceptions import ServerError

import pytest

# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_sync():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        return text('Hello')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'


def test_text():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        return text('Hello')

    request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'


def test_headers():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        headers = {"spam": "great"}
        return text('Hello', headers=headers)

    request, response = sanic_endpoint_test(app)

    assert response.headers.get('spam') == 'great'


def test_non_str_headers():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        headers = {"answer": 42}
        return text('Hello', headers=headers)

    request, response = sanic_endpoint_test(app)

    assert response.headers.get('answer') == '42'
    
def test_invalid_response():
    app = Sanic('test_invalid_response')

    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text('Internal Server Error.', 500)

    @app.route('/')
    async def handler(request):
        return 'This should fail'

    request, response = sanic_endpoint_test(app)
    assert response.status == 500
    assert response.text == "Internal Server Error."
    
    
def test_json():
    app = Sanic('test_json')

    @app.route('/')
    async def handler(request):
        return json({"test": True})

    request, response = sanic_endpoint_test(app)

    try:
        results = json_loads(response.text)
    except:
        raise ValueError("Expected JSON response but got '{}'".format(response))

    assert results.get('test') == True


def test_invalid_json():
    app = Sanic('test_json')

    @app.route('/')
    async def handler(request):
        return json(request.json())

    data = "I am not json"
    request, response = sanic_endpoint_test(app, data=data)

    assert response.status == 400


def test_query_string():
    app = Sanic('test_query_string')

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = sanic_endpoint_test(app, params=[("test1", "1"), ("test2", "false"), ("test2", "true")])

    assert request.args.get('test1') == '1'
    assert request.args.get('test2') == 'false'


def test_token():
    app = Sanic('test_post_token')

    @app.route('/')
    async def handler(request):
        return text('OK')

    # uuid4 generated token.
    token = 'a1d895e0-553a-421a-8e22-5ff8ecb48cbf'
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Token {}'.format(token)
    }

    request, response = sanic_endpoint_test(app, headers=headers)

    assert request.token == token

# ------------------------------------------------------------ #
#  POST
# ------------------------------------------------------------ #

def test_post_json():
    app = Sanic('test_post_json')

    @app.route('/')
    async def handler(request):
        return text('OK')

    payload = {'test': 'OK'}
    headers = {'content-type': 'application/json'}

    request, response = sanic_endpoint_test(app, data=json_dumps(payload), headers=headers)

    assert request.json.get('test') == 'OK'
    assert response.text == 'OK'


def test_post_form_urlencoded():
    app = Sanic('test_post_form_urlencoded')

    @app.route('/')
    async def handler(request):
        return text('OK')

    payload = 'test=OK'
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    request, response = sanic_endpoint_test(app, data=payload, headers=headers)

    assert request.form.get('test') == 'OK'


def test_post_form_multipart_form_data():
    app = Sanic('test_post_form_multipart_form_data')

    @app.route('/')
    async def handler(request):
        return text('OK')

    payload = '------sanic\r\n' \
              'Content-Disposition: form-data; name="test"\r\n' \
              '\r\n' \
              'OK\r\n' \
              '------sanic--\r\n'

    headers = {'content-type': 'multipart/form-data; boundary=----sanic'}

    request, response = sanic_endpoint_test(app, data=payload, headers=headers)

    assert request.form.get('test') == 'OK'


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

    return app


def test_redirect_default_302(redirect_app):
    """
    We expect a 302 default status code and the headers to be set.
    """
    request, response = sanic_endpoint_test(
        redirect_app, method="get",
        uri="/redirect_init",
        allow_redirects=False)

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"
    assert response.headers["Content-Type"] == 'text/html; charset=utf-8'


def test_redirect_headers_none(redirect_app):
    request, response = sanic_endpoint_test(
        redirect_app, method="get",
        uri="/redirect_init",
        headers=None,
        allow_redirects=False)

    assert response.status == 302
    assert response.headers["Location"] == "/redirect_target"


def test_redirect_with_301(redirect_app):
    """
    Test redirection with a different status code.
    """
    request, response = sanic_endpoint_test(
        redirect_app, method="get",
        uri="/redirect_init_with_301",
        allow_redirects=False)

    assert response.status == 301
    assert response.headers["Location"] == "/redirect_target"


def test_get_then_redirect_follow_redirect(redirect_app):
    """
    With `allow_redirects` we expect a 200.
    """
    response = sanic_endpoint_test(
        redirect_app, method="get",
        uri="/redirect_init", gather_request=False,
        allow_redirects=True)

    assert response.status == 200
    assert response.text == 'OK'
