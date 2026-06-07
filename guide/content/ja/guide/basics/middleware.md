# ミドルウェア

一方、リスナーはワーカープロセスのライフサイクルに機能を付加することができます。 ミドルウェアを使用すると、HTTPストリームのライフサイクルに機能を追加できます。

```python
@app.on_request
async def example(request):
	print("I execute before the handler")
```

ミドルウェアは _before_ ハンドラが実行されるか、_after_ のどちらかで実行できます。

```python
@app.on_response
async def example(request, response):
	print("I execute after the handler")
```

.. mermaid::

```
sequenceDiagram
autonumber
participant Worker
participant Middleware
participant MiddlewareHandler
participant RouteHandler
Note over Worker: Incoming HTTP request
loop
    Worker->>Middleware: @app.on_request
    Middleware->>MiddlewareHandler: Invoke middleware handler
    MiddlewareHandler-->>Worker: Return response (optional)
end
rect rgba(255, 13, 104, .1)
Worker->>RouteHandler: Invoke route handler
RouteHandler->>Worker: Return response
end
loop
    Worker->>Middleware: @app.on_response
    Middleware->>MiddlewareHandler: Invoke middleware handler
    MiddlewareHandler-->>Worker: Return response (optional)
end
Note over Worker: Deliver response
```

## ミドルウェアをアタッチ中

.. 列::

```
これはおそらく今ごろはよく見覚えがあるはずです。 ミドルウェアに`request`または`response`を実行させたいときに宣言するだけです。
```

.. 列::

````
```python
async def extract_user(request):
    request.ctx.user = await extract_user_from_request(request)

app.register_middleware(extract_user, "request")
```
````

.. 列::

```
繰り返しになりますが、`Sanic`アプリインスタンスには利便性デコレータもあります。
```

.. 列::

````
```python
@app.middleware("request")
async def extract_user(request):
    request.ctx.user = await extract_user_from_request(request)
```
````

.. 列::

```
Response middleware は `request` と `response` の両方の引数を受け取ります。
```

.. 列::

````
```python
@app.middleware('response')
async def prevent_xss(request, response):
    response.headers["x-xss-protection"] = "1; mode=block"
```
````

.. 列::

```
デコレータをさらに短くすることができます。オートコンプリート付きの IDE がある場合に便利です。

これが好ましい用途であり、今後使用するものです。
```

.. 列::

````
```python
@app.on_request
async def extract_user(request):
    ...

@app.on_response
async def prevent_xss(request, response):
    ...
```
````

## Modification

ミドルウェアは与えられたリクエストやレスポンスのパラメータを変更することができます。

.. 列::

```
#### 実行順序

1. リクエストミドルウェア: `add_key`
2. ルートハンドラ: `index`
3. レスポンスミドルウェア: `prevent_xss`
4. レスポンスミドルウェア: `custom_banner`
```

.. 列::

````
```python
@app.on_request
async def add_key(request):
    # Arbitrary data may be stored in request context:
    request.ctx.foo = "bar"

@app.on_response
async def custom_banner(request, response):
    response.headers["Server"] = "Fake-Server"

@app.on_response
async def prevent_xss(request, response):
    response.headers["x-xss-protection"] = "1; mode=block"

@app.get("/")
async def index(request):
    return text(request.ctx.foo)

```
````

.. 列::

```
`request.match_info`を変更することができます。例えばミドルウェアで`a-slug`をa_slug`に変換するのに役立つ機能です。
```

.. 列::

````
```python
@app.on_request
def convert_slug_to_underscore(request: Request):
    request.match_info["slug"] = request.match_info["slug"].replace("-", "_")

@app.get("/<slug:slug>")
async def handler(request, slug):
    return text(slug)
```
```
$ curl localhost:9999/foo-bar-baz
foo_bar_baz
```
````

## 早期対応

.. 列::

```
middleware が `HTTPResponse` オブジェクトを返す場合、リクエストは処理を停止し、レスポンスが返されます。 ルートハンドラに到達する前にリクエストにこれが発生した場合、ハンドラは **呼び出されません** 。 応答を返すと、さらにミドルウェアが実行されなくなります。

```

.. tip::

```
`None` を返すと、ミドルウェアハンドラの実行が停止し、リクエストが通常通り処理できるようになります。 これは、ミドルウェアハンドラ内のリクエスト処理を避けるために早期の戻り値を使用する場合に便利です。
```

.. 列::

````
```python
@app.on_request
async def halt_request(request):
    return text("I halted the request")

@app.on_response
async def halt_response(request, response):
    return text("I halted the response")
```
````

## 実行の順序

リクエストミドルウェアは宣言された順序で実行されます。 レスポンスミドルウェアは**逆順**で実行されます。

以下の設定では、コンソールでこれを確認する必要があります。

.. 列::

````
```python
@app.on_request
async def middleware_1(request):
    print("middleware_1")

@app.on_request
async def middleware_2(request):
    print("middleware_2")

@app.on_response
async def middleware_3(request, response):
    print("middleware_3")

@app.on_response
async def middleware_4(request, response):
    print("middleware_4")

@app.get("/handler")
async def handler(request):
    print("~ handler ~")
    return text("Done.")
```
````

.. 列::

````
```bash
middleware_1
middleware_2
~ handler ~
middleware_4
middleware_3
[INFO][127.0.0.1:44788]: GET http://localhost:8000/handler 200 5
```
````

### ミドルウェアの優先度

.. 列::

```
ミドルウェアの実行順序は、より高い優先度を割り当てることで変更できます。ミドルウェア定義の内部で発生します。 値が高いほど、他のミドルウェアから相対的に実行されます。ミドルウェアのデフォルトの優先度は `0` です。
```

.. 列::

````
```python
@app.on_request
async def low_priority(request):
    ...

@app.on_request(priority=99)
async def high_priority(request):
    ...
```
````

_v22.9_に追加されました
