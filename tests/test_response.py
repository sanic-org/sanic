import asyncio
import inspect
import os
from aiofiles import os as async_os
from mimetypes import guess_type
from urllib.parse import unquote

import pytest
from random import choice

from sanic import Sanic
from sanic.response import HTTPResponse, stream, StreamingHTTPResponse, file, file_stream, json
from sanic.testing import HOST
from unittest.mock import MagicMock

JSON_DATA = {'ok': True}



def test_response_body_not_a_string():
    """Test when a response body sent from the application is not a string"""
    app = Sanic('response_body_not_a_string')
    random_num = choice(range(1000))

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse(body=random_num)

    request, response = app.test_client.get('/hello')
    assert response.text == str(random_num)


async def sample_streaming_fn(response):
    response.write('foo,')
    await asyncio.sleep(.001)
    response.write('bar')

def test_method_not_allowed():
    app = Sanic('method_not_allowed')

    @app.get('/')
    async def test(request):
        return response.json({'hello': 'world'})

    request, response = app.test_client.head('/')
    assert response.headers['Allow'] == 'GET'

    @app.post('/')
    async def test(request):
        return response.json({'hello': 'world'})

    request, response = app.test_client.head('/')
    assert response.status == 405
    assert set(response.headers['Allow'].split(', ')) == set(['GET', 'POST'])
    assert response.headers['Content-Length'] == '0'


@pytest.fixture
def json_app():
    app = Sanic('json')

    @app.route("/")
    async def test(request):
        return json(JSON_DATA)

    @app.delete("/")
    async def test_delete(request):
        return json(None, status=204)

    return app


def test_json_response(json_app):
    from sanic.response import json_dumps
    request, response = json_app.test_client.get('/')
    assert response.status == 200
    assert response.text == json_dumps(JSON_DATA)
    assert response.json == JSON_DATA


def test_no_content(json_app):
    request, response = json_app.test_client.delete('/')
    assert response.status == 204
    assert response.text == ''
    assert response.headers['Content-Length'] == '0'


@pytest.fixture
def streaming_app():
    app = Sanic('streaming')

    @app.route("/")
    async def test(request):
        return stream(sample_streaming_fn, content_type='text/csv')

    return app


def test_streaming_adds_correct_headers(streaming_app):
    request, response = streaming_app.test_client.get('/')
    assert response.headers['Transfer-Encoding'] == 'chunked'
    assert response.headers['Content-Type'] == 'text/csv'


def test_streaming_returns_correct_content(streaming_app):
    request, response = streaming_app.test_client.get('/')
    assert response.text == 'foo,bar'


@pytest.mark.parametrize('status', [200, 201, 400, 401])
def test_stream_response_status_returns_correct_headers(status):
    response = StreamingHTTPResponse(sample_streaming_fn, status=status)
    headers = response.get_headers()
    assert b"HTTP/1.1 %s" % str(status).encode() in headers


@pytest.mark.parametrize('keep_alive_timeout', [10, 20, 30])
def test_stream_response_keep_alive_returns_correct_headers(
        keep_alive_timeout):
    response = StreamingHTTPResponse(sample_streaming_fn)
    headers = response.get_headers(
        keep_alive=True, keep_alive_timeout=keep_alive_timeout)

    assert b"Keep-Alive: %s\r\n" % str(keep_alive_timeout).encode() in headers


def test_stream_response_includes_chunked_header():
    response = StreamingHTTPResponse(sample_streaming_fn)
    headers = response.get_headers()
    assert b"Transfer-Encoding: chunked\r\n" in headers


def test_stream_response_writes_correct_content_to_transport(streaming_app):
    response = StreamingHTTPResponse(sample_streaming_fn)
    response.transport = MagicMock(asyncio.Transport)

    @streaming_app.listener('after_server_start')
    async def run_stream(app, loop):
        await response.stream()
        assert response.transport.write.call_args_list[1][0][0] == (
            b'4\r\nfoo,\r\n'
        )

        assert response.transport.write.call_args_list[2][0][0] == (
            b'3\r\nbar\r\n'
        )

        assert response.transport.write.call_args_list[3][0][0] == (
            b'0\r\n\r\n'
        )

        app.stop()

    streaming_app.run(host=HOST, port=streaming_app.test_port)


