# Middleware

Whereas listeners allow you to attach functionality to the lifecycle of a worker process, middleware allows you to attach functionality to the lifecycle of an HTTP stream.

```python
@app.on_request
async def example(request):
	print("I execute before the handler.")
```

You can execute middleware either _before_ the handler is executed, or _after_.

```python
@app.on_response
async def example(request, response):
	print("I execute after the handler.")
```

.. mermaid::

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

## Attaching middleware

.. column::

    This should probably look familiar by now. All you need to do is declare when you would like the middleware to execute: on the `request` or on the `response`.

.. column::

    ```python
    async def extract_user(request):
        request.ctx.user = await extract_user_from_request(request)

    app.register_middleware(extract_user, "request")
    ```

.. column::

    Again, the `Sanic` app instance also has a convenience decorator.

.. column::

    ```python
    @app.middleware("request")
    async def extract_user(request):
        request.ctx.user = await extract_user_from_request(request)
    ```

.. column::

    Response middleware receives both the `request` and `response` arguments.

.. column::

    ```python
    @app.middleware('response')
    async def prevent_xss(request, response):
        response.headers["x-xss-protection"] = "1; mode=block"
    ```

.. column::

    You can shorten the decorator even further. This is helpful if you have an IDE with autocomplete.

    This is the preferred usage, and is what we will use going forward.

.. column::

    ```python
    @app.on_request
    async def extract_user(request):
        ...

    @app.on_response
    async def prevent_xss(request, response):
        ...
    ```

## Modification

Middleware can modify the request or response parameter it is given, _as long as it does not return it_.


.. column::

    #### Order of execution

    1. Request middleware: `add_key`
    2. Route handler: `index`
    3. Response middleware: `prevent_xss`
    4. Response middleware: `custom_banner`

.. column::

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

.. column::

    You can modify the `request.match_info`. A useful feature that could be used, for example, in middleware to convert `a-slug` to `a_slug`.

.. column::

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

## Responding early

.. column::

    If middleware returns a `HTTPResponse` object, the request will stop processing and the response will be returned. If this occurs to a request before the route handler is reached, the handler will **not** be called. Returning a response will also prevent any further middleware from running.

    

.. tip:: 

    You can return a `None` value to stop the execution of the middleware handler to allow the request to process as normal. This can be useful when using early return to avoid processing requests inside of that middleware handler.

.. column::

    ```python
    @app.on_request
    async def halt_request(request):
        return text("I halted the request")

    @app.on_response
    async def halt_response(request, response):
        return text("I halted the response")
    ```

## Order of execution

Request middleware is executed in the order declared. Response middleware is executed in **reverse order**.

Given the following setup, we should expect to see this in the console.

.. column::

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

.. column::

    ```bash
    middleware_1
    middleware_2
    ~ handler ~
    middleware_4
    middleware_3
    [INFO][127.0.0.1:44788]: GET http://localhost:8000/handler  200 5
    ```

### Middleware priority

.. column::

    You can modify the order of execution of middleware by assigning it a higher priority. This happens inside of the middleware definition. The higher the value, the earlier it will execute relative to other middleware. The default priority for middleware is `0`.

.. column::

    ```python
    @app.on_request
    async def low_priority(request):
        ...

    @app.on_request(priority=99)
    async def high_priority(request):
        ...
    ```

*Added in v22.9*
