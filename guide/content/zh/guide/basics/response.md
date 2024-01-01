# 答复

所有 [handlers](./handlers.md) _通常_返回一个响应对象， [middleware](./midd) 可以选择返回一个响应对象。

2. 澄清该陈述：

- unless the handler is a streaming endpoint handling its own pattern for sending bytes to the client, the return value must be an instance of :class:`sanic.response.HTTPResponse` (to learn more about this exception see [streaming responses](../advanced/streaming.md#response-streaming)). 在 **最多** 个案件中，您需要返回响应。
- 如果中间件返回响应对象，这将被用来代替处理程序所做的任何(见 [middleware](./midd) 来了解更多)。

最基本的处理程序看起来就像下面一样。 The :class:`sanic.response.HTTPResponse` object will allow you to set the status, body, and headers to be returned to the client.

```python
从 HTTPResponse, Sanic

app = Sanic("TestApp")

@app.route("")
def handler(_):
    return HTTPResponse()
```

然而，通常较容易使用下文讨论的一种方便方法。

## 方法

生成响应对象的最简单方法是使用一个方便函数。

### 文本

.. 列:

```
**默认内容类型**: `text/plain; charset=utf-8`  
**描述**: 返回纯文本
```

.. 列:

````
```python
from sanic import text

@app.route("/")
async def handler(request):
    return text("Hi 😎")
```
````

### HTML

.. 列:

```
**默认内容类型**: `text/html; charset=utf-8`  
**描述**: 返回一个 HTML 文档
```

.. 列:

````
```python
from sanic import html

@app.route("/")
async def handler(request):
    return html('<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><div>Hi 😎</div>')
```
````

### JSON

.. 列:

```
**默认 Content-Type**: `application/json`  
**Description**: 返回 JSON 文档
```

.. 列:

````
```python
from sanic import json

@app.route("/")
async def handler(request):
    return json({"foo": "bar"})
```
````

默认情况下，是 [`ujson`](https://github.com/ultrajson/ultrajson)的 Sanic 船舶，作为其JSON 编码器。 如果未安装 `ujson` ，它将返回到标准库`json` 模块。

如果你想要更改这一点是非常简单的。

```python
from sanic import json
from orjson import dumps

json({"foo": "bar"}, dumps=dumps)
```

您还可以声明在初始化时在全局使用哪些实现：

```python
从 orjson 导入转储

应用 = Sanic(..., dumps=dumps)
```

### 文件

.. 列:

```
**默认内容类型**：N/  
**描述**：返回一个文件
```

.. 列:

````
```python
from sanic import file

@app.route("/")
async def handler(request):
    return 等待文件 ("/path/to/whatever.png")
```
````

Sanic 将检查该文件，并尝试和猜其mime 类型并使用一个适当的内容类型值。 如果您想要：

```python
file("/path/to/whatever.png", mime_type="image/png")
```

您也可以选择覆盖文件名称：

```python
file("/path/to/whatever.png", filename="超级超棒不可思议的.png")
```

### 文件流

.. 列:

```
**默认内容类型**: N/A  
**描述**: 流一个文件到一个客户端, 当像视频一样流出大文件时有用。
```

.. 列:

````
```python
from sanic.response import file_stream

@app.route("/")
async def handler(request):
    return await file_stream("/path/to/whatever.mp4")
```
````

和`file()`方法一样，`file_stream()`会尝试确定文件的 mime 类型。

### 原始文件

.. 列:

```
**默认Content-Type**: `application/octet-stream`  
**Description**: 发送原始字节而不对正文进行编码
```

.. 列:

````
```python
from sanic import raw

@app.route("/")
async def handler(request):
    return raw(B"raw bytes")
```
````

### 重定向

.. 列:

```
**默认Content-Type**: `text/html; charset=utf-8`  
**Description**: 发送一个 `302` 响应来将客户重定向到另一个路径
```

.. 列:

````
```python
from sanic import redirecte

@app.route("/")
async def handler(request):
    return redirect("/login")
```
````

### 空的

.. 列:

```
**默认 Content-Type**: N/A  
**Description**: 为响应[RFC 2616](https://tools.ietf.org/search/rfc2616#section-7.2.1)
```

.. 列:

````
```python
来自sanic import 空

@app.route("/")
async def handler(request):
    return empty()
```

默认`204` 状态。
````

## 默认状态

响应默认的 HTTP 状态代码是 \`200'。 如果您需要更改它，它可以通过响应方式完成。

```python
@app.post("/")
async def create_new(request):
    new_thing = 等待do_create(request)
    return json({"created": True, "id": new_thing.thing_id}, status=201)
```

## 返回 JSON 数据

Starting in v22.12, When you use the `sanic.json` convenience method, it will return a subclass of `HTTPResponse` called :class:`sanic.response.types.JSONResponse`. This object will
have several convenient methods available to modify common JSON body.

```python
从沙尼导入 json

resp = json(...)
```

- `resp.set_body(<raw_body>)` - 设定JSON对象的正文到传递的值
- `resp.append(<value>)` - 追加一个 `list.append` 这个物体的值(仅当root JSON 是一个数组时才起作用)
- `resp.extend(<value>)` - 将一个值扩展到物体像`list.extend` (仅当root JSON 是一个数组时才能工作)
- `resp.update(<value>)` - 更新像`dict.update` 这样的物体(仅当root JSON是一个对象时才工作)
- `resp.pop()` - 弹出一个 `list.pop` 或 `dict.pop` 等值(仅当root JSON 是数组或对象时才起作用)

.. 警告：:

```
原生的 Python 对象作为`raw_body` 存储在 `JSONResponse` 对象上。 虽然用新值覆盖此值是安全的，但是你应该**不应该**试图变换它。 你应该使用上面列出的方法。
```

```python
resp = json({"foo": "bar"})

# This is OKAY
resp.raw_body = {"foo": "bar", "something": "else"}

# This is better
resp.set_body({"foo": "bar", "something": "else"})

# This is also works well
resp.update({"something": "else"})

# This is NOT OKAY
resp.raw_body.update({"something": "else"})
```

```python
# 或者，甚至将其视为列表
resp = json(["foo", "bar"])

# 这是非常重要的
resp. aw_body = ["foo", "bar", "something", "else"]

# 这是更好的
resp. xtend(["something", "else"])

# 这也很适合
resp.append("something")
resp.append("else")

# 这不是很重要的
resp.raw_body.append("something")
```

_添加于 v22.9_
