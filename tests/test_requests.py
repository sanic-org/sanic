from json import loads as json_loads, dumps as json_dumps
from urllib.parse import urlparse
import os
import ssl

import pytest

from sanic.exceptions import ServerError
from sanic.response import json, text
from sanic.request import DEFAULT_HTTP_CONTENT_TYPE
from sanic.testing import HOST, PORT


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_sync(app):

    @app.route('/')
    def handler(request):
        return text('Hello')

    request, response = app.test_client.get('/')

    assert response.text == 'Hello'


def test_remote_address(app):

    @app.route('/')
    def handler(request):
        return text("{}".format(request.ip))

    request, response = app.test_client.get('/')

    assert response.text == '127.0.0.1'


def test_text(app):

    @app.route('/')
    async def handler(request):
        return text('Hello')

    request, response = app.test_client.get('/')

    assert response.text == 'Hello'


def test_headers(app):

    @app.route('/')
    async def handler(request):
        headers = {"spam": "great"}
        return text('Hello', headers=headers)

    request, response = app.test_client.get('/')

    assert response.headers.get('spam') == 'great'


def test_non_str_headers(app):

    @app.route('/')
    async def handler(request):
        headers = {"answer": 42}
        return text('Hello', headers=headers)

    request, response = app.test_client.get('/')

    assert response.headers.get('answer') == '42'


def test_invalid_response(app):

    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text('Internal Server Error.', 500)

    @app.route('/')
    async def handler(request):
        return 'This should fail'

    request, response = app.test_client.get('/')
    assert response.status == 500
    assert response.text == "Internal Server Error."


def test_json(app):

    @app.route('/')
    async def handler(request):
        return json({"test": True})

    request, response = app.test_client.get('/')

    results = json_loads(response.text)

    assert results.get('test') is True


def test_empty_json(app):

    @app.route('/')
    async def handler(request):
        assert request.json is None
        return json(request.json)

    request, response = app.test_client.get('/')
    assert response.status == 200
    assert response.text == 'null'


def test_invalid_json(app):

    @app.route('/')
    async def handler(request):
        return json(request.json)

    data = "I am not json"
    request, response = app.test_client.get('/', data=data)

    assert response.status == 400


def test_query_string(app):

    @app.route('/')
    async def handler(request):
        return text('OK')

    request, response = app.test_client.get(
        '/', params=[("test1", "1"), ("test2", "false"), ("test2", "true")])

    assert request.args.get('test1') == '1'
    assert request.args.get('test2') == 'false'


def test_uri_template(app):

    @app.route('/foo/<id:int>/bar/<name:[A-z]+>')
    async def handler(request):
        return text('OK')

    request, response = app.test_client.get('/foo/123/bar/baz')
    assert request.uri_template == '/foo/<id:int>/bar/<name:[A-z]+>'


def test_token(app):

    @app.route('/')
    async def handler(request):
        return text('OK')

    # uuid4 generated token.
    token = 'a1d895e0-553a-421a-8e22-5ff8ecb48cbf'
    headers = {
        'content-type': 'application/json',
        'Authorization': '{}'.format(token)
    }

    request, response = app.test_client.get('/', headers=headers)

    assert request.token == token

    token = 'a1d895e0-553a-421a-8e22-5ff8ecb48cbf'
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Token {}'.format(token)
    }

    request, response = app.test_client.get('/', headers=headers)

    assert request.token == token

    token = 'a1d895e0-553a-421a-8e22-5ff8ecb48cbf'
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }

    request, response = app.test_client.get('/', headers=headers)

    assert request.token == token

    # no Authorization headers
    headers = {
        'content-type': 'application/json'
    }

    request, response = app.test_client.get('/', headers=headers)

    assert request.token is None


def test_content_type(app):

    @app.route('/')
    async def handler(request):
        return text(request.content_type)

    request, response = app.test_client.get('/')
    assert request.content_type == DEFAULT_HTTP_CONTENT_TYPE
    assert response.text == DEFAULT_HTTP_CONTENT_TYPE

    headers = {
        'content-type': 'application/json',
    }
    request, response = app.test_client.get('/', headers=headers)
    assert request.content_type == 'application/json'
    assert response.text == 'application/json'


def test_remote_addr(app):

    @app.route('/')
    async def handler(request):
        return text(request.remote_addr)

    headers = {
        'X-Forwarded-For': '127.0.0.1, 127.0.1.2'
    }
    request, response = app.test_client.get('/', headers=headers)
    assert request.remote_addr == '127.0.0.1'
    assert response.text == '127.0.0.1'

    request, response = app.test_client.get('/')
    assert request.remote_addr == ''
    assert response.text == ''

    headers = {
        'X-Forwarded-For': '127.0.0.1, ,   ,,127.0.1.2'
    }
    request, response = app.test_client.get('/', headers=headers)
    assert request.remote_addr == '127.0.0.1'
    assert response.text == '127.0.0.1'


