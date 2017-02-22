import pytest

from sanic import Sanic
from sanic.response import text
from sanic.router import RouteExists, RouteDoesNotExist


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #

def test_shorthand_routes_get():
    app = Sanic('test_shorhand_routes_get')

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.post('/get')
    assert response.status == 405

def test_route_optional_slash():
    app = Sanic('test_route_optional_slash')

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'

def test_shorthand_routes_post():
    app = Sanic('test_shorhand_routes_post')

    @app.post('/post')
    def handler(request):
        return text('OK')

    request, response = app.test_client.post('/post')
    assert response.text == 'OK'

    request, response = app.test_client.get('/post')
    assert response.status == 405

def test_shorthand_routes_put():
    app = Sanic('test_shorhand_routes_put')

    @app.put('/put')
    def handler(request):
        return text('OK')

    request, response = app.test_client.put('/put')
    assert response.text == 'OK'

    request, response = app.test_client.get('/put')
    assert response.status == 405

def test_shorthand_routes_patch():
    app = Sanic('test_shorhand_routes_patch')

    @app.patch('/patch')
    def handler(request):
        return text('OK')

    request, response = app.test_client.patch('/patch')
    assert response.text == 'OK'

    request, response = app.test_client.get('/patch')
    assert response.status == 405

def test_shorthand_routes_head():
    app = Sanic('test_shorhand_routes_head')

    @app.head('/head')
    def handler(request):
        return text('OK')

    request, response = app.test_client.head('/head')
    assert response.status == 200

    request, response = app.test_client.get('/head')
    assert response.status == 405

def test_shorthand_routes_options():
    app = Sanic('test_shorhand_routes_options')

    @app.options('/options')
    def handler(request):
        return text('OK')

    request, response = app.test_client.options('/options')
    assert response.status == 200

    request, response = app.test_client.get('/options')
    assert response.status == 405

def test_static_routes():
    app = Sanic('test_dynamic_route')

    @app.route('/test')
    async def handler1(request):
        return text('OK1')

    @app.route('/pizazz')
    async def handler2(request):
        return text('OK2')

    request, response = app.test_client.get('/test')
    assert response.text == 'OK1'

    request, response = app.test_client.get('/pizazz')
    assert response.text == 'OK2'


def test_dynamic_route():
    app = Sanic('test_dynamic_route')

    results = []

    @app.route('/folder/<name>')
    async def handler(request, name):
        results.append(name)
        return text('OK')

    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_route_string():
    app = Sanic('test_dynamic_route_string')

    results = []

    @app.route('/folder/<name:string>')
    async def handler(request, name):
        results.append(name)
        return text('OK')

    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'

    request, response = app.test_client.get('/folder/favicon.ico')

    assert response.text == 'OK'
    assert results[1] == 'favicon.ico'


def test_dynamic_route_int():
    app = Sanic('test_dynamic_route_int')

    results = []

    @app.route('/folder/<folder_id:int>')
    async def handler(request, folder_id):
        results.append(folder_id)
        return text('OK')

    request, response = app.test_client.get('/folder/12345')
    assert response.text == 'OK'
    assert type(results[0]) is int

    request, response = app.test_client.get('/folder/asdf')
    assert response.status == 404


def test_dynamic_route_number():
    app = Sanic('test_dynamic_route_number')

    results = []

    @app.route('/weight/<weight:number>')
    async def handler(request, weight):
        results.append(weight)
        return text('OK')

    request, response = app.test_client.get('/weight/12345')
    assert response.text == 'OK'
    assert type(results[0]) is float

    request, response = app.test_client.get('/weight/1234.56')
    assert response.status == 200

    request, response = app.test_client.get('/weight/1234-56')
    assert response.status == 404


def test_dynamic_route_regex():
    app = Sanic('test_dynamic_route_regex')

    @app.route('/folder/<folder_id:[A-Za-z0-9]{0,4}>')
    async def handler(request, folder_id):
        return text('OK')

    request, response = app.test_client.get('/folder/test')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test1')
    assert response.status == 404

    request, response = app.test_client.get('/folder/test-123')
    assert response.status == 404

    request, response = app.test_client.get('/folder/')
    assert response.status == 200


def test_dynamic_route_unhashable():
    app = Sanic('test_dynamic_route_unhashable')

    @app.route('/folder/<unhashable:[A-Za-z0-9/]+>/end/')
    async def handler(request, unhashable):
        return text('OK')

    request, response = app.test_client.get('/folder/test/asdf/end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test///////end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test/end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test/nope/')
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

    request, response = app.test_client.get('/test')
    assert response.status == 200

    request, response = app.test_client.post('/test')
    assert response.status == 405


def test_static_add_route():
    app = Sanic('test_static_add_route')

    async def handler1(request):
        return text('OK1')

    async def handler2(request):
        return text('OK2')

    app.add_route(handler1, '/test')
    app.add_route(handler2, '/test2')

    request, response = app.test_client.get('/test')
    assert response.text == 'OK1'

    request, response = app.test_client.get('/test2')
    assert response.text == 'OK2'


def test_dynamic_add_route():
    app = Sanic('test_dynamic_add_route')

    results = []

    async def handler(request, name):
        results.append(name)
        return text('OK')

    app.add_route(handler, '/folder/<name>')
    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_add_route_string():
    app = Sanic('test_dynamic_add_route_string')

    results = []

    async def handler(request, name):
        results.append(name)
        return text('OK')

    app.add_route(handler, '/folder/<name:string>')
    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'

    request, response = app.test_client.get('/folder/favicon.ico')

    assert response.text == 'OK'
    assert results[1] == 'favicon.ico'


