import asyncio
import inspect
import os
import pytest

from sanic.blueprints import Blueprint
from sanic.response import text
from sanic.exceptions import NotFound, ServerError, InvalidUsage
from sanic.constants import HTTP_METHODS


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), 'rb') as file:
        return file.read()


@pytest.mark.parametrize('method', HTTP_METHODS)
def test_versioned_routes_get(app, method):
    bp = Blueprint('test_text')

    method = method.lower()

    func = getattr(bp, method)
    if callable(func):
        @func('/{}'.format(method), version=1)
        def handler(request):
            return text('OK')
    else:
        print(func)
        raise

    app.blueprint(bp)

    client_method = getattr(app.test_client, method)

    request, response = client_method('/v1/{}'.format(method))
    assert response.status == 200


def test_bp(app):
    bp = Blueprint('test_text')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    app.blueprint(bp)
    request, response = app.test_client.get('/')
    assert app.is_request_stream is False

    assert response.text == 'Hello'


def test_bp_strict_slash(app):
    bp = Blueprint('test_text')

    @bp.get('/get', strict_slashes=True)
    def get_handler(request):
        return text('OK')

    @bp.post('/post/', strict_slashes=True)
    def post_handler(request):
        return text('OK')

    app.blueprint(bp)

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'
    assert response.json is None

    request, response = app.test_client.get('/get/')
    assert response.status == 404

    request, response = app.test_client.post('/post/')
    assert response.text == 'OK'

    request, response = app.test_client.post('/post')
    assert response.status == 404


def test_bp_strict_slash_default_value(app):
    bp = Blueprint('test_text', strict_slashes=True)

    @bp.get('/get')
    def get_handler(request):
        return text('OK')

    @bp.post('/post/')
    def post_handler(request):
        return text('OK')

    app.blueprint(bp)

    request, response = app.test_client.get('/get/')
    assert response.status == 404

    request, response = app.test_client.post('/post')
    assert response.status == 404


def test_bp_strict_slash_without_passing_default_value(app):
    bp = Blueprint('test_text')

    @bp.get('/get')
    def get_handler(request):
        return text('OK')

    @bp.post('/post/')
    def post_handler(request):
        return text('OK')

    app.blueprint(bp)

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'

    request, response = app.test_client.post('/post')
    assert response.text == 'OK'


def test_bp_strict_slash_default_value_can_be_overwritten(app):
    bp = Blueprint('test_text', strict_slashes=True)

    @bp.get('/get', strict_slashes=False)
    def get_handler(request):
        return text('OK')

    @bp.post('/post/', strict_slashes=False)
    def post_handler(request):
        return text('OK')

    app.blueprint(bp)

    request, response = app.test_client.get('/get/')
    assert response.text == 'OK'

    request, response = app.test_client.post('/post')
    assert response.text == 'OK'


def test_bp_with_url_prefix(app):
    bp = Blueprint('test_text', url_prefix='/test1')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    app.blueprint(bp)
    request, response = app.test_client.get('/test1/')

    assert response.text == 'Hello'


def test_several_bp_with_url_prefix(app):
    bp = Blueprint('test_text', url_prefix='/test1')
    bp2 = Blueprint('test_text2', url_prefix='/test2')

    @bp.route('/')
    def handler(request):
        return text('Hello')

    @bp2.route('/')
    def handler2(request):
        return text('Hello2')

    app.blueprint(bp)
    app.blueprint(bp2)
    request, response = app.test_client.get('/test1/')
    assert response.text == 'Hello'

    request, response = app.test_client.get('/test2/')
    assert response.text == 'Hello2'


def test_bp_with_host(app):
    bp = Blueprint('test_bp_host', url_prefix='/test1', host="example.com")

    @bp.route('/')
    def handler1(request):
        return text('Hello')

    @bp.route('/', host="sub.example.com")
    def handler2(request):
        return text('Hello subdomain!')

    app.blueprint(bp)
    headers = {"Host": "example.com"}
    request, response = app.test_client.get(
        '/test1/',
        headers=headers)
    assert response.text == 'Hello'

    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get(
        '/test1/',
        headers=headers)

    assert response.text == 'Hello subdomain!'


