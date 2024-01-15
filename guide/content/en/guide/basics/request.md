# Request

See API docs: [sanic.request](/api/sanic.request)

The :class:`sanic.request.Request` instance contains **a lot** of helpful information available on its parameters. Refer to the [API documentation](https://sanic.readthedocs.io/) for full details.

As we saw in the section on [handlers](./handlers), the first argument in a route handler is usually the :class:`sanic.request.Request` object. Because Sanic is an async framework, the handler will run inside of a [`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) and will be scheduled by the event loop. This means that the handler will be executed in an isolated context and the request object will be unique to that handler's task.

.. column::

    By convention, the argument is named `request`, but you can name it whatever you want. The name of the argument is not important. Both of the following handlers are valid.
    
.. column::

    ```python
    @app.get("/foo")
    async def typical_use_case(request):
        return text("I said foo!")
    ```

    ```python
    @app.get("/foo")
    async def atypical_use_case(req):
        return text("I said foo!")
    ```

.. column::

    Annotating a request object is super simple.
        
.. column::

    ```python
    from sanic.request import Request
    from sanic.response import text

    @app.get("/typed")
    async def typed_handler(request: Request):
        return text("Done.")
    ```

.. tip::
    
    For your convenience, assuming you are using a modern IDE, you should leverage type annotations to help with code completion and documentation. This is especially helpful when using the `request` object as it has **MANY** properties and methods.
        
    To see the full list of available properties and methods, refer to the [API documentation](/api/sanic.request).

## Body

The `Request` object allows you to access the content of the request body in a few different ways.

### JSON

.. column::

    **Parameter**: `request.json`  
    **Description**: The parsed JSON object

.. column::

    ```bash
    $ curl localhost:8000 -d '{"foo": "bar"}'
    ```

    ```python
    >>> print(request.json)
    {'foo': 'bar'}
    ```

### Raw

.. column::

    **Parameter**: `request.body`  
    **Description**: The raw bytes from the request body

.. column::

    ```bash
    $ curl localhost:8000 -d '{"foo": "bar"}'
    ```

    ```python
    >>> print(request.body)
    b'{"foo": "bar"}'
    ```

### Form

.. column::

    **Parameter**: `request.form`  
    **Description**: The form data

    .. tip:: FYI

        The `request.form` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

        Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.

.. column::

    ```bash
    $ curl localhost:8000 -d 'foo=bar'
    ```

    ```python
    >>> print(request.body)
    b'foo=bar'

    >>> print(request.form)
    {'foo': ['bar']}

    >>> print(request.form.get("foo"))
    bar

    >>> print(request.form.getlist("foo"))
    ['bar']
    ```

### Uploaded

.. column::

    **Parameter**: `request.files`  
    **Description**: The files uploaded to the server

    .. tip:: FYI

        The `request.files` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

        Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.

.. column::

    ```bash
    $ curl -F 'my_file=@/path/to/TEST' http://localhost:8000
    ```

    ```python
    >>> print(request.body)
    b'--------------------------cb566ad845ad02d3\r\nContent-Disposition: form-data; name="my_file"; filename="TEST"\r\nContent-Type: application/octet-stream\r\n\r\nhello\n\r\n--------------------------cb566ad845ad02d3--\r\n'

    >>> print(request.files)
    {'my_file': [File(type='application/octet-stream', body=b'hello\n', name='TEST')]}

    >>> print(request.files.get("my_file"))
    File(type='application/octet-stream', body=b'hello\n', name='TEST')

    >>> print(request.files.getlist("my_file"))
    [File(type='application/octet-stream', body=b'hello\n', name='TEST')]
    ```

## Context

### Request context

The `request.ctx` object is your playground to store whatever information you need to about the request. This lives only for the duration of the request and is unique to the request.

This can be constrasted with the `app.ctx` object which is shared across all requests. Be careful not to confuse them! 

The `request.ctx` object by default is a `SimpleNamespace` object allowing you to set arbitrary attributes on it. Sanic will not use this object for anything, so you are free to use it however you want without worrying about name clashes.

```python

### Typical use case

This is often used to store items like authenticated user details. We will get more into [middleware](./middleware.md) later, but here is a simple example.

```python
@app.on_request
async def run_before_handler(request):
    request.ctx.user = await fetch_user_by_token(request.token)

@app.route('/hi')
async def hi_my_name_is(request):
    if not request.ctx.user:
        return text("Hmm... I don't know you)
    return text(f"Hi, my name is {request.ctx.user.name}")
```

As you can see, the `request.ctx` object is a great place to store information that you need to access in multiple handlers making your code more DRY and easier to maintain. But, as we will learn in the [middleware section](./middleware.md), you can also use it to store information from one middleware that will be used in another.

### Connection context

.. column::

    Often times your API will need to serve multiple concurrent (or consecutive) requests to the same client. This happens, for example, very often with progressive web apps that need to query multiple endpoints to get data.

    The HTTP protocol calls for an easing of overhead time caused by the connection with the use of [keep alive headers](../deployment/configuration.md#keep-alive-timeout).

    When multiple requests share a single connection, Sanic provides a context object to allow those requests to share state.

.. column::

    ```python
    @app.on_request
    async def increment_foo(request):
        if not hasattr(request.conn_info.ctx, "foo"):
            request.conn_info.ctx.foo = 0
        request.conn_info.ctx.foo += 1

    @app.get("/")
    async def count_foo(request):
        return text(f"request.conn_info.ctx.foo={request.conn_info.ctx.foo}")
    ```

    ```bash
    $ curl localhost:8000 localhost:8000 localhost:8000
    request.conn_info.ctx.foo=1
    request.conn_info.ctx.foo=2
    request.conn_info.ctx.foo=3
    ```

.. warning::

    While this looks like a convenient place to store information between requests by a single HTTP connection, do not assume that all requests on a single connection came from a single end user. This is because HTTP proxies and load balancers can multiplex multiple connections into a single connection to your server.
    
    **DO NOT** use this to store information about a single user. Use the `request.ctx` object for that.

### Custom Request Objects

As dicussed in [application customization](./app.md#custom-requests), you can create a subclass of :class:`sanic.request.Request` to add additional functionality to the request object. This is useful for adding additional attributes or methods that are specific to your application.

.. column::

    For example, imagine your application sends a custom header that contains a user ID. You can create a custom request object that will parse that header and store the user ID for you.

.. column::

    ```python
    from sanic import Sanic, Request

    class CustomRequest(Request):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.user_id = self.headers.get("X-User-ID")

    app = Sanic("Example", request_class=CustomRequest)
    ```


.. column::

    Now, in your handlers, you can access the `user_id` attribute.

.. column::

    ```python
    @app.route("/")
    async def handler(request: CustomRequest):
        return text(f"User ID: {request.user_id}")
    ```


### Custom Request Context

By default, the request context (`request.ctx`) is a [`Simplenamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) object allowing you to set arbitrary attributes on it. While this is super helpful to reuse logic across your application, it can be difficult in the development experience since the IDE will not know what attributes are available.

To help with this, you can create a custom request context object that will be used instead of the default `SimpleNamespace`. This allows you to add type hints to the context object and have them be available in your IDE.

.. column::

    Start by subclassing the :class:`sanic.request.Request` class to create a custom request type. Then, you will need to add a `make_context()` method that returns an instance of your custom context object. *NOTE: the `make_context` method should be a static method.*

.. column::

    ```python
    from sanic import Sanic, Request
    from types import SimpleNamespace

    class CustomRequest(Request):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.ctx.user_id = self.headers.get("X-User-ID")

        @staticmethod
        def make_context() -> CustomContext:
            return CustomContext()

    @dataclass
    class CustomContext:
        user_id: str = None
    ```

.. note::

    This is a Sanic poweruser feature that makes it super convenient in large codebases to have typed request context objects. It is of course not required, but can be very helpful.

*Added in v23.6*


## Parameters

.. column::

    Values that are extracted from the path parameters are injected into the handler as argumets, or more specifically as keyword arguments. There is much more detail about this in the [Routing section](./routing.md).

.. column::

    ```python
    @app.route('/tag/<tag>')
    async def tag_handler(request, tag):
        return text("Tag - {}".format(tag))
    
    # or, explicitly as keyword arguments
    @app.route('/tag/<tag>')
    async def tag_handler(request, *, tag):
        return text("Tag - {}".format(tag))
    ```


## Arguments

There are two attributes on the `request` instance to get query parameters:

- `request.args`
- `request.query_args`

These allow you to access the query parameters from the request path (the part after the `?` in the URL).

### Typical use case

In most use cases, you will want to use the `request.args` object to access the query parameters. This will be the parsed query string as a dictionary.

This is by far the most common pattern.

.. column::

    Consider the example where we have a `/search` endpoint with a `q` parameter that we want to use to search for something.

.. column::

    ```python
    @app.get("/search")
    async def search(request):
       query = request.args.get("q")
        if not query:
            return text("No query string provided")
        return text(f"Searching for: {query}")
    ```

### Parsing the query string

Sometimes, however, you may want to access the query string as a raw string or as a list of tuples. For this, you can use the `request.query_string` and `request.query_args` attributes. 

It also should be noted that HTTP allows multiple values for a single key. Although `request.args` may seem like a regular dictionary, it is actually a special type that allows for multiple values for a single key. You can access this by using the `request.args.getlist()` method.

- `request.query_string` - The raw query string
- `request.query_args` - The parsed query string as a list of tuples
- `request.args` - The parsed query string as a *special* dictionary
  - `request.args.get()` - Get the first value for a key (behaves like a regular dictionary)
  - `request.args.getlist()` - Get all values for a key

```sh
curl "http://localhost:8000?key1=val1&key2=val2&key1=val3"
```

```python
>>> print(request.args)
{'key1': ['val1', 'val3'], 'key2': ['val2']}

>>> print(request.args.get("key1"))
val1

>>> print(request.args.getlist("key1"))
['val1', 'val3']

>>> print(request.query_args)
[('key1', 'val1'), ('key2', 'val2'), ('key1', 'val3')]

>>> print(request.query_string)
key1=val1&key2=val2&key1=val3

```


.. tip:: FYI

    The `request.args` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

    Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.

## Current request getter

Sometimes you may find that you need access to the current request in your application in a location where it is not accessible. A typical example might be in a `logging` format. You can use `Request.get_current()` to fetch the current request (if any).

Remember, the request object is confined to the single [`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) that is running the handler. If you are not in that task, there is no request object.

```python
import logging

from sanic import Request, Sanic, json
from sanic.exceptions import SanicException
from sanic.log import LOGGING_CONFIG_DEFAULTS

LOGGING_FORMAT = (
    "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
    "%(request_id)s %(request)s %(message)s %(status)d %(byte)d"
)

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.request_id = ""

    try:
        request = Request.get_current()
    except SanicException:
        ...
    else:
        record.request_id = str(request.id)

    return record

logging.setLogRecordFactory(record_factory)


LOGGING_CONFIG_DEFAULTS["formatters"]["access"]["format"] = LOGGING_FORMAT
app = Sanic("Example", log_config=LOGGING_CONFIG_DEFAULTS)
```

In this example, we are adding the `request.id` to every access log message.

*Added in v22.6*
