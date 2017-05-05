from sanic import Sanic
from sanic.response import stream

app = Sanic('test_request_stream', is_request_stream=True)


@app.post('/stream')
async def handler(request):
    async def sample_streaming_fn(response):
        while True:
            body = await request.stream.get()
            if body is None:
                break
            body = body.decode('utf-8').replace('1', 'A')
            response.write(body)
    return stream(sample_streaming_fn)


def test_request_stream():
    data = ""
    for i in range(1, 250000):
        data += str(i)
    request, response = app.test_client.post('/stream', data=data)
    text = data.replace('1', 'A')
    assert response.status == 200
    assert response.text == text