def test_several_bp_with_host(app):
    bp = Blueprint('test_text',
                   url_prefix='/test',
                   host="example.com")
    bp2 = Blueprint('test_text2',
                    url_prefix='/test',
                    host="sub.example.com")

    @bp.route('/')
    def handler(request):
        return text('Hello')

    @bp2.route('/')
    def handler1(request):
        return text('Hello2')

    @bp2.route('/other/')
    def handler2(request):
        return text('Hello3')

    app.blueprint(bp)
    app.blueprint(bp2)

    assert bp.host == "example.com"
    headers = {"Host": "example.com"}
    request, response = app.test_client.get(
        '/test/',
        headers=headers)
    assert response.text == 'Hello'

    assert bp2.host == "sub.example.com"
    headers = {"Host": "sub.example.com"}
    request, response = app.test_client.get(
        '/test/',
        headers=headers)

    assert response.text == 'Hello2'
    request, response = app.test_client.get(
        '/test/other/',
        headers=headers)
    assert response.text == 'Hello3'


def test_bp_middleware(app):
    blueprint = Blueprint('test_middleware')

    @blueprint.middleware('response')
    async def process_response(request, response):
        return text('OK')

    @app.route('/')
    async def handler(request):
        return text('FAIL')

    app.blueprint(blueprint)

    request, response = app.test_client.get('/')

    assert response.status == 200
    assert response.text == 'OK'


def test_bp_exception_handler(app):
    blueprint = Blueprint('test_middleware')

    @blueprint.route('/1')
    def handler_1(request):
        raise InvalidUsage("OK")

    @blueprint.route('/2')
    def handler_2(request):
        raise ServerError("OK")

    @blueprint.route('/3')
    def handler_3(request):
        raise NotFound("OK")

    @blueprint.exception(NotFound, ServerError)
    def handler_exception(request, exception):
        return text("OK")

    app.blueprint(blueprint)

    request, response = app.test_client.get('/1')
    assert response.status == 400

    request, response = app.test_client.get('/2')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.get('/3')
    assert response.status == 200


def test_bp_listeners(app):
    blueprint = Blueprint('test_middleware')

    order = []

    @blueprint.listener('before_server_start')
    def handler_1(sanic, loop):
        order.append(1)

    @blueprint.listener('after_server_start')
    def handler_2(sanic, loop):
        order.append(2)

    @blueprint.listener('after_server_start')
    def handler_3(sanic, loop):
        order.append(3)

    @blueprint.listener('before_server_stop')
    def handler_4(sanic, loop):
        order.append(5)

    @blueprint.listener('before_server_stop')
    def handler_5(sanic, loop):
        order.append(4)

    @blueprint.listener('after_server_stop')
    def handler_6(sanic, loop):
        order.append(6)

    app.blueprint(blueprint)

    request, response = app.test_client.get('/')

    assert order == [1, 2, 3, 4, 5, 6]


def test_bp_static(app):
    current_file = inspect.getfile(inspect.currentframe())
    with open(current_file, 'rb') as file:
        current_file_contents = file.read()

    blueprint = Blueprint('test_static')

    blueprint.static('/testing.file', current_file)

    app.blueprint(blueprint)

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert response.body == current_file_contents


@pytest.mark.parametrize('file_name', ['test.html'])
def test_bp_static_content_type(app, file_name):
    # This is done here, since no other test loads a file here
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, 'static')

    blueprint = Blueprint('test_static')
    blueprint.static(
        '/testing.file',
        get_file_path(static_directory, file_name),
        content_type='text/html; charset=utf-8'
    )

    app.blueprint(blueprint)

    request, response = app.test_client.get('/testing.file')
    assert response.status == 200
    assert response.body == get_file_content(static_directory, file_name)
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


