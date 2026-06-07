---
title: Sanic 扩展 - HTTP 方法
---

# HTTP 方法

## 自动终点

默认行为是自动生成所有的 `GET` 路径的 `HEAD` 端点，以及所有
路径的 `OPTIONS` 端点。 此外，还有自动生成 `TRACE` 端点的选项。 然而，
默认情况下没有启用这些功能。

### 黑色

.. 列:

```
- **配置**: `AUTO_HEAD` (默认 `True`)
- **MDN**: [阅读更多](https://developer.mozilla). rg/en-US/docs/Web/HTTPMethods/HEAD

A `HEAD` 请求提供了标题和对一个 `GET` 请求提供的相同的响应。
然而，实际上并没有归还尸体。
```

.. 列:

````
```python
@app.get("/")
async def hello_world(request):
    return text("Hello, world"
``

鉴于上述路由定义，Sanic Extensions 将能使`HEAD` 反应，如上所示。

```
$ curl localhost:8000 --head
HTTP/1。 200 OK
access-allow-origin: *
content-length: 13
connection: keep-alive
content-type: text/plain; charset=utf-8
```
````

### 选项

.. 列:

```
- **配置**: `AUTO_OPTIONS` (默认 `True`)
- **MDN**: [阅读更多] (https://developer.mozilla). rg/en-US/docs/Web/HTTP/Methods/OPTIONS

"OPTIONS" 请求向收件人详细介绍了如何允许客户端与指定
端口进行通信。
```

.. 列:

````
```python
@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```

Given the above route definition, Sanic Extensions will enable `OPTIONS` responses, as seen here.

It is important to note that we also see `access-control-allow-origins` in this example. This is because
the [CORS protection](cors.md) is enabled by default.

```
$ curl localhost:8000 -X OPTIONS -i
HTTP/1.1 204 No Content
allow: GET,HEAD,OPTIONS
access-control-allow-origin: *
connection: keep-alive
```
````

.. tip::

```
即使Sanic 扩展会自动为您设置这些路径，如果您决定手动创建一个 `@app.options` 路径，它将*不*被覆盖。
```

### 追踪器

.. 列:

```
- **Configuration**: `AUTO_TRACE` (default `False`)
- **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/TRACE)

By default, `TRACE` endpoints will **not** be automatically created. However, Sanic Extensions **will allow** you to
create them if you wanted. This is something that is not allowed in vanilla Sanic.
```

.. 列:

````
```python
@app.route("/", methods=["追踪"])
async def 处理器(请求):

```

要启用这些端点的自动创建，您必须先启用它们才能扩展 Sanic。

```python
from sanic_ext import Extend, Config

app. xtend(config=Config(http_auto_trace=True))
```

现在，假定您有一些端点设置， 你可以在这里追踪它们：

```
$ curl localhost:8000 -X TRACE
TRACE / HTTP/1。
主机：localhost:9999
User-Agent：curl/7.76.1
接受：*/*
```
````

.. tip::

```
设置 `AUTO_TRACE` 可以提供超级帮助， 尤其是当您的应用程序被部署在代理后面，因为它将帮助您确定代理人的行为方式。
```

## 额外方法支持

Vanilla Sanic允许您使用 HTTP 方法构建终点：

- [GET](/en/guide/basics/routing.html#get)
- [POST](/en/guide/basics/routing.html#post)
- [PUT](/en/guide/basics/routing.html#put)
- [HEAD](/en/guide/basics/routing.html#head)
- [OPTIONS](/en/guide/basics/routing.html#选项)
- [PATCH](/en/guide/basics/routing.html#patch)
- [DELETE](/en/guide/basics/routing.html#delete)

详见[MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)

.. 列:

```
然而，还有两种"标准"HTTP方法：`TRACE`和`CONNECT`。 Sanic 扩展将允许您使用这些方法构建
端点，否则这些方法是不允许的。

值得指出的是，这将*无* 启用方便方法：`@app。 竞技`或`@app.connect`。您需要
使用示例`@app.route`。
```

.. 列:

````
```python
@app.route("/", methods=["追踪", "connect"])
async def handler(_):
    return empty()
```
````

