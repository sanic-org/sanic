# Streaming

## Request streaming

Sanic allows you to stream data sent by the client to begin processing data as the bytes arrive.

.. column::

    When enabled on an endpoint, you can stream the request body using `await request.stream.read()`.

    That method will return `None` when the body is completed.

.. column::

    ```python
    from sanic.views import stream

    class SimpleView(HTTPMethodView):
        @stream
        async def post(self, request):
            result = ""
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                result += body.decode("utf-8")
            return text(result)
    ```


.. column::

    It also can be enabled with a keyword argument in the decorator...

.. column::

    ```python
    @app.post("/stream", stream=True)
    async def handler(request):
            ...
            body = await request.stream.read()
            ...
    ```


.. column::

    ... or the `add_route()` method.

.. column::

    ```python
    bp.add_route(
        bp_handler,
        "/bp_stream",
        methods=["POST"],
        stream=True,
    )
    ```



.. tip:: FYI

    Only post, put and patch decorators have stream argument.


## Response streaming

.. column::

    Sanic allows you to stream content to the client.

.. column::

    ```python
    @app.route("/")
    async def test(request):
        response = await request.respond(content_type="text/csv")
        await response.send("foo,")
        await response.send("bar")

        # Optionally, you can explicitly end the stream by calling:
        await response.eof()
    ```

This is useful in situations where you want to stream content to the client that originates in an external service, like a database. For example, you can stream database records to the client with the asynchronous cursor that `asyncpg` provides.

```python
@app.route("/")
async def index(request):
    response = await request.respond()
    conn = await asyncpg.connect(database='test')
    async with conn.transaction():
        async for record in conn.cursor('SELECT generate_series(0, 10)'):
            await response.send(record[0])
```


You can explicitly end a stream by calling `await response.eof()`. It a convenience method to replace `await response.send("", True)`. It should be called **one time** *after* your handler has determined that it has nothing left to send back to the client. While it is *optional* to use with Sanic server, if you are running Sanic in ASGI mode, then you **must** explicitly terminate the stream.

*Calling `eof` became optional in v21.6*

## File streaming

.. column::

    Sanic provides `sanic.response.file_stream` function that is useful when you want to send a large file. It returns a `StreamingHTTPResponse` object and will use chunked transfer encoding by default; for this reason Sanic doesn’t add `Content-Length` HTTP header in the response.

    A typical use case might be streaming an video file.

.. column::

    ```python
    @app.route("/mp4")
    async def handler_file_stream(request):
        return await response.file_stream(
            "/path/to/sample.mp4",
            chunk_size=1024,
            mime_type="application/metalink4+xml",
            headers={
                "Content-Disposition": 'Attachment; filename="nicer_name.meta4"',
                "Content-Type": "application/metalink4+xml",
            },
        )
    ```


.. column::

    If you want to use the `Content-Length` header, you can disable chunked transfer encoding and add it manually simply by adding the `Content-Length` header.

.. column::

    ```python
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
        )
    ```

