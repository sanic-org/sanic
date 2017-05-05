from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import stream, text

bp = Blueprint('test_blueprint_request_stream')
app = Sanic('test_request_stream')


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
async def bp_handler(request):
    result = ''
    while True:
        body = await request.stream.get()
        if body is None:
            break
        result += body.decode('utf-8')
    return text(result)

app.blueprint(bp)


def test_request_stream():
    data = "abc" * 100000
    request, response = app.test_client.post('/stream', data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get('/get')
    assert response.status == 200
    assert response.text == 'OK'

    request, response = app.test_client.post('/bp_stream', data=data)
    assert response.status == 200
    assert response.text == data
