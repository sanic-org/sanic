# Exceptions

Exceptions can be thrown from within request handlers and will automatically be handled by Sanic.  Exceptions take a message as their first argument, and can also take a status_code to be passed back in the HTTP response.  Check sanic.exceptions for the full list of exceptions to throw.

## Throwing an exception

```python
from sanic import Sanic
from sanic.exceptions import ServerError

@app.route('/killme')
def i_am_ready_to_die(request):
	raise ServerError("Something bad happened")
```

## Handling Exceptions

Just use the @exception decorator.  The decorator expects a list of exceptions to handle as arguments.  You can pass SanicException to catch them all!  The exception handler must expect a request and exception object as arguments.

```python
from sanic import Sanic
from sanic.response import text
from sanic.exceptions import NotFound

@app.exception(NotFound)
def ignore_404s(request, exception):
	return text("Yep, I totally found the page: {}".format(request.url))
```