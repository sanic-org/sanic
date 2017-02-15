import inspect
import os

import pytest

from sanic import Sanic


@pytest.fixture(scope='module')
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, 'static')
    return static_directory


def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), 'rb') as file:
        return file.read()


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_file(static_file_directory, file_name):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name))

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
@pytest.mark.parametrize('base_uri', ['/static', '', '/dir'])
def test_static_directory(file_name, base_uri, static_file_directory):

    app = Sanic('test_static')
    app.static(base_uri, static_file_directory)

    request, response = app.test_client.get(
        uri='{}/{}'.format(base_uri, file_name))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_head_request(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    request, response = app.test_client.head('/testing.file')
    assert response.status == 200
    assert 'Accept-Ranges' in response.headers
    assert 'Content-Length' in response.headers
    assert int(response.headers[
               'Content-Length']) == len(
                   get_file_content(static_file_directory, file_name))


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_content_range_correct(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    headers = {
        'Range': 'bytes=12-19'
    }
    request, response = app.test_client.get('/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(get_file_content(
        static_file_directory, file_name))[12:19]
    assert int(response.headers[
               'Content-Length']) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_content_range_front(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    headers = {
        'Range': 'bytes=12-'
    }
    request, response = app.test_client.get('/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(get_file_content(
        static_file_directory, file_name))[12:]
    assert int(response.headers[
               'Content-Length']) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_content_range_back(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    headers = {
        'Range': 'bytes=-12'
    }
    request, response = app.test_client.get('/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(get_file_content(
        static_file_directory, file_name))[-12:]
    assert int(response.headers[
               'Content-Length']) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_content_range_empty(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' not in response.headers
    assert int(response.headers[
               'Content-Length']) == len(get_file_content(static_file_directory, file_name))
    assert response.body == bytes(
        get_file_content(static_file_directory, file_name))


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_content_range_error(file_name, static_file_directory):
    app = Sanic('test_static')
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name),
        use_content_range=True)

    headers = {
        'Range': 'bytes=1-0'
    }
    request, response = app.test_client.get('/testing.file', headers=headers)
    assert response.status == 416
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    assert response.headers['Content-Range'] == "bytes */%s" % (
        len(get_file_content(static_file_directory, file_name)),)
