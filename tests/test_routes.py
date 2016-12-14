import pytest

from sanic import Sanic
from sanic.response import text
from sanic.router import RouteExists
from sanic.utils import sanic_endpoint_test


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #

def test_static_routes():
    app = Sanic('test_dynamic_route')

    @app.route('/test')
    async def handler1(request):
        return text('OK1')

    @app.route('/pizazz')
    async def handler2(request):
        return text('OK2')

    request, response = sanic_endpoint_test(app, uri='/test')
    assert response.text == 'OK1'

    request, response = sanic_endpoint_test(app, uri='/pizazz')
    assert response.text == 'OK2'


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

    request, response = sanic_endpoint_test(app, uri='/folder/favicon.ico')

    assert response.text == 'OK'
    assert results[1] == 'favicon.ico'


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
    app = Sanic('test_dynamic_route_number')

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
    app = Sanic('test_dynamic_route_regex')

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


def test_dynamic_route_unhashable():
    app = Sanic('test_dynamic_route_unhashable')

    @app.route('/folder/<unhashable:[A-Za-z0-9/]+>/end/')
    async def handler(request, unhashable):
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/folder/test/asdf/end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test///////end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test/end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test/nope/')
    assert response.status == 404


def test_route_duplicate():
    app = Sanic('test_route_duplicate')

    with pytest.raises(RouteExists):
        @app.route('/test')
        async def handler1(request):
            pass

        @app.route('/test')
        async def handler2(request):
            pass

    with pytest.raises(RouteExists):
        @app.route('/test/<dynamic>/')
        async def handler1(request, dynamic):
            pass

        @app.route('/test/<dynamic>/')
        async def handler2(request, dynamic):
            pass


def test_method_not_allowed():
    app = Sanic('test_method_not_allowed')

    @app.route('/test', methods=['GET'])
    async def handler(request):
        return text('OK')

    request, response = sanic_endpoint_test(app, uri='/test')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, method='post', uri='/test')
    assert response.status == 405


def test_static_add_route():
    app = Sanic('test_static_add_route')

    async def handler1(request):
        return text('OK1')

    async def handler2(request):
        return text('OK2')

    app.add_route(handler1, '/test')
    app.add_route(handler2, '/test2')

    request, response = sanic_endpoint_test(app, uri='/test')
    assert response.text == 'OK1'

    request, response = sanic_endpoint_test(app, uri='/test2')
    assert response.text == 'OK2'


def test_dynamic_add_route():
    app = Sanic('test_dynamic_add_route')

    results = []

    async def handler(request, name):
        results.append(name)
        return text('OK')

    app.add_route(handler, '/folder/<name>')
    request, response = sanic_endpoint_test(app, uri='/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_add_route_string():
    app = Sanic('test_dynamic_add_route_string')

    results = []

    async def handler(request, name):
        results.append(name)
        return text('OK')

    app.add_route(handler, '/folder/<name:string>')
    request, response = sanic_endpoint_test(app, uri='/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'

    request, response = sanic_endpoint_test(app, uri='/folder/favicon.ico')

    assert response.text == 'OK'
    assert results[1] == 'favicon.ico'


def test_dynamic_add_route_int():
    app = Sanic('test_dynamic_add_route_int')

    results = []

    async def handler(request, folder_id):
        results.append(folder_id)
        return text('OK')

    app.add_route(handler, '/folder/<folder_id:int>')

    request, response = sanic_endpoint_test(app, uri='/folder/12345')
    assert response.text == 'OK'
    assert type(results[0]) is int

    request, response = sanic_endpoint_test(app, uri='/folder/asdf')
    assert response.status == 404


def test_dynamic_add_route_number():
    app = Sanic('test_dynamic_add_route_number')

    results = []

    async def handler(request, weight):
        results.append(weight)
        return text('OK')

    app.add_route(handler, '/weight/<weight:number>')

    request, response = sanic_endpoint_test(app, uri='/weight/12345')
    assert response.text == 'OK'
    assert type(results[0]) is float

    request, response = sanic_endpoint_test(app, uri='/weight/1234.56')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/weight/1234-56')
    assert response.status == 404


def test_dynamic_add_route_regex():
    app = Sanic('test_dynamic_route_int')

    async def handler(request, folder_id):
        return text('OK')

    app.add_route(handler, '/folder/<folder_id:[A-Za-z0-9]{0,4}>')

    request, response = sanic_endpoint_test(app, uri='/folder/test')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test1')
    assert response.status == 404

    request, response = sanic_endpoint_test(app, uri='/folder/test-123')
    assert response.status == 404

    request, response = sanic_endpoint_test(app, uri='/folder/')
    assert response.status == 200


def test_dynamic_add_route_unhashable():
    app = Sanic('test_dynamic_add_route_unhashable')

    async def handler(request, unhashable):
        return text('OK')

    app.add_route(handler, '/folder/<unhashable:[A-Za-z0-9/]+>/end/')

    request, response = sanic_endpoint_test(app, uri='/folder/test/asdf/end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test///////end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test/end/')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, uri='/folder/test/nope/')
    assert response.status == 404


def test_add_route_duplicate():
    app = Sanic('test_add_route_duplicate')

    with pytest.raises(RouteExists):
        async def handler1(request):
            pass

        async def handler2(request):
            pass

        app.add_route(handler1, '/test')
        app.add_route(handler2, '/test')

    with pytest.raises(RouteExists):
        async def handler1(request, dynamic):
            pass

        async def handler2(request, dynamic):
            pass

        app.add_route(handler1, '/test/<dynamic>/')
        app.add_route(handler2, '/test/<dynamic>/')


def test_add_route_method_not_allowed():
    app = Sanic('test_add_route_method_not_allowed')

    async def handler(request):
        return text('OK')

    app.add_route(handler, '/test', methods=['GET'])

    request, response = sanic_endpoint_test(app, uri='/test')
    assert response.status == 200

    request, response = sanic_endpoint_test(app, method='post', uri='/test')
    assert response.status == 405
