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
