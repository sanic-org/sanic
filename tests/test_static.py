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

    request, response = sanic_endpoint_test(app, uri='/testing.file')
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize('file_name', ['test.file', 'decode me.txt'])
@pytest.mark.parametrize('base_uri', ['/static', '', '/dir'])
def test_static_directory(file_name, base_uri, static_file_directory):

    app = Sanic('test_static')
    app.static(base_uri, static_file_directory)

    request, response = sanic_endpoint_test(
        app, uri='{}/{}'.format(base_uri, file_name))
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
