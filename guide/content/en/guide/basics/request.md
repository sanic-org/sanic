# Request

The `Request` instance contains **a lot** of helpful information available on its parameters. Refer to the [API documentation](https://sanic.readthedocs.io/) for full details.

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

The `request.ctx` object is your playground to store whatever information you need to about the request.

This is often used to store items like authenticated user details. We will get more into [middleware](./middleware.md) later, but here is a simple example.

```python
@app.on_request
async def run_before_handler(request):
    request.ctx.user = await fetch_user_by_token(request.token)

@app.route('/hi')
async def hi_my_name_is(request):
    return text("Hi, my name is {}".format(request.ctx.user.name))
```

A typical use case would be to store the user object acquired from database in an authentication middleware. Keys added are accessible to all later middleware as well as the handler over the duration of the request.

Custom context is reserved for applications and extensions. Sanic itself makes no use of it.

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

### Custom Request Objects

As dicussed in [application customization](./app.md#custom-requests), you can create a subclass of `sanic.Request` to add additional functionality to the request object. This is useful for adding additional attributes or methods that are specific to your application.

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



.. new:: NEW in v23.6

    ### Custom Request Context

By default, the request context (`request.ctx`) is a `SimpleNamespace` object allowing you to set arbitrary attributes on it. While this is super helpful to reuse logic across your application, it can be difficult in the development experience since the IDE will not know what attributes are available.

To help with this, you can create a custom request context object that will be used instead of the default `SimpleNamespace`. This allows you to add type hints to the context object and have them be available in your IDE.

.. column::

    Start by subclassing the `sanic.Request` class to create a custom request type. Then, you will need to add a `make_context()` method that returns an instance of your custom context object. *NOTE: the `make_context` method should be a static method.*

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

*Added in v23.6*


## Parameters

.. column::

    Values that are extracted from the path are injected into the handler as parameters, or more specifically as keyword arguments. There is much more detail about this in the [Routing section](./routing.md).

.. column::

    ```python
    @app.route('/tag/<tag>')
    async def tag_handler(request, tag):
        return text("Tag - {}".format(tag))
    ```


## Arguments

There are two attributes on the `request` instance to get query parameters:

- `request.args`
- `request.query_args`

```bash
$ curl http://localhost:8000\?key1\=val1\&key2\=val2\&key1\=val3
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
