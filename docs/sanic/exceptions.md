# Exceptions

Exceptions can be thrown from within request handlers and will automatically be
handled by Sanic. Exceptions take a message as their first argument, and can
also take a status code to be passed back in the HTTP response.

## Throwing an exception

To throw an exception, simply `raise` the relevant exception from the
`sanic.exceptions` module.

```python
from sanic.exceptions import ServerError

@app.route('/killme')
async def i_am_ready_to_die(request):
	raise ServerError("Something bad happened", status_code=500)
```

You can also use the `abort` function with the appropriate status code:

```python
from sanic.exceptions import abort
from sanic.response import text

@app.route('/youshallnotpass')
async def no_no(request):

	return abort(401)
```

## Handling exceptions

To override Sanic's default handling of an exception, the `@app.exception`
decorator is used. The decorator expects a list of exceptions to handle as
arguments. You can pass `SanicException` to catch them all! The decorated
exception handler function must take a `Request` and `Exception` object as
arguments.

```python
from sanic.response import text
from sanic.exceptions import NotFound

@app.exception(NotFound)
async def ignore_404s(request, exception):
	return text("Yep, I totally found the page: {}".format(request.url))
```

You can also add an exception handler as such:

```python
from sanic import Sanic

async def server_error_handler(request, exception):
	return text("Oops, server error", status=500)

app = Sanic()
app.error_handler.add(Exception, server_error_handler)
```

In some cases, you might want to add some more error handling
functionality to what is provided by default. In that case, you
can subclass Sanic's default error handler as such:

```python
from sanic import Sanic
from sanic.handlers import ErrorHandler

class CustomErrorHandler(ErrorHandler):
	def default(self, request, exception):
		''' handles errors that have no error handlers assigned '''
		# You custom error handling logic...
		return super().default(request, exception)

app = Sanic()
app.error_handler = CustomErrorHandler()
```

## Useful exceptions

Some of the most useful exceptions are presented below:

- `NotFound`: called when a suitable route for the request isn't found.
- `ServerError`: called when something goes wrong inside the server. This
  usually occurs if there is an exception raised in user code.

See the `sanic.exceptions` module for the full list of exceptions to throw.