def test_bp_shorthand(app):
    blueprint = Blueprint('test_shorhand_routes')
    ev = asyncio.Event()

    @blueprint.get('/get')
    def handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.put('/put')
    def put_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.post('/post')
    def post_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.head('/head')
    def head_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.options('/options')
    def options_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.patch('/patch')
    def patch_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.delete('/delete')
    def delete_handler(request):
        assert request.stream is None
        return text('OK')

    @blueprint.websocket('/ws')
    async def websocket_handler(request, ws):
        assert request.stream is None
        ev.set()

    app.blueprint(blueprint)

    assert app.is_request_stream is False

    request, response = app.test_client.get('/get')
    assert response.text == 'OK'

    request, response = app.test_client.post('/get')
    assert response.status == 405

    request, response = app.test_client.put('/put')
    assert response.text == 'OK'

    request, response = app.test_client.get('/post')
    assert response.status == 405

    request, response = app.test_client.post('/post')
    assert response.text == 'OK'

    request, response = app.test_client.get('/post')
    assert response.status == 405

    request, response = app.test_client.head('/head')
    assert response.status == 200

    request, response = app.test_client.get('/head')
    assert response.status == 405

    request, response = app.test_client.options('/options')
    assert response.text == 'OK'

    request, response = app.test_client.get('/options')
    assert response.status == 405

    request, response = app.test_client.patch('/patch')
    assert response.text == 'OK'

    request, response = app.test_client.get('/patch')
    assert response.status == 405

    request, response = app.test_client.delete('/delete')
    assert response.text == 'OK'

    request, response = app.test_client.get('/delete')
    assert response.status == 405

    request, response = app.test_client.get('/ws', headers={
        'Upgrade': 'websocket',
        'Connection': 'upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13'})
    assert response.status == 101
    assert ev.is_set()


def test_bp_group(app):
    deep_0 = Blueprint('deep_0', url_prefix='/deep')
    deep_1 = Blueprint('deep_1', url_prefix='/deep1')

    @deep_0.route('/')
    def handler(request):
        return text('D0_OK')

    @deep_1.route('/bottom')
    def bottom_handler(request):
        return text('D1B_OK')

    mid_0 = Blueprint.group(deep_0, deep_1, url_prefix='/mid')
    mid_1 = Blueprint('mid_tier', url_prefix='/mid1')

    @mid_1.route('/')
    def handler1(request):
        return text('M1_OK')

    top = Blueprint.group(mid_0, mid_1)

    app.blueprint(top)

    @app.route('/')
    def handler2(request):
        return text('TOP_OK')

    request, response = app.test_client.get('/')
    assert response.text == 'TOP_OK'

    request, response = app.test_client.get('/mid1')
    assert response.text == 'M1_OK'

    request, response = app.test_client.get('/mid/deep')
    assert response.text == 'D0_OK'

    request, response = app.test_client.get('/mid/deep1/bottom')
    assert response.text == 'D1B_OK'


def test_bp_group_with_default_url_prefix(app):

    from sanic.response import json
    bp_resources = Blueprint('bp_resources')

    @bp_resources.get('/')
    def list_resources_handler(request):
        resource = {}
        return json([resource])

    bp_resource = Blueprint('bp_resource', url_prefix='/<resource_id>')

    @bp_resource.get('/')
    def get_resource_hander(request, resource_id):
        resource = {'resource_id': resource_id}
        return json(resource)

    bp_resources_group = Blueprint.group(bp_resources, bp_resource,
                                         url_prefix='/resources')
    bp_api_v1 = Blueprint('bp_api_v1')

    @bp_api_v1.get('/info')
    def api_v1_info(request):
        return text('api_version: v1')

    bp_api_v1_group = Blueprint.group(bp_api_v1, bp_resources_group,
                                      url_prefix='/v1')
    bp_api_group = Blueprint.group(bp_api_v1_group, url_prefix='/api')
    app.blueprint(bp_api_group)

    request, response = app.test_client.get('/api/v1/info')
    assert response.text == 'api_version: v1'

    request, response = app.test_client.get('/api/v1/resources')
    assert response.json == [{}]

    from uuid import uuid4
    resource_id = str(uuid4())
    request, response = app.test_client.get(
        '/api/v1/resources/{0}'.format(resource_id))
    assert response.json == {'resource_id': resource_id}
