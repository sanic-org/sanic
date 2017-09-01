from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from sanic import Sanic
from sanic.response import text
import pytest


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_cookies():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text('Cookies are: {}'.format(request.cookies['test']))
        response.cookies['right_back'] = 'at you'
        return response

    request, response = app.test_client.get('/', cookies={"test": "working!"})
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get('Set-Cookie', {}))

    assert response.text == 'Cookies are: working!'
    assert response_cookies['right_back'].value == 'at you'

@pytest.mark.parametrize("httponly,expected", [
        (False, False),
        (True, True),
])
def test_http_only_cookies(httponly, expected):
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text('Giving you cookies')
        response.cookies['right_back'] = 'at you'
        response.cookies['right_back']['httponly'] = httponly
        return response

    request, response = app.test_client.get('/')
    set_cookie_text = response.headers.get('Set-Cookie', '')

    assert ('HttpOnly' in set_cookie_text) == expected
    assert 'HttpOnly=' not in set_cookie_text

@pytest.mark.parametrize("secure,expected", [
        (False, False),
        (True, True),
])
def test_secure_cookies(secure, expected):
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text('Giving you cookies')
        response.cookies['right_back'] = 'at you'
        response.cookies['right_back']['secure'] = secure
        return response

    request, response = app.test_client.get('/')
    set_cookie_text = response.headers.get('Set-Cookie', '')

    assert ('Secure' in set_cookie_text) == expected
    assert 'Secure=' not in set_cookie_text

def test_http2_cookies():
    app = Sanic('test_http2_cookies')

    @app.route('/')
    async def handler(request):
        response = text('Cookies are: {}'.format(request.cookies['test']))
        return response

    headers = {'cookie': 'test=working!'}
    request, response = app.test_client.get('/', headers=headers)

    assert response.text == 'Cookies are: working!'

def test_cookie_options():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text("OK")
        response.cookies['test'] = 'at you'
        response.cookies['test']['httponly'] = True
        response.cookies['test']['expires'] = datetime.now() + timedelta(seconds=10)
        return response

    request, response = app.test_client.get('/')
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get('Set-Cookie', {}))

    assert response_cookies['test'].value == 'at you'
    assert response_cookies['test']['httponly'] == True

def test_cookie_deletion():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text("OK")
        del response.cookies['i_want_to_die']
        response.cookies['i_never_existed'] = 'testing'
        del response.cookies['i_never_existed']
        return response

    request, response = app.test_client.get('/')
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get('Set-Cookie', {}))

    assert int(response_cookies['i_want_to_die']['max-age']) == 0
    with pytest.raises(KeyError):
        response.cookies['i_never_existed']
