from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test
from sanic.exceptions import ServerError


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
