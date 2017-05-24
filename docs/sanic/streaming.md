# Streaming

Sanic allows you to stream content to the client with the `stream` method. This method accepts a coroutine callback which is passed a `StreamingHTTPResponse` object that is written to. A simple example is like follows:

```python
from sanic import Sanic
from sanic.response import stream

app = Sanic(__name__)

@app.route("/")
async def test(request):
    async def sample_streaming_fn(response):
        response.write('foo,')
        response.write('bar')

    return stream(sample_streaming_fn, content_type='text/csv')
```

This is useful in situations where you want to stream content to the client that originates in an external service, like a database. For example, you can stream database records to the client with the asynchronous cursor that `asyncpg` provides:

```python
@app.route("/")
async def index(request):
    async def stream_from_db(response):
        conn = await asyncpg.connect(database='test')
        async with conn.transaction():
            async for record in conn.cursor('SELECT generate_series(0, 10)'):
                response.write(record[0])

    return stream(stream_from_db)
```

## Request Streaming

Sanic allows you to get request data by stream, as below. It is necessary to set `is_request_stream` to True. When the request ends, `request.stream.get()` returns `None`. It is not able to use common request and request stream in same application.

```
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
            body = body.decode('utf-8').replace('1', 'A')
            response.write(body)
    return stream(sample_streaming_fn)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
```
