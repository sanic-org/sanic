---
title: Sanic Extensions - HTTP Methods
---

# HTTP Methods

## Auto-endpoints

The default behavior is to automatically generate `HEAD` endpoints for all `GET` routes, and `OPTIONS` endpoints for all
routes. Additionally, there is the option to automatically generate `TRACE` endpoints. However, these are not enabled by
default.

### HEAD

.. column::

    - **Configuration**: `AUTO_HEAD` (default `True`)
    - **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD)

    A `HEAD` request provides the headers and an otherwise identical response to what a `GET` request would provide.
    However, it does not actually return the body.

.. column::

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

### OPTIONS

.. column::

    - **Configuration**: `AUTO_OPTIONS` (default `True`)
    - **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS)

    `OPTIONS` requests provide the recipient with details about how the client is allowed to communicate with a given
    endpoint.

.. column::

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

.. tip::
    
    Even though Sanic Extensions will setup these routes for you automatically, if you decide to manually create an `@app.options` route, it will *not* be overridden.

### TRACE

.. column::

    - **Configuration**: `AUTO_TRACE` (default `False`)
    - **MDN**: [Read more](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/TRACE)

    By default, `TRACE` endpoints will **not** be automatically created. However, Sanic Extensions **will allow** you to
    create them if you wanted. This is something that is not allowed in vanilla Sanic.

.. column::

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

.. tip:: 

    Setting up `AUTO_TRACE` can be super helpful, especially when your application is deployed behind a proxy since it will help you determine how the proxy is behaving.

## Additional method support

Vanilla Sanic allows you to build endpoints with the following HTTP methods:

- [GET](/en/guide/basics/routing.html#get)
- [POST](/en/guide/basics/routing.html#post)
- [PUT](/en/guide/basics/routing.html#put)
- [HEAD](/en/guide/basics/routing.html#head)
- [OPTIONS](/en/guide/basics/routing.html#options)
- [PATCH](/en/guide/basics/routing.html#patch)
- [DELETE](/en/guide/basics/routing.html#delete)

See [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) for more.

.. column::

    There are, however, two more "standard" HTTP methods: `TRACE` and `CONNECT`. Sanic Extensions will allow you to build
    endpoints using these methods, which would otherwise not be allowed.

    It is worth pointing out that this will *NOT* enable convenience methods: `@app.trace` or `@app.connect`. You need to
    use `@app.route` as shown in the example here.

.. column::

    ```python
    @app.route("/", methods=["trace", "connect"])
    async def handler(_):
        return empty()
    ```