def test_dynamic_add_route_int():
    app = Sanic('test_dynamic_add_route_int')

    results = []

    async def handler(request, folder_id):
        results.append(folder_id)
        return text('OK')

    app.add_route(handler, '/folder/<folder_id:int>')

    request, response = app.test_client.get('/folder/12345')
    assert response.text == 'OK'
    assert type(results[0]) is int

    request, response = app.test_client.get('/folder/asdf')
    assert response.status == 404


def test_dynamic_add_route_number():
    app = Sanic('test_dynamic_add_route_number')

    results = []

    async def handler(request, weight):
        results.append(weight)
        return text('OK')

    app.add_route(handler, '/weight/<weight:number>')

    request, response = app.test_client.get('/weight/12345')
    assert response.text == 'OK'
    assert type(results[0]) is float

    request, response = app.test_client.get('/weight/1234.56')
    assert response.status == 200

    request, response = app.test_client.get('/weight/1234-56')
    assert response.status == 404


def test_dynamic_add_route_regex():
    app = Sanic('test_dynamic_route_int')

    async def handler(request, folder_id):
        return text('OK')

    app.add_route(handler, '/folder/<folder_id:[A-Za-z0-9]{0,4}>')

    request, response = app.test_client.get('/folder/test')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test1')
    assert response.status == 404

    request, response = app.test_client.get('/folder/test-123')
    assert response.status == 404

    request, response = app.test_client.get('/folder/')
    assert response.status == 200


def test_dynamic_add_route_unhashable():
    app = Sanic('test_dynamic_add_route_unhashable')

    async def handler(request, unhashable):
        return text('OK')

    app.add_route(handler, '/folder/<unhashable:[A-Za-z0-9/]+>/end/')

    request, response = app.test_client.get('/folder/test/asdf/end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test///////end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test/end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test/nope/')
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

    request, response = app.test_client.get('/test')
    assert response.status == 200

    request, response = app.test_client.post('/test')
    assert response.status == 405


def test_remove_static_route():
    app = Sanic('test_remove_static_route')

    async def handler1(request):
        return text('OK1')

    async def handler2(request):
        return text('OK2')

    app.add_route(handler1, '/test')
    app.add_route(handler2, '/test2')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    request, response = app.test_client.get('/test2')
    assert response.status == 200

    app.remove_route('/test')
    app.remove_route('/test2')

    request, response = app.test_client.get('/test')
    assert response.status == 404

    request, response = app.test_client.get('/test2')
    assert response.status == 404


def test_remove_dynamic_route():
    app = Sanic('test_remove_dynamic_route')

    async def handler(request, name):
        return text('OK')

    app.add_route(handler, '/folder/<name>')

    request, response = app.test_client.get('/folder/test123')
    assert response.status == 200

    app.remove_route('/folder/<name>')
    request, response = app.test_client.get('/folder/test123')
    assert response.status == 404


def test_remove_inexistent_route():
    app = Sanic('test_remove_inexistent_route')

    with pytest.raises(RouteDoesNotExist):
        app.remove_route('/test')


def test_remove_unhashable_route():
    app = Sanic('test_remove_unhashable_route')

    async def handler(request, unhashable):
        return text('OK')

    app.add_route(handler, '/folder/<unhashable:[A-Za-z0-9/]+>/end/')

    request, response = app.test_client.get('/folder/test/asdf/end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test///////end/')
    assert response.status == 200

    request, response = app.test_client.get('/folder/test/end/')
    assert response.status == 200

    app.remove_route('/folder/<unhashable:[A-Za-z0-9/]+>/end/')

    request, response = app.test_client.get('/folder/test/asdf/end/')
    assert response.status == 404

    request, response = app.test_client.get('/folder/test///////end/')
    assert response.status == 404

    request, response = app.test_client.get('/folder/test/end/')
    assert response.status == 404


def test_remove_route_without_clean_cache():
    app = Sanic('test_remove_static_route')

    async def handler(request):
        return text('OK')

    app.add_route(handler, '/test')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    app.remove_route('/test', clean_cache=True)

    request, response = app.test_client.get('/test')
    assert response.status == 404

    app.add_route(handler, '/test')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    app.remove_route('/test', clean_cache=False)

    request, response = app.test_client.get('/test')
    assert response.status == 200


def test_overload_routes():
    app = Sanic('test_dynamic_route')

    @app.route('/overload', methods=['GET'])
    async def handler1(request):
        return text('OK1')

    @app.route('/overload', methods=['POST', 'PUT'])
    async def handler2(request):
        return text('OK2')

    request, response = app.test_client.get('/overload')
    assert response.text == 'OK1'

    request, response = app.test_client.post('/overload')
    assert response.text == 'OK2'

    request, response = app.test_client.put('/overload')
    assert response.text == 'OK2'

    request, response = app.test_client.delete('/overload')
    assert response.status == 405

    with pytest.raises(RouteExists):
        @app.route('/overload', methods=['PUT', 'DELETE'])
        async def handler3(request):
            return text('Duplicated')


def test_unmergeable_overload_routes():
    app = Sanic('test_dynamic_route')

    @app.route('/overload_whole', methods=None)
    async def handler1(request):
        return text('OK1')

    with pytest.raises(RouteExists):
        @app.route('/overload_whole', methods=['POST', 'PUT'])
        async def handler2(request):
            return text('Duplicated')

    request, response = app.test_client.get('/overload_whole')
    assert response.text == 'OK1'

    request, response = app.test_client.post('/overload_whole')
    assert response.text == 'OK1'


    @app.route('/overload_part', methods=['GET'])
    async def handler1(request):
        return text('OK1')

    with pytest.raises(RouteExists):
        @app.route('/overload_part')
        async def handler2(request):
            return text('Duplicated')

    request, response = app.test_client.get('/overload_part')
    assert response.text == 'OK1'

    request, response = app.test_client.post('/overload_part')
    assert response.status == 405
