# Blueprints

Blueprints are objects that can be used for sub-routing within an application.
Instead of adding routes to the application object, blueprints define similar
methods for adding routes, which are then registered with the application in a
flexible and plugable manner.

## Why?

Blueprints are especially useful for larger applications, where your application
logic can be broken down into several groups or areas of responsibility.

It is also useful for API versioning, where one blueprint may point at
`/v1/<routes>`, and another pointing at `/v2/<routes>`.


## My First Blueprint

The following shows a very simple blueprint that registers a handler-function at
the root `/` of your application.

Suppose you save this file as `my_blueprint.py`, this can be imported in your
main application later.

```python
from sanic.response import json
from sanic import Blueprint

bp = Blueprint('my_blueprint')

@bp.route('/')
async def bp_root():
    return json({'my': 'blueprint'})

```

## Registering Blueprints
Blueprints must be registered with the application.

```python
from sanic import Sanic
from my_blueprint import bp

app = Sanic(__name__)
app.register_blueprint(bp)

app.run(host='0.0.0.0', port=8000, debug=True)
```

This will add the blueprint to the application and register any routes defined
by that blueprint.
In this example, the registered routes in the `app.router` will look like:

```python
[Route(handler=<function bp_root at 0x7f908382f9d8>, methods=None, pattern=re.compile('^/$'), parameters=[])]
```

## Middleware
Blueprints must be registered with the application.

```python
@bp.middleware
async def halt_request(request):
	print("I am a spy")

@bp.middleware('request')
async def halt_request(request):
	return text('I halted the request')

@bp.middleware('response')
async def halt_response(request, response):
	return text('I halted the response')
```

## Exceptions
Blueprints must be registered with the application.

```python
@bp.exception(NotFound)
def ignore_404s(request, exception):
	return text("Yep, I totally found the page: {}".format(request.url))
```