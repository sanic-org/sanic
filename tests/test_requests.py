from json import loads as json_loads, dumps as json_dumps

import pytest

from sanic import Sanic
from sanic.exceptions import ServerError
from sanic.response import json, text, redirect


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_sync():
    app = Sanic('test_text')

    @app.route('/')
    def handler(request):
        return text('Hello')

    request, response = app.test_client.get('/')

    assert response.text == 'Hello'


def test_text():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        return text('Hello')

    request, response = app.test_client.get('/')

    assert response.text == 'Hello'


def test_headers():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        headers = {"spam": "great"}
        return text('Hello', headers=headers)

    request, response = app.test_client.get('/')

    assert response.headers.get('spam') == 'great'


def test_non_str_headers():
    app = Sanic('test_text')

    @app.route('/')
    async def handler(request):
        headers = {"answer": 42}
        return text('Hello', headers=headers)

    request, response = app.test_client.get('/')

    assert response.headers.get('answer') == '42'

def test_invalid_response():
    app = Sanic('test_invalid_response')

    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text('Internal Server Error.', 500)

    @app.route('/')
    async def handler(request):
        return 'This should fail'

    request, response = app.test_client.get('/')
    assert response.status == 500
    assert response.text == "Internal Server Error."


def test_json():
    app = Sanic('test_json')

    @app.route('/')
    async def handler(request):
        return json({"test": True})

    request, response = app.test_client.get('/')

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
    request, response = app.test_client.get('/', data=data)

    assert response.status == 400


def test_query_string():
    app = Sanic('test_query_string')

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = app.test_client.get(
        '/', params=[("test1", "1"), ("test2", "false"), ("test2", "true")])

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

    request, response = app.test_client.get('/', headers=headers)

    assert request.token == token

# ------------------------------------------------------------ #
#  POST
# ------------------------------------------------------------ #

def test_post_json():
    app = Sanic('test_post_json')

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    payload = {'test': 'OK'}
    headers = {'content-type': 'application/json'}

    request, response = app.test_client.post(
        '/', data=json_dumps(payload), headers=headers)

    assert request.json.get('test') == 'OK'
    assert response.text == 'OK'


def test_post_form_urlencoded():
    app = Sanic('test_post_form_urlencoded')

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    payload = 'test=OK'
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    request, response = app.test_client.post('/', data=payload, headers=headers)

    assert request.form.get('test') == 'OK'


def test_post_form_multipart_form_data():
    app = Sanic('test_post_form_multipart_form_data')

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    payload = '------sanic\r\n' \
              'Content-Disposition: form-data; name="test"\r\n' \
              '\r\n' \
              'OK\r\n' \
              '------sanic--\r\n'

    headers = {'content-type': 'multipart/form-data; boundary=----sanic'}

    request, response = app.test_client.post(data=payload, headers=headers)

    assert request.form.get('test') == 'OK'
