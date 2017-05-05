from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import stream, text

bp = Blueprint('blueprint_request_stream')
app = Sanic('request_stream')


@app.stream('/stream')
async def handler(request):
    async def streaming(response):
        while True:
            body = await request.stream.get()
            if body is None:
                break
            body = body.decode('utf-8').replace('1', 'A')
            response.write(body)
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
        result += body.decode('utf-8').replace('1', 'A')
    return text(result)

app.blueprint(bp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
