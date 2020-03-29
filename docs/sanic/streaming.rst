Streaming
=========

Request Streaming
-----------------

Sanic allows you to get request data by stream, as below. When the request ends, `await request.stream.read()` returns `None`. Only post, put and patch decorator have stream argument.

.. code-block:: python

    from sanic import Sanic
    from sanic.views import CompositionView
    from sanic.views import HTTPMethodView
    from sanic.views import stream as stream_decorator
    from sanic.blueprints import Blueprint
    from sanic.response import stream, text

    bp = Blueprint('blueprint_request_stream')
    app = Sanic(__name__)


    class SimpleView(HTTPMethodView):

        @stream_decorator
        async def post(self, request):
            result = ''
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                result += body.decode('utf-8')
            return text(result)


    @app.post('/stream', stream=True)
    async def handler(request):
        async def streaming(response):
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                body = body.decode('utf-8').replace('1', 'A')
                await response.write(body)
        return stream(streaming)


    @bp.put('/bp_stream', stream=True)
    async def bp_put_handler(request):
        result = ''
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode('utf-8').replace('1', 'A')
        return text(result)


    # You can also use `bp.add_route()` with stream argument
    async def bp_post_handler(request):
        result = ''
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode('utf-8').replace('1', 'A')
        return text(result)

    bp.add_route(bp_post_handler, '/bp_stream', methods=['POST'], stream=True)


    async def post_handler(request):
        result = ''
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode('utf-8')
        return text(result)

    app.blueprint(bp)
    app.add_route(SimpleView.as_view(), '/method_view')
    view = CompositionView()
    view.add(['POST'], post_handler, stream=True)
    app.add_route(view, '/composition_view')


    if __name__ == '__main__':
        app.run(host='127.0.0.1', port=8000)

Response Streaming
------------------

Sanic allows you to stream content to the client with the `stream` method. This method accepts a coroutine callback which is passed a `StreamingHTTPResponse` object that is written to. A simple example is like follows:

.. code-block:: python

    from sanic import Sanic
    from sanic.response import stream

    app = Sanic(__name__)

    @app.route("/")
    async def test(request):
        async def sample_streaming_fn(response):
            await response.write('foo,')
            await response.write('bar')

        return stream(sample_streaming_fn, content_type='text/csv')

This is useful in situations where you want to stream content to the client that originates in an external service, like a database. For example, you can stream database records to the client with the asynchronous cursor that `asyncpg` provides:

.. code-block:: python

    @app.route("/")
    async def index(request):
        async def stream_from_db(response):
            conn = await asyncpg.connect(database='test')
            async with conn.transaction():
                async for record in conn.cursor('SELECT generate_series(0, 10)'):
                    await response.write(record[0])

        return stream(stream_from_db)

If a client supports HTTP/1.1, Sanic will use `chunked transfer encoding <https://en.wikipedia.org/wiki/Chunked_transfer_encoding>`_; you can explicitly enable or disable it using `chunked` option of the `stream` function.

File Streaming
--------------

Sanic provides `sanic.response.file_stream` function that is useful when you want to send a large file. It returns a `StreamingHTTPResponse` object and will use chunked transfer encoding by default; for this reason Sanic doesn't add `Content-Length` HTTP header in the response. If you want to use this header, you can disable chunked transfer encoding and add it manually:

.. code-block:: python

    from aiofiles import os as async_os
    from sanic.response import file_stream

    @app.route("/")
    async def index(request):
        file_path = "/srv/www/whatever.png"

        file_stat = await async_os.stat(file_path)
        headers = {"Content-Length": str(file_stat.st_size)}

        return await file_stream(
            file_path,
            headers=headers,
            chunked=False,
        )
