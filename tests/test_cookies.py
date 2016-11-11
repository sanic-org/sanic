from datetime import datetime, timedelta
from http.cookies import SimpleCookie

from sanic import Sanic
from sanic.response import text
from sanic.utils import sanic_endpoint_test


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

    request, response = sanic_endpoint_test(app, cookies={"test": "working!"})
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get('Set-Cookie', {}))

    assert response.text == 'Cookies are: working!'
    assert response_cookies['right_back'].value == 'at you'


def test_cookie_options():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        response = text("OK")
        response.cookies['test'] = 'at you'
        response.cookies['test']['httponly'] = True
        response.cookies['test']['expires'] = datetime.now() + timedelta(seconds=10)
        return response

    request, response = sanic_endpoint_test(app)
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get('Set-Cookie', {}))

    assert response_cookies['test'].value == 'at you'
    assert response_cookies['test']['httponly'] == True
