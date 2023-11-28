# Decorators

One of the best ways to create a consistent and DRY web API is to make use of decorators to remove functionality from the handlers, and make it repeatable across your views.

.. column::

    Therefore, it is very common to see a Sanic view handler with several decorators on it.

.. column::

    ```python
    @app.get("/orders")
    @authorized("view_order")
    @validate_list_params()
    @inject_user()
    async def get_order_details(request, params, user):
        ...
    ```


## Example

Here is a starter template to help you create decorators.

In this example, let’s say you want to check that a user is authorized to access a particular endpoint. You can create a decorator that wraps a handler function, checks a request if the client is authorized to access a resource, and sends the appropriate response.
```python
from functools import wraps
from sanic.response import json

def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = await check_request_for_authorization_status(request)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return json({"status": "not_authorized"}, 403)
        return decorated_function
    return decorator

@app.route("/")
@authorized()
async def test(request):
    return json({"status": "authorized"})
```

## Templates

Decorators are **fundamental** to building applications with Sanic. They increase the portability and maintainablity of your code. 

In paraphrasing the Zen of Python: "[decorators] are one honking great idea -- let's do more of those!"

To make it easier to implement them, here are three examples of copy/pastable code to get you started.

.. column::

    Don't forget to add these import statements. Although it is *not* necessary, using `@wraps` helps keep some of the metadata of your function intact. [See docs](https://docs.python.org/3/library/functools.html#functools.wraps). Also, we use the `isawaitable` pattern here to allow the route handlers to by regular or asynchronous functions.

.. column::

    ```python
    from inspect import isawaitable
    from functools import wraps
    ```

### With args

.. column::

    Often, you will want a decorator that will *always* need arguments. Therefore, when it is implemented you will always be calling it.

    ```python
    @app.get("/")
    @foobar(1, 2)
    async def handler(request: Request):
        return text("hi")
    ```

.. column::

    ```python
    def foobar(arg1, arg2):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):

                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response

                return response

            return decorated_function

        return decorator
    ```

### Without args

.. column::

    Sometimes you want a decorator that will not take arguments. When this is the case, it is a nice convenience not to have to call it

    ```python
    @app.get("/")
    @foobar
    async def handler(request: Request):
        return text("hi")
    ```

.. column::

    ```python
    def foobar(func):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):

                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response

                return response

            return decorated_function

        return decorator(func)
    ```

### With or Without args

.. column::

    If you want a decorator with the ability to be called or not, you can follow this pattern. Using keyword only arguments is not necessary, but might make implementation simpler.

    ```python
    @app.get("/")
    @foobar(arg1=1, arg2=2)
    async def handler(request: Request):
        return text("hi")
    ```

    ```python
    @app.get("/")
    @foobar
    async def handler(request: Request):
        return text("hi")
    ```

.. column::

    ```python
    def foobar(maybe_func=None, *, arg1=None, arg2=None):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):

                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response

                return response

            return decorated_function

        return decorator(maybe_func) if maybe_func else decorator
    ```