def test_match_info(app):

    @app.route('/api/v1/user/<user_id>/')
    async def handler(request, user_id):
        return json(request.match_info)

    request, response = app.test_client.get('/api/v1/user/sanic_user/')

    assert request.match_info == {"user_id": "sanic_user"}
    assert json_loads(response.text) == {"user_id": "sanic_user"}


# ------------------------------------------------------------ #
#  POST
# ------------------------------------------------------------ #

def test_post_json(app):

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    payload = {'test': 'OK'}
    headers = {'content-type': 'application/json'}

    request, response = app.test_client.post(
        '/', data=json_dumps(payload), headers=headers)

    assert request.json.get('test') == 'OK'
    assert response.text == 'OK'


def test_post_form_urlencoded(app):

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    payload = 'test=OK'
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    request, response = app.test_client.post('/', data=payload,
                                             headers=headers)

    assert request.form.get('test') == 'OK'


@pytest.mark.parametrize(
    'payload', [
        '------sanic\r\n'
        'Content-Disposition: form-data; name="test"\r\n'
        '\r\n'
        'OK\r\n'
        '------sanic--\r\n',
        '------sanic\r\n'
        'content-disposition: form-data; name="test"\r\n'
        '\r\n'
        'OK\r\n'
        '------sanic--\r\n',
    ])
def test_post_form_multipart_form_data(app, payload):

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text('OK')

    headers = {'content-type': 'multipart/form-data; boundary=----sanic'}

    request, response = app.test_client.post(data=payload, headers=headers)

    assert request.form.get('test') == 'OK'


@pytest.mark.parametrize(
    'path,query,expected_url', [
        ('/foo', '', 'http://{}:{}/foo'),
        ('/bar/baz', '', 'http://{}:{}/bar/baz'),
        ('/moo/boo', 'arg1=val1', 'http://{}:{}/moo/boo?arg1=val1')
    ])
def test_url_attributes_no_ssl(app, path, query, expected_url):

    async def handler(request):
        return text('OK')

    app.add_route(handler, path)

    request, response = app.test_client.get(path + '?{}'.format(query))
    assert request.url == expected_url.format(HOST, PORT)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    'path,query,expected_url', [
        ('/foo', '', 'https://{}:{}/foo'),
        ('/bar/baz', '', 'https://{}:{}/bar/baz'),
        ('/moo/boo', 'arg1=val1', 'https://{}:{}/moo/boo?arg1=val1')
    ])
def test_url_attributes_with_ssl(app, path, query, expected_url):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(
        os.path.join(current_dir, 'certs/selfsigned.cert'),
        keyfile=os.path.join(current_dir, 'certs/selfsigned.key'))

    async def handler(request):
        return text('OK')

    app.add_route(handler, path)

    request, response = app.test_client.get(
        'https://{}:{}'.format(HOST, PORT) + path + '?{}'.format(query),
        server_kwargs={'ssl': context})
    assert request.url == expected_url.format(HOST, PORT)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


def test_form_with_multiple_values(app):

    @app.route('/', methods=['POST'])
    async def handler(request):
        return text("OK")

    payload="selectedItems=v1&selectedItems=v2&selectedItems=v3"

    headers = {'content-type': 'application/x-www-form-urlencoded'}

    request, response = app.test_client.post('/', data=payload,
                                             headers=headers)

    assert request.form.getlist("selectedItems") == ["v1", "v2", "v3"]


def test_request_string_representation(app):
    @app.route('/', methods=["GET"])
    async def get(request):
        return text("OK")

    request, _ = app.test_client.get("/")
    assert repr(request) == '<Request: GET />'


@pytest.mark.parametrize(
    'payload', [
        '------sanic\r\n'
        'Content-Disposition: form-data; filename="filename"; name="test"\r\n'
        '\r\n'
        'OK\r\n'
        '------sanic--\r\n',
        '------sanic\r\n'
        'content-disposition: form-data; filename="filename"; name="test"\r\n'
        '\r\n'
        'content-type: application/json; {"field": "value"}\r\n'
        '------sanic--\r\n',
    ])
def test_request_multipart_files(app, payload):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    headers = {'content-type': 'multipart/form-data; boundary=----sanic'}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get('test').name == "filename"


def test_request_multipart_file_with_json_content_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"' \
              '\r\nContent-Type: application/json\r\n\r\n\r\n------sanic--'

    headers = {'content-type': 'multipart/form-data; boundary=------sanic'}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get('file').type == 'application/json'


def test_request_multipart_with_multiple_files_and_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"' \
              '\r\nContent-Type: application/json\r\n\r\n\r\n' \
              '------sanic\r\nContent-Disposition: form-data; name="file"; filename="some_file.pdf"\r\n' \
              'Content-Type: application/pdf\r\n\r\n\r\n------sanic--'
    headers = {'content-type': 'multipart/form-data; boundary=------sanic'}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert len(request.files.getlist('file')) == 2
    assert request.files.getlist('file')[0].type == 'application/json'
    assert request.files.getlist('file')[1].type == 'application/pdf'
