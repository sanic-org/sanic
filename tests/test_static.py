import inspect
import os

import pytest

from sanic import Sanic
from sanic.utils import sanic_endpoint_test


@pytest.fixture(scope='module')
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, 'static')
    return static_directory


@pytest.fixture(scope='module')
def static_file_path(static_file_directory):
    """The path to the static file that we want to serve"""
    return os.path.join(static_file_directory, 'test.file')


@pytest.fixture(scope='module')
def static_file_content(static_file_path):
    """The content of the static file to check"""
    with open(static_file_path, 'rb') as file:
        return file.read()


def test_static_file(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path)

    request, response = sanic_endpoint_test(app, uri='/testing.file')
    assert response.status == 200
    assert response.body == static_file_content


def test_static_directory(
        static_file_directory, static_file_path, static_file_content):

    app = Sanic('test_static')
    app.static('/dir', static_file_directory)

    request, response = sanic_endpoint_test(app, uri='/dir/test.file')
    assert response.status == 200
    assert response.body == static_file_content


def test_static_url_decode_file(static_file_directory):
    decode_me_path = os.path.join(static_file_directory, 'decode me.txt')
    with open(decode_me_path, 'rb') as file:
        decode_me_contents = file.read()

    app = Sanic('test_static')
    app.static('/dir', static_file_directory)

    request, response = sanic_endpoint_test(app, uri='/dir/decode me.txt')
    assert response.status == 200
    assert response.body == decode_me_contents


def test_static_head_request(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    request, response = sanic_endpoint_test(
        app, uri='/testing.file', method='head')
    assert response.status == 200
    assert 'Accept-Ranges' in response.headers
    assert 'Content-Length' in response.headers
    assert int(response.headers['Content-Length']) == len(static_file_content)


def test_static_content_range_correct(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    headers = {
        'Range': 'bytes=12-19'
    }
    request, response = sanic_endpoint_test(
        app, uri='/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(static_file_content)[12:19]
    assert int(response.headers['Content-Length']) == len(static_content)
    assert response.body == static_content


def test_static_content_range_front(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    headers = {
        'Range': 'bytes=12-'
    }
    request, response = sanic_endpoint_test(
        app, uri='/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(static_file_content)[12:]
    assert int(response.headers['Content-Length']) == len(static_content)
    assert response.body == static_content


def test_static_content_range_back(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    headers = {
        'Range': 'bytes=-12'
    }
    request, response = sanic_endpoint_test(
        app, uri='/testing.file', headers=headers)
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    static_content = bytes(static_file_content)[-12:]
    assert int(response.headers['Content-Length']) == len(static_content)
    assert response.body == static_content


def test_static_content_range_empty(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    request, response = sanic_endpoint_test(app, uri='/testing.file')
    assert response.status == 200
    assert 'Content-Length' in response.headers
    assert 'Content-Range' not in response.headers
    assert int(response.headers['Content-Length']) == len(static_file_content)
    assert response.body == bytes(static_file_content)


def test_static_content_range_error(static_file_path, static_file_content):
    app = Sanic('test_static')
    app.static('/testing.file', static_file_path, use_content_range=True)

    headers = {
        'Range': 'bytes=1-0'
    }
    request, response = sanic_endpoint_test(
        app, uri='/testing.file', headers=headers)
    assert response.status == 416
    assert 'Content-Length' in response.headers
    assert 'Content-Range' in response.headers
    assert response.headers['Content-Range'] == "bytes */%s" % (
        len(static_file_content),)
