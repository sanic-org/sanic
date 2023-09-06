# Exceptions

## Using Sanic exceptions

Sometimes you just need to tell Sanic to halt execution of a handler and send back a status code response. You can raise a `SanicException` for this and Sanic will do the rest for you.

You can pass an optional `status_code` argument. By default, a SanicException will return an internal server error 500 response.

```python
from sanic.exceptions import SanicException

@app.route("/youshallnotpass")
async def no_no(request):
        raise SanicException("Something went wrong.", status_code=501)
```

Sanic provides a number of standard exceptions. They each automatically will raise the appropriate HTTP status code in your response. [Check the API reference](https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#module-sanic.exceptions) for more details. 

.. column::

    The more common exceptions you _should_ implement yourself include:

    - `BadRequest` (400)
    - `Unauthorized` (401)
    - `Forbidden` (403)
    - `NotFound` (404)
    - `ServerError` (500)

.. column::

    ```python
    from sanic import exceptions

    @app.route("/login")
    async def login(request):
        user = await some_login_func(request)
        if not user:
            raise exceptions.NotFound(
                f"Could not find user with username={request.json.username}"
            )
    ```

## Exception properties

All exceptions in Sanic derive from `SanicException`. That class has a few properties on it that assist the developer in consistently reporting their exceptions across an application.

- `message`
- `status_code`
- `quiet`
- `headers`
- `context`
- `extra`

All of these properties can be passed to the exception when it is created, but the first three can also be used as class variables as we will see.

.. column::

    ### `message`

    The `message` property obviously controls the message that will be displayed as with any other exception in Python. What is particularly useful is that you can set the `message` property on the class definition allowing for easy standardization of language across an application

.. column::

    ```python
    class CustomError(SanicException):
        message = "Something bad happened"

    raise CustomError
    # or
    raise CustomError("Override the default message with something else")
    ```


.. column::

    ### `status_code`

    This property is used to set the response code when the exception is raised. This can particularly be useful when creating custom 400 series exceptions that are usually in response to bad information coming from the client.

.. column::

    ```python
    class TeapotError(SanicException):
        status_code = 418
        message = "Sorry, I cannot brew coffee"

    raise TeapotError
    # or
    raise TeapotError(status_code=400)
    ```


.. column::

    ### `quiet`

    By default, exceptions will be output by Sanic to the `error_logger`. Sometimes this may not be desirable, especially if you are using exceptions to trigger events in exception handlers (see [the following section](./exceptions.md#handling)). You can suppress the log output using `quiet=True`.

.. column::

    ```python
    class SilentError(SanicException):
        message = "Something happened, but not shown in logs"
        quiet = True

    raise SilentError
    # or
    raise InvalidUsage("blah blah", quiet=True)
    ```


.. column::

    Sometimes while debugging you may want to globally ignore the `quiet=True` property. You can force Sanic to log out all exceptions regardless of this property using `NOISY_EXCEPTIONS`

    *Added in v21.12*

.. column::

    ```python
    app.config.NOISY_EXCEPTIONS = True
    ```


.. column::

    ### `headers`

    Using `SanicException` as a tool for creating responses is super powerful. This is in part because not only can you control the `status_code`, but you can also control reponse headers directly from the exception.

.. column::

    ```python
    class MyException(SanicException):
        headers = {
          "X-Foo": "bar"
        }

    raise MyException
    # or
    raise InvalidUsage("blah blah", headers={
        "X-Foo": "bar"
    })
    ```


.. column::

    ### `extra`

    See [contextual exceptions](./exceptions.md#contextual-exceptions)

    *Added in v21.12*

.. column::

    ```python
    raise SanicException(..., extra={"name": "Adam"})
    ```


.. column::

    ### `context`

    See [contextual exceptions](./exceptions.md#contextual-exceptions)

    *Added in v21.12*

.. column::

    ```python
    raise SanicException(..., context={"foo": "bar"})
    ```


## Handling

Sanic handles exceptions automatically by rendering an error page, so in many cases you don't need to handle them yourself. However, if you would like more control on what to do when an exception is raised, you can implement a handler yourself.

Sanic provides a decorator for this, which applies to not only the Sanic standard exceptions, but **any** exception that your application might throw.

.. column::

    The easiest method to add a handler is to use `@app.exception()` and pass it one or more exceptions.

.. column::

    ```python
    from sanic.exceptions import NotFound

    @app.exception(NotFound, SomeCustomException)
    async def ignore_404s(request, exception):
        return text("Yep, I totally found the page: {}".format(request.url))
    ```


.. column::

    You can also create a catchall handler by catching `Exception`.

.. column::

    ```python
    @app.exception(Exception)
    async def catch_anything(request, exception):
        ...
    ```


.. column::

    You can also use `app.error_handler.add()` to add error handlers.

.. column::

    ```python
    async def server_error_handler(request, exception):
        return text("Oops, server error", status=500)

    app.error_handler.add(Exception, server_error_handler)
    ```

## Built-in error handling

Sanic ships with three formats for exceptions: HTML, JSON, and text. You can see examples of them below in the [Fallback handler](#fallback-handler) section.

.. column::

    You can control _per route_ which format to use with the `error_format` keyword argument.

    *Added in v21.9*

.. column::

    ```python
    @app.request("/", error_format="text")
    async def handler(request):
        ...
    ```


## Custom error handling

In some cases, you might want to add some more error handling functionality to what is provided by default. In that case, you can subclass Sanic's default error handler as such:

```python
from sanic.handlers import ErrorHandler

class CustomErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        ''' handles errors that have no error handlers assigned '''
        # You custom error handling logic...
        status_code = getattr(exception, "status_code", 500)
        return json({
          "error": str(exception),
          "foo": "bar"
        }, status=status_code)

app.error_handler = CustomErrorHandler()
```

## Fallback handler

Sanic comes with three fallback exception handlers:

1. HTML
2. Text
3. JSON

These handlers present differing levels of detail depending upon whether your application is in [debug mode](/guide/deployment/development.md) or not.

By default, Sanic will be in "auto" mode, which means that it will using the incoming request and potential matching handler to choose the appropriate response format. For example, when in a browser it should always provide an HTML error page. When using curl, you might see JSON or plain text.

### HTML

```python
app.config.FALLBACK_ERROR_FORMAT = "html"
```

.. column::

    ```python
    app.config.DEBUG = True
    ```

    ![Error](/assets/images/error-display-html-debug.png)

.. column::

    ```python
    app.config.DEBUG = False
    ```

    ![Error](/assets/images/error-display-html-prod.png)

### Text

```python
app.config.FALLBACK_ERROR_FORMAT = "text"
```

.. column::

    ```python
    app.config.DEBUG = True
    ```

    ```sh
    curl localhost:8000/exc -i
    HTTP/1.1 500 Internal Server Error
    content-length: 620
    connection: keep-alive
    content-type: text/plain; charset=utf-8

    ⚠️ 500 — Internal Server Error
    ==============================
    That time when that thing broke that other thing? That happened.

    ServerError: That time when that thing broke that other thing? That happened. while handling path /exc
    Traceback of TestApp (most recent call last):

      ServerError: That time when that thing broke that other thing? That happened.
        File /path/to/sanic/app.py, line 979, in handle_request
        response = await response

        File /path/to/server.py, line 16, in handler
        do_something(cause_error=True)

        File /path/to/something.py, line 9, in do_something
        raise ServerError(
    ```

.. column::

    ```python
    app.config.DEBUG = False
    ```

    ```sh
    curl localhost:8000/exc -i
    HTTP/1.1 500 Internal Server Error
    content-length: 134
    connection: keep-alive
    content-type: text/plain; charset=utf-8

    ⚠️ 500 — Internal Server Error
    ==============================
    That time when that thing broke that other thing? That happened.
    ```

### JSON

```python
app.config.FALLBACK_ERROR_FORMAT = "json"
```

.. column::

    ```python
    app.config.DEBUG = True
    ```

    ```sh
    curl localhost:8000/exc -i
    HTTP/1.1 500 Internal Server Error
    content-length: 572
    connection: keep-alive
    content-type: application/jso

    {
      "description": "Internal Server Error",
      "status": 500,
      "message": "That time when that thing broke that other thing? That happened.",
      "path": "/exc",
      "args": {},
      "exceptions": [
        {
          "type": "ServerError",
          "exception": "That time when that thing broke that other thing? That happened.",
          "frames": [
            {
              "file": "/path/to/sanic/app.py",
              "line": 979,
              "name": "handle_request",
              "src": "response = await response"
            },
            {
              "file": "/path/to/server.py",
              "line": 16,
              "name": "handler",
              "src": "do_something(cause_error=True)"
            },
            {
              "file": "/path/to/something.py",
              "line": 9,
              "name": "do_something",
              "src": "raise ServerError("
            }
          ]
        }
      ]
    }
    ```

.. column::

    ```python
    app.config.DEBUG = False
    ```

    ```sh
    curl localhost:8000/exc -i
    HTTP/1.1 500 Internal Server Error
    content-length: 129
    connection: keep-alive
    content-type: application/json

    {
      "description": "Internal Server Error",
      "status": 500,
      "message": "That time when that thing broke that other thing? That happened."
    }

    ```

### Auto

Sanic also provides an option for guessing which fallback option to use.

```python
app.config.FALLBACK_ERROR_FORMAT = "auto"
```
## Contextual Exceptions

Default exception messages that simplify the ability to consistently raise exceptions throughout your application.

```python
class TeapotError(SanicException):
    status_code = 418
    message = "Sorry, I cannot brew coffee"

raise TeapotError
```

But this lacks two things:

1. A dynamic and predictable message format
2. The ability to add additional context to an error message (more on this in a moment)

*Added in v21.12*

Using one of Sanic's exceptions, you have two options to provide additional details at runtime:

```python
raise TeapotError(extra={"foo": "bar"}, context={"foo": "bar"})
```

What's the difference and when should you decide to use each?

- `extra` - The object itself will **never** be sent to a production client. It is meant for internal use only. What could it be used for?
  - Generating (as we will see in a minute) a dynamic error message
  - Providing runtime details to a logger
  - Debug information (when in development mode, it is rendered)
- `context` - This object is **always** sent to production clients. It is generally meant to be used to send additional details about the context of what happened. What could it be used for?
  - Providing alternative values on a `BadRequest` validation issue
  - Responding with helpful details for your customers to open a support ticket
  - Displaying state information like current logged in user info

### Dynamic and predictable message using `extra`

Sanic exceptions can be raised using `extra` keyword arguments to provide additional information to a raised exception instance.

```python
class TeapotError(SanicException):
    status_code = 418

    @property
    def message(self):
        return f"Sorry {self.extra['name']}, I cannot make you coffee"

raise TeapotError(extra={"name": "Adam"})
```

The new feature allows the passing of `extra` meta to the exception instance, which can be particularly useful as in the above example to pass dynamic data into the message text. This `extra` info object **will be suppressed** when in `PRODUCTION` mode, but displayed in `DEVELOPMENT` mode.

.. column::

    **DEVELOPMENT**

    ![image](~@assets/images/error-extra-debug.png)

.. column::

    **PRODUCTION**

    ![image](~@assets/images/error-extra-prod.png)

### Additional `context` to an error message

Sanic exceptions can also be raised with a `context` argument to pass intended information along to the user about what happened. This is particularly useful when creating microservices or an API intended to pass error messages in JSON format. In this use case, we want to have some context around the exception beyond just a parseable error message to return details to the client.

```python
raise TeapotError(context={"foo": "bar"})
```

This is information **that we want** to always be passed in the error (when it is available). Here is what it should look like:

.. column::

    **PRODUCTION**

    ```json
    {
      "description": "I'm a teapot",
      "status": 418,
      "message": "Sorry Adam, I cannot make you coffee",
      "context": {
        "foo": "bar"
      }
    }
    ```

.. column::

    **DEVELOPMENT**

    ```json
    {
      "description": "I'm a teapot",
      "status": 418,
      "message": "Sorry Adam, I cannot make you coffee",
      "context": {
        "foo": "bar"
      },
      "path": "/",
      "args": {},
      "exceptions": [
        {
          "type": "TeapotError",
          "exception": "Sorry Adam, I cannot make you coffee",
          "frames": [
            {
              "file": "handle_request",
              "line": 83,
              "name": "handle_request",
              "src": ""
            },
            {
              "file": "/tmp/p.py",
              "line": 17,
              "name": "handler",
              "src": "raise TeapotError("
            }
          ]
        }
      ]
    }
    ```



.. new:: NEW in v23.6

    ## Error reporting

    Sanic has a [signal](../advanced/signals.md#built-in-signals) that allows you to hook into the exception reporting process. This is useful if you want to send exception information to a third party service like Sentry or Rollbar. This can be conveniently accomplished by attaching an error reporting handler as show below:

    ```python
    @app.report_exception
    async def catch_any_exception(app: Sanic, exception: Exception):
        print("Caught exception:", exception)
    ```

.. note::

    This handler will be dispatched into a background task and **IS NOT** intended for use to manipulate any response data. It is intended to be used for logging or reporting purposes only, and should not impact the ability of your application to return the error response to the client.

*Added in v23.6*

