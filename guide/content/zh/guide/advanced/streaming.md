# 流式传输(Streaming)

## 请求流(Request streaming)

Sanic 允许您流式处理客户端发送的数据，以便在字节到达时立即开始处理数据。

.. column::

```
当在路由入口上启用流式处理时，您可以使用 `await request.stream.read()` 来流式读取请求体。

当请求体读取完毕时，该方法将返回 `None`。
```

.. column::

````
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
````

.. column::

```
也可以在装饰器中通过关键字参数启用该功能...
```

.. column::

````
```python
@app.post("/stream", stream=True)
async def handler(request):
        ...
        body = await request.stream.read()
        ...
```
````

.. column::

```
... 或者使用`add_route()` 方法
```

.. column::

````
```python
bp.add_route(
    bp_handler,
    "/bp_stream",
    methods=["POST"],
    stream=True,
)
```
````

.. tip:: 提示一下

```
只有post、put和patch这三个装饰器具有stream参数。
```

## 响应流（Response streaming）

.. column::

```
Sanic 支持向客户端流式传输内容。
```

.. column::

````
```python
@app.route("/")
async def test(request):
    response = await request.respond(content_type="text/csv")
    await response.send("foo,")
    await response.send("bar")

    # Optionally, you can explicitly end the stream by calling:
    await response.eof()
```
````

在需要将源自外部服务（例如数据库）的内容实时传输给客户端的情况下，这项功能非常有用。 举例来说，您可以利用`asyncpg`提供的异步游标将数据库记录逐条流式传输至客户端。

```python
@app.route("/")
async def index(request):
    response = await request.respond()
    conn = await asyncpg.connect(database='test')
    async with conn.transaction():
        async for record in conn.cursor('SELECT generate_series(0, 10)'):
            await response.send(record[0])
```

您可以通过调用 `await response.eof()` 显式结束一个流。 这是一个便捷方法，替代了 `await response.send("", True)`。 在处理器确定已无任何内容需要发送回客户端后，应调用**一次**此方法。 管在Sanic服务器中使用它是可选的，但如果在ASGI模式下运行Sanic，则必须显式终止流。

_自v21.6版本起，调用`eof`变为可选_

## 文件流(File streaming)

.. column::

```
Sanic 提供了一个名为 `sanic.response.file_stream` 的函数，当您需要发送大文件时，这个函数非常有用。它会返回一个 `StreamingHTTPResponse` 对象，默认采用分块传输编码；因此，Sanic 不会在响应中添加 `Content-Length` HTTP 头部信息。

典型应用场景可能是流式传输视频文件。
```

.. column::

````
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
````

.. column::

```
如果您希望使用 `Content-Length` 头部信息，可以通过禁用分块传输编码并手动添加它来实现。只需简单地向响应中添加 `Content-Length` 头部即可。
```

.. column::

````
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
````

