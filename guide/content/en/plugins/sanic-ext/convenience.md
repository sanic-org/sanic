# Convenience

## Fixed serializer

.. column::

    Often when developing an application, there will be certain routes that always return the same sort of response. When this is the case, you can predefine the return serializer and on the endpoint, and then all that needs to be returned is the content.

.. column::

    ```python
    from sanic_ext import serializer

    @app.get("/<name>")
    @serializer(text)
    async def hello_world(request, name: str):
        if name.isnumeric():
            return "hello " * int(name)
        return f"Hello, {name}"
    ```



.. column::

    The `serializer` decorator also can add status codes.

.. column::

    ```python
    from sanic_ext import serializer

    @app.post("/")
    @serializer(text, status=202)
    async def create_something(request):
        ...
    ```

## Custom serializer

.. column::

    Using the `@serializer` decorator, you can also pass your own custom functions as long as they also return a valid type (`HTTPResonse`).

.. column::

    ```python
    def message(retval, request, action, status):
        return json(
            {
                "request_id": str(request.id),
                "action": action,
                "message": retval,
            },
            status=status,
        )

    @app.post("/<action>")
    @serializer(message)
    async def do_action(request, action: str):
        return "This is a message"
    ```


.. column::

    Now, returning just a string should return a nice serialized output.

.. column::

    ```python
    $ curl localhost:8000/eat_cookies -X POST
    {
      "request_id": "ef81c45b-235c-46dd-9dbd-b550f8fa77f9",
      "action": "eat_cookies",
      "message": "This is a message"
    }

    ```


## Request counter

.. column::

    Sanic Extensions comes with a subclass of `Request` that can be setup to automatically keep track of the number of requests processed per worker process. To enable this, you should pass the `CountedRequest` class to your application contructor.

.. column::

    ```python
    from sanic_ext import CountedRequest

    app = Sanic(..., request_class=CountedRequest)
    ```


.. column::

    You will now have access to the number of requests served during the lifetime of the worker process.

.. column::

    ```python
    @app.get("/")
    async def handler(request: CountedRequest):
        return json({"count": request.count})
    ```

If possible, the request count will also be added to the [worker state](../../guide/deployment/manager.md#worker-state).

![](https://user-images.githubusercontent.com/166269/190922460-43bd2cfc-f81a-443b-b84f-07b6ce475cbf.png)
