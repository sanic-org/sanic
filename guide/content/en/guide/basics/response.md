# Response

All [handlers](./handlers.md) *usually* return a response object, and [middleware](./middleware.md) may optionally return a response object.

To clarify that statement:
- unless the handler is a streaming endpoint handling its own pattern for sending bytes to the client, the return value must be an instance of `sanic.HTTPResponse` (to learn more about this exception see [streaming responses](../advanced/streaming.md#response-streaming))
- if a middleware returns a response object, that will be used instead of whatever the handler would do (see [middleware](./middleware.md) to learn more)

A most basic handler would look like the following. The `HTTPResponse` object will allow you to set the status, body, and headers to be returned to the client.

```python
from sanic import HTTPResponse, Sanic

app = Sanic("TestApp")

@app.route("")
def handler(_):
    return HTTPResponse()
```

However, usually it is easier to use one of the convenience methods discussed below.

## Methods

The easiest way to generate a response object is to use one of the nine (9) convenience methods.

### Text

.. column::

    **Default Content-Type**: `text/plain; charset=utf-8`  
    **Description**: Returns plain text

.. column::

    ```python
    from sanic import text

    @app.route("/")
    async def handler(request):
        return text("Hi 😎")
    ```

### HTML

.. column::

    **Default Content-Type**: `text/html; charset=utf-8`  
    **Description**: Returns an HTML document

.. column::

    ```python
    from sanic import html

    @app.route("/")
    async def handler(request):
        return html('<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><div>Hi 😎</div>')
    ```

### JSON

.. column::

    **Default Content-Type**: `application/json`  
    **Description**: Returns a JSON document

.. column::

    ```python
    from sanic import json

    @app.route("/")
    async def handler(request):
        return json({"foo": "bar"})
    ```

    By default, Sanic ships with [`ujson`](https://github.com/ultrajson/ultrajson) as its JSON encoder of choice. It is super simple to change this if you want.

    ```python
    from orjson import dumps

    json({"foo": "bar"}, dumps=dumps)
    ```

    If `ujson` is not installed, it will fall back to the standard library `json` module.

    You may additionally declare which implementation to use globally across your application at initialization:

    ```python
    from orjson import dumps

    app = Sanic(..., dumps=dumps)
    ```

### File

.. column::

    **Default Content-Type**: N/A  
    **Description**: Returns a file

.. column::

    ```python
    from sanic import file

    @app.route("/")
    async def handler(request):
        return await file("/path/to/whatever.png")
    ```

    Sanic will examine the file, and try and guess its mime type and use an appropriate value for the content type. You could be explicit, if you would like:

    ```python
    file("/path/to/whatever.png", mime_type="image/png")
    ```

    You can also choose to override the file name:

    ```python
    file("/path/to/whatever.png", filename="super-awesome-incredible.png")
    ```

### File Streaming

.. column::

    **Default Content-Type**: N/A  
    **Description**: Streams a file to a client, useful when streaming large files, like a video

.. column::

    ```python
    from sanic.response import file_stream

    @app.route("/")
    async def handler(request):
        return await file_stream("/path/to/whatever.mp4")
    ```

    Like the `file()` method, `file_stream()` will attempt to determine the mime type of the file.



### Raw

.. column::

    **Default Content-Type**: `application/octet-stream`  
    **Description**: Send raw bytes without encoding the body

.. column::

    ```python
    from sanic import raw

    @app.route("/")
    async def handler(request):
        return raw(b"raw bytes")
    ```

### Redirect

.. column::

    **Default Content-Type**: `text/html; charset=utf-8`  
    **Description**: Send a `302` response to redirect the client to a different path

.. column::

    ```python
    from sanic import redirect

    @app.route("/")
    async def handler(request):
        return redirect("/login")
    ```

### Empty

.. column::

    **Default Content-Type**: N/A  
    **Description**: For responding with an empty message as defined by [RFC 2616](https://tools.ietf.org/search/rfc2616#section-7.2.1)

.. column::

    ```python
    from sanic import empty

    @app.route("/")
    async def handler(request):
        return empty()
    ```

    Defaults to a `204` status.

## Default status

The default HTTP status code for the response is `200`. If you need to change it, it can be done by the response method.

```python
@app.post("/")
async def create_new(request):
    new_thing = await do_create(request)
    return json({"created": True, "id": new_thing.thing_id}, status=201)
```

## Returning JSON data

Starting in v22.12, When you use the `sanic.json` convenience method, it will return a subclass of `HTTPResponse` called `JSONResponse`. This object will 
have several convenient methods available to modify common JSON body.

```python
from sanic import json

resp = json(...)
```

- `resp.set_body(<raw_body>)` - Set the body of the JSON object to the value passed
- `resp.append(<value>)` - Append a value to the body like `list.append` (only works if the root JSON is an array)
- `resp.extend(<value>)` - Extend a value to the body like `list.extend` (only works if the root JSON is an array)
- `resp.update(<value>)` - Update the body with a value like `dict.update` (only works if the root JSON is an object)
- `resp.pop()` - Pop a value like `list.pop` or `dict.pop` (only works if the root JSON is an array or an object)

.. warning::

    The raw Python object is stored on the `JSONResponse` object as `raw_body`. While it is safe to overwrite this value with a new one, you should **not** attempt to mutate it. You should instead use the methods listed above.

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

*Added in v22.9*
