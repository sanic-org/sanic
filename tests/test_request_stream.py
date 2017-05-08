import asyncio
from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.views import CompositionView
from sanic.views import HTTPMethodView
from sanic.views import stream as stream_decorator
from sanic.response import stream, text

data = "abc" * 100000


def test_request_stream_method_view():
    '''for self.is_request_stream = True'''

    app = Sanic('test_request_stream_method_view')

    class SimpleView(HTTPMethodView):

        def get(self, request):
            assert request.stream is None
            return text('OK')

        @stream_decorator
        async def post(self, request):
            assert isinstance(request.stream, asyncio.Queue)
            result = ''
            while True:
                body = await request.stream.get()
                if body is None:
                    break
                result += body.decode('utf-8')
            return text(result)

    app.add_route(SimpleView.as_view(), '/method_view')

    assert app.is_request_stream is True

    request, response = app.test_client.get('/method_view')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/method_view', data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream_app():
    '''for self.is_request_stream = True'''

    app = Sanic('test_request_stream_app')

    @app.stream('/stream')
    async def handler(request):
        assert isinstance(request.stream, asyncio.Queue)

        async def streaming(response):
            while True:
                body = await request.stream.get()
                if body is None:
                    break
                response.write(body.decode('utf-8'))
        return stream(streaming)

    @app.get('/get')
    async def get(request):
        assert request.stream is None
        return text('OK')

    assert app.is_request_stream is True

    request, response = app.test_client.get('/get')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/stream', data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream_blueprint():
    '''for self.is_request_stream = True'''

    app = Sanic('test_request_stream_blueprint')
    bp = Blueprint('test_blueprint_request_stream_blueprint')

    @bp.stream('/bp_stream')
    async def bp_stream(request):
        assert isinstance(request.stream, asyncio.Queue)
        result = ''
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)

    @bp.get('/bp_get')
    async def bp_get(request):
        assert request.stream is None
        return text('OK')

    app.blueprint(bp)

    assert app.is_request_stream is True

    request, response = app.test_client.get('/bp_get')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/bp_stream', data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream_composition_view():
    '''for self.is_request_stream = True'''

    app = Sanic('test_request_stream__composition_view')

    def get_handler(request):
        assert request.stream is None
        return text('OK')

    async def post_handler(request):
        assert isinstance(request.stream, asyncio.Queue)
        result = ''
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)

    view = CompositionView()
    view.add(['GET'], get_handler)
    view.add(['POST'], post_handler, stream=True)
    app.add_route(view, '/composition_view')

    assert app.is_request_stream is True

    request, response = app.test_client.get('/composition_view')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/composition_view', data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream():
    '''test for complex application'''

    bp = Blueprint('test_blueprint_request_stream')
    app = Sanic('test_request_stream')

    class SimpleView(HTTPMethodView):

        def get(self, request):
            assert request.stream is None
            return text('OK')

        @stream_decorator
        async def post(self, request):
            assert isinstance(request.stream, asyncio.Queue)
            result = ''
            while True:
                body = await request.stream.get()
                if body is None:
                    break
                result += body.decode('utf-8')
            return text(result)

    @app.stream('/stream')
    async def handler(request):
        assert isinstance(request.stream, asyncio.Queue)

        async def streaming(response):
            while True:
                body = await request.stream.get()
                if body is None:
                    break
                response.write(body.decode('utf-8'))
        return stream(streaming)

    @app.get('/get')
    async def get(request):
        assert request.stream is None
        return text('OK')

    @bp.stream('/bp_stream')
    async def bp_stream(request):
        assert isinstance(request.stream, asyncio.Queue)
        result = ''
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)

    @bp.get('/bp_get')
    async def bp_get(request):
        assert request.stream is None
        return text('OK')

    def get_handler(request):
        assert request.stream is None
        return text('OK')

    async def post_handler(request):
        assert isinstance(request.stream, asyncio.Queue)
        result = ''
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)

    app.add_route(SimpleView.as_view(), '/method_view')

    view = CompositionView()
    view.add(['GET'], get_handler)
    view.add(['POST'], post_handler, stream=True)

    app.blueprint(bp)

    app.add_route(view, '/composition_view')

    assert app.is_request_stream is True

    request, response = app.test_client.get('/method_view')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/method_view', data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get('/composition_view')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/composition_view', data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get('/get')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/stream', data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get('/bp_get')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/bp_stream', data=data)
    assert response.status == 200
    assert response.text == data
