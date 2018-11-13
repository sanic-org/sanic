import asyncio
import pytest

from sanic import Sanic
from sanic.response import text, json
from sanic.router import RouteExists, RouteDoesNotExist, ParameterNameConflicts
from sanic.constants import HTTP_METHODS


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #

@pytest.mark.parametrize('method', HTTP_METHODS)
def test_versioned_routes_get(app, method):
    method = method.lower()

    func = getattr(app, method)
    if callable(func):
        @func('/{}'.format(method), version=1)
        def handler(request):
            return text('OK')
    else:
        print(func)
        raise

    client_method = getattr(app.test_client, method)

    request, response = client_method('/v1/{}'.format(method))
    assert response.status == 200


def test_shorthand_routes_get(app):

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.post('/get')
    assert response.status == 405


def test_shorthand_routes_multiple(app):

    @app.get('/get')
    def get_handler(request):
        return text('OK')

    @app.options('/get')
    def options_handler(request):
        return text('')

    request, response = app.test_client.get('/get/')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.options('/get/')
    assert response.status == 200


def test_route_strict_slash(app):

    @app.get('/get', strict_slashes=True)
    def handler1(request):
        assert request.stream is None
        return text('OK')

    @app.post('/post/', strict_slashes=True)
    def handler2(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.get('/get/')
    assert response.status == 404

    request, response = app.test_client.post('/post/')
    assert response.text == 'OK'

    request, response = app.test_client.post('/post')
    assert response.status == 404


def test_route_invalid_parameter_syntax(app):
    with pytest.raises(ValueError):

        @app.get('/get/<:string>', strict_slashes=True)
        def handler(request):
            return text('OK')

        request, response = app.test_client.get('/get')


def test_route_strict_slash_default_value():
    app = Sanic('test_route_strict_slash', strict_slashes=True)

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get/')
    assert response.status == 404


def test_route_strict_slash_without_passing_default_value(app):

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'


def test_route_strict_slash_default_value_can_be_overwritten():
    app = Sanic('test_route_strict_slash', strict_slashes=True)

    @app.get('/get', strict_slashes=False)
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'


def test_route_slashes_overload(app):

    @app.get('/hello/')
    def handler_get(request):
        return text('OK')

    @app.post('/hello/')
    def handler_post(request):
        return text('OK')

    request, response = app.test_client.get('/hello')
    assert response.text == 'OK'

    request, response = app.test_client.get('/hello/')
    assert response.text == 'OK'

    request, response = app.test_client.post('/hello')
    assert response.text == 'OK'

    request, response = app.test_client.post('/hello/')
    assert response.text == 'OK'


def test_route_optional_slash(app):

    @app.get('/get')
    def handler(request):
        return text('OK')

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'


def test_route_strict_slashes_set_to_false_and_host_is_a_list(app):
    # Part of regression test for issue #1120

    site1 = '127.0.0.1:{}'.format(app.test_client.port)

    # before fix, this raises a RouteExists error
    @app.get('/get', host=[site1, 'site2.com'], strict_slashes=False)
    def get_handler(request):
        return text('OK')

    request, response = app.test_client.get('http://' + site1 + '/get')
    assert response.text == 'OK'

    @app.post('/post', host=[site1, 'site2.com'], strict_slashes=False)
    def post_handler(request):
        return text('OK')

    request, response = app.test_client.post('http://' + site1 + '/post')
    assert response.text == 'OK'

    @app.put('/put', host=[site1, 'site2.com'], strict_slashes=False)
    def put_handler(request):
        return text('OK')

    request, response = app.test_client.put('http://' + site1 + '/put')
    assert response.text == 'OK'

    @app.delete('/delete', host=[site1, 'site2.com'], strict_slashes=False)
    def delete_handler(request):
        return text('OK')

    request, response = app.test_client.delete('http://' + site1 + '/delete')
    assert response.text == 'OK'


def test_shorthand_routes_post(app):

    @app.post('/post')
    def handler(request):
        return text('OK')

    request, response = app.test_client.post('/post')
    assert response.text == 'OK'

    request, response = app.test_client.get('/post')
    assert response.status == 405


def test_shorthand_routes_put(app):

    @app.put('/put')
    def handler(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.put('/put')
    assert response.text == 'OK'

    request, response = app.test_client.get('/put')
    assert response.status == 405


def test_shorthand_routes_delete(app):

    @app.delete('/delete')
    def handler(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.delete('/delete')
    assert response.text == 'OK'

    request, response = app.test_client.get('/delete')
    assert response.status == 405


def test_shorthand_routes_patch(app):

    @app.patch('/patch')
    def handler(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.patch('/patch')
    assert response.text == 'OK'

    request, response = app.test_client.get('/patch')
    assert response.status == 405


def test_shorthand_routes_head(app):

    @app.head('/head')
    def handler(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.head('/head')
    assert response.status == 200

    request, response = app.test_client.get('/head')
    assert response.status == 405


def test_shorthand_routes_options(app):

    @app.options('/options')
    def handler(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is False

    request, response = app.test_client.options('/options')
    assert response.status == 200

    request, response = app.test_client.get('/options')
    assert response.status == 405


def test_static_routes(app):

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


def test_dynamic_route(app):
    results = []

    @app.route('/folder/<name>')
    async def handler(request, name):
        results.append(name)
        return text('OK')

    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_route_string(app):
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


def test_dynamic_route_int(app):
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


def test_dynamic_route_number(app):
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


def test_dynamic_route_regex(app):

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


def test_dynamic_route_uuid(app):
    import uuid

    results = []

    @app.route('/quirky/<unique_id:uuid>')
    async def handler(request, unique_id):
        results.append(unique_id)
        return text('OK')

    url = '/quirky/123e4567-e89b-12d3-a456-426655440000'
    request, response = app.test_client.get(url)
    assert response.text == 'OK'
    assert type(results[0]) is uuid.UUID

    request, response = app.test_client.get('/quirky/{}'.format(uuid.uuid4()))
    assert response.status == 200

    request, response = app.test_client.get('/quirky/non-existing')
    assert response.status == 404


def test_dynamic_route_path(app):

    @app.route('/<path:path>/info')
    async def handler(request, path):
        return text('OK')

    request, response = app.test_client.get('/path/1/info')
    assert response.status == 200

    request, response = app.test_client.get('/info')
    assert response.status == 404

    @app.route('/<path:path>')
    async def handler1(request, path):
        return text('OK')

    request, response = app.test_client.get('/info')
    assert response.status == 200

    request, response = app.test_client.get('/whatever/you/set')
    assert response.status == 200


def test_dynamic_route_unhashable(app):

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


def test_websocket_route(app):
    ev = asyncio.Event()

    @app.websocket('/ws')
    async def handler(request, ws):
        assert ws.subprotocol is None
        ev.set()

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13'})
    assert response.status == 101
    assert ev.is_set()


def test_websocket_route_with_subprotocols(app):
    results = []

    @app.websocket('/ws', subprotocols=['foo', 'bar'])
    async def handler(request, ws):
        results.append(ws.subprotocol)

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Protocol': 'bar'})
    assert response.status == 101

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Protocol': 'bar, foo'})
    assert response.status == 101

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Protocol': 'baz'})
    assert response.status == 101

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13'})
    assert response.status == 101

    assert results == ['bar', 'bar', None, None]


def test_route_duplicate(app):

    with pytest.raises(RouteExists):
        @app.route('/test')
        async def handler1(request):
            pass

        @app.route('/test')
        async def handler2(request):
            pass

    with pytest.raises(RouteExists):
        @app.route('/test/<dynamic>/')
        async def handler3(request, dynamic):
            pass

        @app.route('/test/<dynamic>/')
        async def handler4(request, dynamic):
            pass


def test_method_not_allowed(app):

    @app.route('/test', methods=['GET'])
    async def handler(request):
        return text('OK')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    request, response = app.test_client.post('/test')
    assert response.status == 405


def test_static_add_route(app):

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


def test_dynamic_add_route(app):

    results = []

    async def handler(request, name):
        results.append(name)
        return text('OK')

    app.add_route(handler, '/folder/<name>')
    request, response = app.test_client.get('/folder/test123')

    assert response.text == 'OK'
    assert results[0] == 'test123'


def test_dynamic_add_route_string(app):

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


def test_dynamic_add_route_int(app):
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


def test_dynamic_add_route_number(app):
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


def test_dynamic_add_route_regex(app):

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


def test_dynamic_add_route_unhashable(app):

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


def test_add_route_duplicate(app):

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


def test_add_route_method_not_allowed(app):

    async def handler(request):
        return text('OK')

    app.add_route(handler, '/test', methods=['GET'])

    request, response = app.test_client.get('/test')
    assert response.status == 200

    request, response = app.test_client.post('/test')
    assert response.status == 405


def test_remove_static_route(app):

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


def test_remove_dynamic_route(app):

    async def handler(request, name):
        return text('OK')

    app.add_route(handler, '/folder/<name>')

    request, response = app.test_client.get('/folder/test123')
    assert response.status == 200

    app.remove_route('/folder/<name>')
    request, response = app.test_client.get('/folder/test123')
    assert response.status == 404


def test_remove_inexistent_route(app):

    with pytest.raises(RouteDoesNotExist):
        app.remove_route('/test')


def test_removing_slash(app):

    @app.get('/rest/<resource>')
    def get(_):
        pass

    @app.post('/rest/<resource>')
    def post(_):
        pass

    assert len(app.router.routes_all.keys()) == 2


def test_remove_unhashable_route(app):

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


def test_remove_route_without_clean_cache(app):

    async def handler(request):
        return text('OK')

    app.add_route(handler, '/test')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    app.remove_route('/test', clean_cache=True)
    app.remove_route('/test/', clean_cache=True)

    request, response = app.test_client.get('/test')
    assert response.status == 404

    app.add_route(handler, '/test')

    request, response = app.test_client.get('/test')
    assert response.status == 200

    app.remove_route('/test', clean_cache=False)

    request, response = app.test_client.get('/test')
    assert response.status == 200


def test_overload_routes(app):

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


def test_unmergeable_overload_routes(app):

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
    async def handler3(request):
        return text('OK1')

    with pytest.raises(RouteExists):
        @app.route('/overload_part')
        async def handler4(request):
            return text('Duplicated')

    request, response = app.test_client.get('/overload_part')
    assert response.text == 'OK1'

    request, response = app.test_client.post('/overload_part')
    assert response.status == 405


def test_unicode_routes(app):

    @app.get('/你好')
    def handler1(request):
        return text('OK1')

    request, response = app.test_client.get('/你好')
    assert response.text == 'OK1'

    @app.route('/overload/<param>', methods=['GET'])
    async def handler2(request, param):
        return text('OK2 ' + param)

    request, response = app.test_client.get('/overload/你好')
    assert response.text == 'OK2 你好'


def test_uri_with_different_method_and_different_params(app):

    @app.route('/ads/<ad_id>', methods=['GET'])
    async def ad_get(request, ad_id):
        return json({'ad_id': ad_id})

    @app.route('/ads/<action>', methods=['POST'])
    async def ad_post(request, action):
        return json({'action': action})

    request, response = app.test_client.get('/ads/1234')
    assert response.status == 200
    assert response.json == {
        'ad_id': '1234'
    }

    request, response = app.test_client.post('/ads/post')
    assert response.status == 200
    assert response.json == {
        'action': 'post'
    }


def test_route_raise_ParameterNameConflicts(app):
    with pytest.raises(ParameterNameConflicts):
        @app.get('/api/v1/<user>/<user>/')
        def handler(request, user):
            return text('OK')
