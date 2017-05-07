from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.views import CompositionView
from sanic.views import HTTPMethodView
from sanic.views import stream as stream_decorator
from sanic.response import stream, text

bp = Blueprint('test_blueprint_request_stream')
app = Sanic('test_request_stream')


class SimpleView(HTTPMethodView):

    def get(self, request):
        return text('OK')

    @stream_decorator
    async def post(self, request):
        result = ''
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)


@app.stream('/stream')
async def handler(request):
    async def streaming(response):
        while True:
            body = await request.stream.get()
            if body is None:
                break
            response.write(body.decode('utf-8'))
    return stream(streaming)


@app.get('/get')
async def get(request):
    return text('OK')


@bp.stream('/bp_stream')
async def bp_stream(request):
    result = ''
    while True:
        body = await request.stream.get()
        if body is None:
            break
        result += body.decode('utf-8')
    return text(result)


@bp.get('/bp_get')
async def bp_get(request):
    return text('OK')


def get_handler(request):
    return text('OK')


async def post_handler(request):
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


def test_request_stream():
    data = "abc" * 100000

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
