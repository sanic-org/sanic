# 中间件

听众允许您在工作流程的生命周期中附加功能， 中间件允许您在HTTP流的生命周期中附加功能。

```python
@app.on_request
async def example(request):
	print("I execute before the handler.")
```

您可以执行 _befor_ 的处理程序或者执行 _after _。

```python
@app.on_response
async def example(request, response):
	print("I execute after the handler.")
```

.. mermaid:

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

## 附加中间件

.. 列:

```
现在也许应该看起来很熟悉。 您需要做的只是当您想要执行中间件时声明：在 "request" 或 "response" 上。
```

.. 列:

````
```python
async def extract_user(request):
    request.ctx.user = request_user_from_request(request)

app.register_middleware(extract_user, "request")
```
````

.. 列:

```
同样，“Sanic”应用实例也有一个方便装饰器。
```

.. 列:

````
```python
@app.midleware("request")
async def extract_user(request):
    request.ctx.user = request_user_from_request(request)
```
````

.. 列:

```
响应中间件同时收到“request”和“response”两个参数。
```

.. 列:

````
```python
@app.midleware('response')
async def prevent_xss(request, response):
    response.headers["x-xss-protection"] = "1; mode=block"
```
````

.. 列:

```
您可以进一步缩短装饰。如果您拥有一个自动完成的 IDE，这将是很有帮助的。

这是首选用法，这是我们今后使用的方法。
```

.. 列:

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

## 修改

中间件可以修改它被指定的请求或响应参数，只要它不返回它。

.. 列:

```
#### 执行顺序

1. 请求中间行：`add_key`
2. 路由处理：`index`
3. 响应中间行：`prevent_xss`
4. 响应中间行程：`cust_banner`
```

.. 列:

````
```python
@app。 n_request
async def add_key(请求):
    # 任意数据可能存储在请求的上下文中:
    请求。 tx.foo = "bar"

@app.on_response
async def custom_banner(request, response):
    response. eaders["Server"] = "Fake-Server"

@app.on_response
async def prevent_xss(request, response):
    response. eaders["x-xss-protection"] = "1; mode=block"

@app.get("/")
async def index(request):
    return text(request.ctx.foo)

```
````

.. 列:

```
您可以修改 `request.match_info` 。例如，一个有用的功能可以用于中间件将`a-slug` 转换为 `a_slug` 。
```

.. 列:

````
```python
@app.on_request
def convert_slug_to_underly(request:
    request.match_info["slug"] = request.match_info["slug"].replace("-"_")

@app. et("/<slug:slug>")
async def 处理器(请求) slug):
    return text(slug)
```
```
$ curl localhost:99999/foo-bar-baz
foo_bar_baz
```
````

## 早期响应

.. 列:

```
If middleware returns a `HTTPResponse` object, the request will stop processing and the response will be returned. If this occurs to a request before the route handler is reached, the handler will **not** be called. Returning a response will also prevent any further middleware from running.

```

.. tip::

```
您可以返回 `None` 值来停止执行中间件处理程序，以允许请求正常处理。 这可能有助于早日返回以避免处理中间件处理器内的请求。
```

.. 列:

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

## 执行顺序

请求中间件在已声明的订单中执行。 响应中间件在 **逆序** 中执行。

鉴于以下情况，我们应该在控制台上看到这一点。

.. 列:

````
```python
@app.on_request
async def middleware_1(request):
    print("middleware_1")

@appp. n_request
async def middleware_2(request):
    print("middleware_2")

@app. n_response
async def middleware_3(request, response):
    print("middleware_3")

@app. n_response
async def middleware_4(request, response):
    print("middleware_4")

@app. et("/handler")
async def handler(request):
    print("~handler ~")
    return text("完成")
```
````

.. 列:

````
```bash
middleware_1
middleware_2
~
middleware_4
middleware_3
[INFO][127.0.0.1:4478]: GET http://localhost:8000/handler 200 5
```
````

### 中间件优先级

.. 列:

```
您可以通过赋予它更高的优先级来修改中间件的执行顺序。这发生在中间件定义内。 值越高，相对于其他中间件执行的越早。中间件的默认优先级是 `0'。
```

.. 列:

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

_添加于 v22.9_