@pytest.fixture
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, 'static')
    return static_directory


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(os.path.join(static_file_directory, file_name), 'rb') as file:
        return file.read()

@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt', 'python.png'])
def test_file_response(file_name, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET'])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file(file_path, mime_type=guess_type(file_path)[0] or 'text/plain')

    request, response = app.test_client.get('/files/{}'.format(file_name))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert 'Content-Disposition' not in response.headers

@pytest.mark.parametrize('source,dest', [
    ('test.file', 'my_file.txt'), ('decode me.txt', 'readme.md'), ('python.png', 'logo.png')])
def test_file_response_custom_filename(source, dest, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET'])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file(file_path, filename=dest)

    request, response = app.test_client.get('/files/{}'.format(source))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, source)
    assert response.headers['Content-Disposition'] == 'attachment; filename="{}"'.format(dest)

@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_file_head_response(file_name, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET', 'HEAD'])
    async def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        stats = await async_os.stat(file_path)
        headers = dict()
        headers['Accept-Ranges'] = 'bytes'
        headers['Content-Length'] = str(stats.st_size)
        if request.method == "HEAD":
            return HTTPResponse(
                headers=headers,
                content_type=guess_type(file_path)[0] or 'text/plain')
        else:
            return file(file_path, headers=headers,
                        mime_type=guess_type(file_path)[0] or 'text/plain')

    request, response = app.test_client.head('/files/{}'.format(file_name))
    assert response.status == 200
    assert 'Accept-Ranges' in response.headers
    assert 'Content-Length' in response.headers
    assert int(response.headers[
               'Content-Length']) == len(
                   get_file_content(static_file_directory, file_name))

@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt', 'python.png'])
def test_file_stream_response(file_name, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET'])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file_stream(file_path, chunk_size=32,
                          mime_type=guess_type(file_path)[0] or 'text/plain')

    request, response = app.test_client.get('/files/{}'.format(file_name))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert 'Content-Disposition' not in response.headers

@pytest.mark.parametrize('source,dest', [
    ('test.file', 'my_file.txt'), ('decode me.txt', 'readme.md'), ('python.png', 'logo.png')])
def test_file_stream_response_custom_filename(source, dest, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET'])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file_stream(file_path, chunk_size=32, filename=dest)

    request, response = app.test_client.get('/files/{}'.format(source))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, source)
    assert response.headers['Content-Disposition'] == 'attachment; filename="{}"'.format(dest)

@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_file_stream_head_response(file_name, static_file_directory):
    app = Sanic('test_file_helper')
    @app.route('/files/<filename>', methods=['GET', 'HEAD'])
    async def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        headers = dict()
        headers['Accept-Ranges'] = 'bytes'
        if request.method == "HEAD":
            # Return a normal HTTPResponse, not a
            # StreamingHTTPResponse for a HEAD request
            stats = await async_os.stat(file_path)
            headers['Content-Length'] = str(stats.st_size)
            return HTTPResponse(
                headers=headers,
                content_type=guess_type(file_path)[0] or 'text/plain')
        else:
            return file_stream(file_path, chunk_size=32, headers=headers,
                        mime_type=guess_type(file_path)[0] or 'text/plain')

    request, response = app.test_client.head('/files/{}'.format(file_name))
    assert response.status == 200
    # A HEAD request should never be streamed/chunked.
    if 'Transfer-Encoding' in response.headers:
        assert response.headers['Transfer-Encoding'] != "chunked"
    assert 'Accept-Ranges' in response.headers
    # A HEAD request should get the Content-Length too
    assert 'Content-Length' in response.headers
    assert int(response.headers[
               'Content-Length']) == len(
                   get_file_content(static_file_directory, file_name))
