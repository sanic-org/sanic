import inspect
import os

import pytest


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


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt', 'python.png'])
def test_static_file(app, static_file_directory, file_name):
    app.static(
        '/testing.file', get_file_path(static_file_directory, file_name))

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize('file_name', ['test.html'])
def test_static_file_content_type(app, static_file_directory, file_name):
    app.static(
        '/testing.file',
        get_file_path(static_file_directory, file_name),
        content_type='text/html; charset=utf-8'
    )

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
@pytest.mark.parametrize('base_uri', ['/static', '', '/dir'])
def test_static_directory(app, file_name, base_uri, static_file_directory):
    app.static(base_uri, static_file_directory)

    request, response = app.test_client.get(
        uri='{}/{}'.format(base_uri, file_name))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
def test_static_head_request(app, file_name, static_file_directory):
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
def test_static_content_range_correct(app, file_name, static_file_directory):
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
def test_static_content_range_front(app, file_name, static_file_directory):
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
def test_static_content_range_back(app, file_name, static_file_directory):
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
def test_static_content_range_empty(app, file_name, static_file_directory):
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
def test_static_content_range_error(app, file_name, static_file_directory):
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


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt', 'python.png'])
def test_static_file_specified_host(app, static_file_directory, file_name):
    app.static(
        '/testing.file',
        get_file_path(static_file_directory, file_name),
        host="www.example.com"
    )

    headers = {"Host": "www.example.com"}
    request, response = app.test_client.get('/testing.file', headers=headers)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    request, response = app.test_client.get('/testing.file')
    assert response.status == 404
