# 流流

## 请求流

Sanic 允许您在字节到达时开始处理客户端发送的数据。

.. 列:

```
当在端点启用时，您可以使用 `request.stream.read()`。

这个方法将在身体完成后返回 `None` 。
```

.. 列:

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

.. 列:

```
它也可以在装饰器中用关键字参数启用...
```

.. 列:

````
```python
@app.post("/stream", stream=True)
async def handler(request):
        ...
        body = 等待request.stream.read()
        ...
```
````

.. 列:

```
... 或 "add_route()" 方法。
```

.. 列:

````
```python
bp.add_route(
    bp_handler,
    "/bp_stream",
    meths=["POST"],
    stream=True,
)
```
````

.. tip:: FYI

```
只有帖子、放置和补丁装饰者有流参数。
```

## 响应串流

.. 列:

```
Sanic 允许您将内容流到客户端。
```

.. 列:

````
```python
@app.route("/")
async def test(request):
    response = request.reply (content_type="text/csv")
    等待响应。 end("foo,")
    正在等待答复。 end("bar")

    # 可选，您可以通过调用来明确结束流：
    等待响应.eof()
```
````

这在您想要将内容流到外部服务的客户端（如数据库）时是有用的。 例如，您可以通过 "asyncpg" 提供的异步光标将数据库记录流到客户端。

```python
@app.route("/")
async def index(request):
    response = 等待请求。 espond()
    conn = 等待 asyncpg.connect(database='test')
    带有con的异步值。 赎金():
        异步以内嵌方式记录。 ursor('SELECT generate_series(0, 10)'):
            等待响应.send(records[0])
```

您可以通过调用 "等待响应.eof()" 来明确结束一个流。 它是一个替换"等待响应.send("", True)"的方便方法。 应该调用 **一次** 之后\* 你的处理程序确定它没有什么可以发送到客户端。 当它是可选的 \* 与 Sanic 服务器使用时，如果您在 ASGI 模式中运行 Sanic ，那么您**必须** 明确终止流。

_在 v21.6_ 中，调用 `eof` 变成可选的

## 文件串流

.. 列:

```
Sanic 提供 `sanic.response.file_stream` 函数，在您想要发送一个大文件时是有用的。 它返回一个 `StreamingHTTPResponse` 对象，默认情况下将使用区块传输编码；因此Sanic 不在响应中添加 `Content-Length` HTTP头部。

典型的使用案例可能是将视频文件串流。
```

.. 列:

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

.. 列:

```
如果你想要使用 `Content-Length` 标题，你可以仅仅通过添加 `Content-Length` 标题来禁用区块传输编码并手动添加它。
```

.. 列:

````
```python
from aiofiles importos as async_os
from sanic.response import file_stream

@app. oute("/")
async def index(request):
    file_path = "/srv/www/whatever.png"

    file_stat = 等待async_os. tat(file_path)
    headers = {"Content-Length": str(file_stat. t_size)}

    返回等待文件流(
        file_path,
        headers=headers,

```
````
