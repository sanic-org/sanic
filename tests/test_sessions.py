# -*- encoding: utf-8 -*-
from sanic.sessions import SecureCookieSessionInterface
from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import text
from sanic.request import Request
from http.cookies import SimpleCookie


def test_sessions():
    app = Sanic("test_sessions")

    class DummyView(HTTPMethodView):
        async def get(self, request):
            """method to check session value"""
            value = request.session.get('value')
            if value is None:
                return text("No Value")
            else:
                return text("Value is: {}".format(value))

        async def post(self, request: Request):
            """method to set session value"""
            value = request.args.get('value')
            if value is None:
                return text("no args value")
            else:
                request.session['value'] = value
                return text("set value to {}".format(value))

        async def delete(self, request: Request):
            """method to delete session value"""
            del request.session['value']
            return text('deleled value.')

    app.add_route(DummyView.as_view(), '/')
    client = app.test_client
    _, response = client.get('/')
    assert response.text == "No Value"
    _, response = client.post('/?value=123')
    # TODO: TestClient not support cookie, need fix.
    header = response.headers.get('Set-Cookie')
    response_cookies = SimpleCookie()
    response_cookies.load(header)
    assert response.text == "set value to 123"
    assert 'session' in response_cookies

    _, response = client.get(cookies=response_cookies)
    assert response.text == "Value is: 123"
