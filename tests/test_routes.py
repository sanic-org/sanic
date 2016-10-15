from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text
from sanic.utils import sanic_endpoint_test


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #

def test_dynamic_route():
    app = Sanic('test_dynamic_route')

    results = []

    @app.route('/folder/<name>')
    async def handler(request, name):
        results.append(name)
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_route_string():
    app = Sanic('test_dynamic_route_string')

    results = []

    @app.route('/folder/<name:string>')
    async def handler(request, name):
        results.append(name)
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_route_int():
    app = Sanic('test_dynamic_route_int')

    results = []

    @app.route('/folder/<folder_id:int>')
    async def handler(request, folder_id):
        results.append(folder_id)
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/folder/12345')
    assert response.text == 'OK'
    assert type(results[0]) is int

    request, response = sanic_endpoint_test(app, uri='/folder/asdf')
    assert response.status == 404


def test_dynamic_route_number():
    app = Sanic('test_dynamic_route_int')

    results = []

    @app.route('/weight/<weight:number>')
    async def handler(request, weight):
        results.append(weight)
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/weight/12345')
    assert response.text == 'OK'
    assert type(results[0]) is float

    request, response = sanic_endpoint_test(app, uri='/weight/1234.56')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/weight/1234-56')
    assert response.status == 404


def test_dynamic_route_regex():
    app = Sanic('test_dynamic_route_int')

    @app.route('/folder/<folder_id:[A-Za-z0-9]{0,4}>')
    async def handler(request, folder_id):
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/folder/test')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test1')
    assert response.status == 404

    request, response = sanic_endpoint_test(app, uri='/folder/test-123')
    assert response.status == 404

    request, response = sanic_endpoint_test(app, uri='/folder/')
    assert response.status == 200
