---
title: サニックエクステンション - HTTPメソッド
---

# HTTPメソッド

## 自動エンドポイント

デフォルトの動作は、すべての `GET` ルートの `HEAD` エンドポイントと、すべての
ルートの `OPTIONS` エンドポイントを自動的に生成することです。 さらに、 `TRACE` エンドポイントを自動生成するオプションもあります。 ただし、これらは
デフォルトでは有効になっていません。

### 頭

.. 列::

```
- **Configuration**: `AUTO_HEAD` (default `True`)
- **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD)

A `HEAD` request provides the headers and an otherwise identical response to what a `GET` request would provide.
However, it does not actually return the body.
```

.. 列::

````
```python
@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```

Given the above route definition, Sanic Extensions will enable `HEAD` responses, as seen here.

```
$ curl localhost:8000 --head
HTTP/1.1 200 OK
access-control-allow-origin: *
content-length: 13
connection: keep-alive
content-type: text/plain; charset=utf-8
```
````

### オプション

.. 列::

```
- **Configuration**: `AUTO_OPTIONS` (default `True`)
- **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS)

`OPTIONS` requests provide the recipient with details about how the client is allowed to communicate with a given
endpoint.
```

.. 列::

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
Sanic Extensionsは自動的にこれらのルートを設定しますが、`@app.options`ルートを手動で作成する場合、上書きされることはありません。
```

### トレースする

.. 列::

```
- **Configuration**: `AUTO_TRACE` (default `False`)
- **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/TRACE)

By default, `TRACE` endpoints will **not** be automatically created. However, Sanic Extensions **will allow** you to
create them if you wanted. This is something that is not allowed in vanilla Sanic.
```

.. 列::

````
```python
@app.route("/", methods=["trace"])
async def handler(request):
    ...
```

To enable auto-creation of these endpoints, you must first enable them when extending Sanic.

```python
from sanic_ext import Extend, Config

app.extend(config=Config(http_auto_trace=True))
```

Now, assuming you have some endpoints setup, you can trace them as shown here:

```
$ curl localhost:8000 -X TRACE
TRACE / HTTP/1.1
Host: localhost:9999
User-Agent: curl/7.76.1
Accept: */*
```
````

.. tip::

```
`AUTO_TRACE` のセットアップはとても役に立ちます。 アプリケーションがプロキシの背後に展開されている場合は特にプロキシがどのように動作するかを判断するのに役立ちます
```

## 追加メソッドのサポート

Vanilla Sanicは以下のHTTPメソッドでエンドポイントを構築できます。

- [GET](/ja/guide/basics/routing.html#get)
- [POST](/ja/guide/basics/routing.html#post)
- [PUT](/ja/guide/basics/routing.html#put)
- [HEAD](/ja/guide/basics/routing.html#head)
- [OPTIONS](/ja/guide/basics/routing.html#options)
- [PATCH](/ja/guide/basics/routing.html#patch)
- [DELETE](/ja/guide/basics/routing.html#delete)

詳細は [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) を参照してください。

.. 列::

```
There are, however, two more "standard" HTTP methods: `TRACE` and `CONNECT`. Sanic Extensions will allow you to build
endpoints using these methods, which would otherwise not be allowed.

It is worth pointing out that this will *NOT* enable convenience methods: `@app.trace` or `@app.connect`. You need to
use `@app.route` as shown in the example here.
```

.. 列::

````
```python
@app.route("/", methods=["trace", "connect"])
async def handler(_):
    return empty()
```
````
