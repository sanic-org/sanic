import inspect
import os

from sanic import Sanic
from sanic.utils import sanic_endpoint_test

def test_static_file():
    current_file = inspect.getfile(inspect.currentframe())
    with open(current_file, 'rb') as file:
        current_file_contents = file.read()

    app = Sanic('test_static')
    app.static(current_file, '/testing.file')

    request, response = sanic_endpoint_test(app, uri='/testing.file')
    assert response.status == 200
    assert response.body == current_file_contents

def test_static_directory():
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    with open(current_file, 'rb') as file:
        current_file_contents = file.read()

    app = Sanic('test_static')
    app.static(current_directory, '/dir')

    request, response = sanic_endpoint_test(app, uri='/dir/test_static.py')
    assert response.status == 200
    assert response.body == current_file_contents