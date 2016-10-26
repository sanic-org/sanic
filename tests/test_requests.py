from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text, redirect
from sanic.utils import sanic_endpoint_test


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_sync():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        return text('Hello')

    _request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'


def test_text():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        return text('Hello')

    _request, response = sanic_endpoint_test(app)

    assert response.text == 'Hello'


def test_json():
    app = Sanic('test_json')

    @app.route('/')
    async def handler(request):
        return json({"test": True})

    _request, response = sanic_endpoint_test(app)

    try:
        results = json_loads(response.text)
    except:
        raise ValueError("Expected JSON response but got '{}'".format(response))

    assert results.get('test') == True


def test_query_string():
    app = Sanic('test_query_string')

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, _response = sanic_endpoint_test(app, params=[("test1", 1), ("test2", "false"), ("test2", "true")])

    assert request.args.get('test1') == '1'
    assert request.args.get('test2') == 'false'


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

    request, _response = sanic_endpoint_test(app, data=payload, headers=headers)

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

    request, _response = sanic_endpoint_test(app, data=payload, headers=headers)

    assert request.form.get('test') == 'OK'


def test_get_then_redirect():
    app = Sanic('test_get_then_redirect')

    @app.route('/path1')
    async def handler01(request):
        return redirect(request, "/path2")

    @app.route('/path2')
    async def handler02(request):
        return text('OK')

    _request, response = sanic_endpoint_test(app, method="get",
                                             uri="/path1",
                                             allow_redirects=False)

    assert response.status == 302
    assert response.headers["Location"] == "/path2"

