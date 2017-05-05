from sanic import Sanic
from sanic.response import stream

app = Sanic(__name__, is_request_stream=True)


@app.post('/stream')
async def handler(request):
    async def sample_streaming_fn(response):
        while True:
            body = await request.stream.get()
            if body is None:
                break
            print('Hello!')
            body = body.decode('utf-8').replace('1', 'A')
            response.write(body)
    return stream(sample_streaming_fn)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
