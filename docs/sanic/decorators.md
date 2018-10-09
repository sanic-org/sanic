# Handler Decorators

Since Sanic handlers are simple Python functions, you can apply decorators to them in a similar manner to Flask. A typical use case is when you want some code to run before a handler's code is executed. 

## Authorization Decorator

Let's say you want to check that a user is authorized to access a particular endpoint. You can create a decorator that wraps a handler function, checks a request if the client is authorized to access a resource, and sends the appropriate response.


```python
from functools import wraps
from sanic.response import json

def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = check_request_for_authorization_status(request)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized. 
                return json({'status': 'not_authorized'}, 403)
        return decorated_function
    return decorator


@app.route("/")
@authorized()
async def test(request):
    return json({'status': 'authorized'})
``` 

