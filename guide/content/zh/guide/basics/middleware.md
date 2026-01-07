# 中间件(Middleware)

监听器（listeners ）允许您将功能附加到工作进程的生命周期中，中间件（middleware ）则允许您将功能附加到HTTP流的生命周期中。

```python
@app.on_request
async def example(request):
	print("I execute before the handler.")
```

您可以选择在处理器执行前或执行后执行中间件。

```python
@app.on_response
async def example(request, response):
	print("I execute after the handler.")
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

## 注册中间件（Attaching middleware）

.. column::

```
到现在为止，这个概念应该已经很熟悉了。您需要做的只是声明何时希望中间件执行：是在请求（`request`）阶段还是响应（`response`）阶段。
```

.. column::

````
```python
async def extract_user(request):
    request.ctx.user = await extract_user_from_request(request)

app.register_middleware(extract_user, "request")
```
````

.. column::

```
同样，`Sanic` 应用实例也提供了一个便捷的装饰器。
```

.. column::

````
```python
@app.middleware("request")
async def extract_user(request):
    request.ctx.user = await extract_user_from_request(request)
```
````

.. column::

```
响应中间件同时接收 `request` 和 `response` 参数。
```

.. column::

````
```python
@app.middleware('response')
async def prevent_xss(request, response):
    response.headers["x-xss-protection"] = "1; mode=block"
```
````

.. column::

```
您甚至可以进一步简化装饰器。如果您使用的IDE支持自动补全，这将非常有帮助。

这是首选用法，也是我们后续将会采用的方式。
```

.. column::

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

## 修改（Modification）

只要中间件不返回请求或响应参数，它可以修改接收到的请求或响应参数。

.. column::

```
#### 执行顺序

1. Request middleware: `add_key`
2. Route handler: `index`
3. Response middleware: `prevent_xss`
4. Response middleware: `custom_banner`
```

.. column::

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

.. column::

```
您可以修改 `request.match_info`。例如，在中间件中，可以利用这一有用特性将 `a-slug` 转换为 `a_slug`。
```

.. column::

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

## 提前响应(Resonding early)

.. column::

```
如果中间件返回一个 `HTTPResponse` 对象，则请求处理将停止，并返回该响应。如果在到达路由处理器之前发生这种情况，则不会调用处理器。返回响应也将阻止任何其他中间件继续执行。
```

.. tip:: 提示

```
您可以在中间件处理器中返回 `None` 值来停止执行，以允许请求正常进行处理。当使用早期返回机制避免在此中间件处理器内部处理请求时，这一做法十分有用。
```

.. column::

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

## 执行顺序(Order of execution)

请求中间件按照声明的顺序执行。 响应中间件按**相反顺序**执行。

按照下面的代码，我们应该期望在控制台看到这样的输出结果。

.. column::

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

.. column::

````
```bash
middleware_1
middleware_2
~ handler ~
middleware_4
middleware_3
[INFO][127.0.0.1:44788]: GET http://localhost:8000/handler  200 5
```
````

### 中间件优先级（Middleware priority）

.. column::

```
您可以通过分配更高的优先级来修改中间件执行的顺序。这一操作在定义中间件时进行。优先级值越高，相对于其他中间件，其执行就越早。默认情况下，中间件的优先级为 `0`。
```

.. column::

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

\*添加于 v22.9 \*
