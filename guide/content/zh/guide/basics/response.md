# 响应(Response)

所有 [handlers](./handlers.md) _通常_返回一个响应对象， [middleware](./midd) 可以选择是否返回一个响应对象。

解释一下

- 除非处理器是一个流式响应，即发送字节到客户端模式的流式路由，否则返回值必须是:class:`sanic.response.HTTPResponse`类的实例（要了解更多关于这一例外情况，请参[阅流式响应](../advanced/streaming.md#response-streaming)） 否则，您需要返回一个响应。
- 如果中间件确实返回了一个响应对象，则会使用该响应对象代替处理器原本的行为（更多细节请参阅 [中间件](./middleware.md) 部分）。

一个最基本的处理器可能如下所示。 使用 :class:`sanic.response.HTTPResponse` 类对象，您可以设置要返回给客户端的状态码、主体内容以及头部信息。

```python
from sanic import HTTPResponse, Sanic

app = Sanic("TestApp")

@app.route("")
def handler(_):
    return HTTPResponse()
```

然而，通常使用下文讨论的一些便捷方法更为简单。

## 响应方式(Methods)

生成响应对象最简便的方式是使用以下便捷函数。

### Text（文本）

.. column::

```
**默认Content-Type**: `text/plain; charset=utf-8`  
**描述**: 返回纯文本
```

.. column::

````
```python
from sanic import text

@app.route("/")
async def handler(request):
    return text("Hi 😎")
```
````

### HTML（HTML）

.. column::

```
**默认Content-Type**: `text/html; charset=utf-8`  
**描述**: 返回一个 HTML 文档
```

.. column::

````
```python
from sanic import html

@app.route("/")
async def handler(request):
    return html('<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><div>Hi 😎</div>')
```
````

### JSON（JSON）

.. column::

```
**默认 Content-Type**: `application/json`  
**描述**: 返回 JSON 数据
```

.. column::

````
```python
from sanic import json

@app.route("/")
async def handler(request):
    return json({"foo": "bar"})
```
````

默认情况下，Sanic 使用 [`ujson`](https://github.com/ultrajson/ultrajson) 作为其首选的 JSON 解析器。 如果`ujson`模块没有被安装，程序将会退回到使用标准库中的`json`模块。

想要改变默认的json解析器，非常简单

```python
from sanic import json
from orjson import dumps

json({"foo": "bar"}, dumps=dumps)
```

您还可以在初始化时全局声明在整个应用程序中使用哪个json解析器

```python
from orjson import dumps

app = Sanic(..., dumps=dumps)
```

### File（文件）

.. column::

```
**默认Content-Type**：N/A 
**描述**：返回一个文件
```

.. column::

````
```python
from sanic import file

@app.route("/")
async def handler(request):
    return await file("/path/to/whatever.png")
```
````

Sanic 将会检查该文件，并尝试猜测其 MIME 类型，然后为内容类型使用合适的值。 如果您愿意，也可以明确指定：

```python
file("/path/to/whatever.png", mime_type="image/png")
```

您也可以选择覆盖文件名称：

```python
file("/path/to/whatever.png", filename="super-awesome-incredible.png")
```

### File Streaming（文件流）

.. column::

```
**默认Content-Type**: N/A  
**描述**: 流一个文件到一个客户端, 当像视频一样流出大文件时有用。
```

.. column::

````
```python
from sanic.response import file_stream

@app.route("/")
async def handler(request):
    return await file_stream("/path/to/whatever.mp4")
```
````

与 `file()` 方法类似，`file_stream()` 也会尝试确定文件的 MIME 类型。

### Raw（原始数据）

.. column::

```
**默认Content-Type**: `application/octet-stream`  
**描述**: 发送原始字节而不对正文进行编码
```

.. column::

````
```python
from sanic import raw

@app.route("/")
async def handler(request):
    return raw(b"raw bytes")
```
````

### Redirect（重定向）

.. column::

```
**默认Content-Type**: `text/html; charset=utf-8`  
**描述**: 发送一个 `302` 响应来将客户重定向到另一个URL
```

.. column::

````
```python
from sanic import redirect

@app.route("/")
async def handler(request):
    return redirect("/login")
```
````

### Empty（空返回）

.. column::

```
**默认 Content-Type**: N/A 
**描述**: 对于按照 [RFC 2616](https://tools.ietf.org/search/rfc2616#section-7.2.1) 规定响应空消息
```

.. column::

````
```python
from sanic import empty

@app.route("/")
async def handler(request):
    return empty()
```

默认的状态码是 `204`
````

## Default Status（默认状态码）

响应默认的 HTTP 状态代码是 `200'。 如果您需要更改它，它可以通过在响应函数中传入指定的`status\`。

```python
@app.post("/")
async def create_new(request):
    new_thing = await do_create(request)
    return json({"created": True, "id": new_thing.thing_id}, status=201)
```

## Returning JSON data（返回json数据）

从 v22.12 版本开始，当您使用 `sanic.json` 的便捷方法时，它将返回一个名为 :class:`sanic.response.types.JSONResponse` 的 `HTTPResponse` 子类。 此对象将提供多个便捷方法来修改常见的 JSON 正文。

```python
from sanic import json

resp = json(...)
```

- `resp.set_body(<raw_body>)` - 将 JSON 对象的正文设置为传递的值
- `resp.append(<value>)` - 向正文追加一个值，如同 `list.append`（仅当根 JSON 是数组时有效）
- `resp.extend(<value>)` -  将一个值扩展到正文中，如同 `list.extend`（仅当根 JSON 是数组时有效）
- `resp.update(<value>)` -使用类似 `dict.update` 的方式更新正文（仅当根 JSON 是对象时有效）
- `resp.pop()` - 移除并返回一个值，如同 `list.pop` 或 `dict.pop`（仅当根 JSON 是数组或对象时有效）

.. warning:: 警告⚠

```
原始 Python 对象作为 `raw_body` 存储在 `JSONResponse` 对象上。虽然您可以安全地用新值覆盖这个值，但您应该**不要**尝试对其进行修改。相反，您应该使用上面列出的方法进行操作。
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
# Or, even treat it like a list
resp = json(["foo", "bar"])

# This is OKAY
resp.raw_body = ["foo", "bar", "something", "else"]

# This is better
resp.extend(["something", "else"])

# This is also works well
resp.append("something")
resp.append("else")

# This is NOT OKAY
resp.raw_body.append("something")
```

_添加于 v22.9_
