# Blueprints

Blueprints are objects that can be used for sub-routing within an application.
Instead of adding routes to the application instance, blueprints define similar
methods for adding routes, which are then registered with the application in a
flexible and pluggable manner.

Blueprints are especially useful for larger applications, where your
application logic can be broken down into several groups or areas of
responsibility.

## My First Blueprint

The following shows a very simple blueprint that registers a handler-function at
the root `/` of your application.

Suppose you save this file as `my_blueprint.py`, which can be imported into your
main application later.

```python
from sanic.response import json
from sanic import Blueprint

bp = Blueprint('my_blueprint')

@bp.route('/')
async def bp_root(request):
    return json({'my': 'blueprint'})

```

## Registering blueprints

Blueprints must be registered with the application.

```python
from sanic import Sanic
from my_blueprint import bp

app = Sanic(__name__)
app.blueprint(bp)

app.run(host='0.0.0.0', port=8000, debug=True)
```

This will add the blueprint to the application and register any routes defined
by that blueprint. In this example, the registered routes in the `app.router`
will look like:

```python
[Route(handler=<function bp_root at 0x7f908382f9d8>, methods=None, pattern=re.compile('^/$'), parameters=[])]
```

## Using blueprints

Blueprints have much the same functionality as an application instance.

### Middleware

Using blueprints allows you to also register middleware globally.

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

### Exceptions

Exceptions can be applied exclusively to blueprints globally.

```python
@bp.exception(NotFound)
def ignore_404s(request, exception):
	return text("Yep, I totally found the page: {}".format(request.url))
```

### Static files

Static files can be served globally, under the blueprint prefix.

```python
bp.static('/folder/to/serve', '/web/path')
```

## Start and stop

Blueprints can run functions during the start and stop process of the server.
If running in multiprocessor mode (more than 1 worker), these are triggered
after the workers fork.

Available events are:

- `before_server_start`: Executed before the server begins to accept connections
- `after_server_start`: Executed after the server begins to accept connections
- `before_server_stop`: Executed before the server stops accepting connections
- `after_server_stop`: Executed after the server is stopped and all requests are complete

```python
bp = Blueprint('my_blueprint')

@bp.listen('before_server_start')
async def setup_connection():
    global database
    database = mysql.connect(host='127.0.0.1'...)
    
@bp.listen('after_server_stop')
async def close_connection():
    await database.close()
```

## Use-case: API versioning

Blueprints can be very useful for API versioning, where one blueprint may point
at `/v1/<routes>`, and another pointing at `/v2/<routes>`.

When a blueprint is initialised, it can take an optional `url_prefix` argument,
which will be prepended to all routes defined on the blueprint. This feature
can be used to implement our API versioning scheme.

```python
# blueprints.py
from sanic.response import text
from sanic import Blueprint

blueprint_v1 = Blueprint('v1')
blueprint_v2 = Blueprint('v2')

@blueprint_v1.route('/')
async def api_v1_root(request):
    return text('Welcome to version 1 of our documentation')
    
@blueprint_v2.route('/')
async def api_v2_root(request):
    return text('Welcome to version 2 of our documentation')
```

When we register our blueprints on the app, the routes `/v1` and `/v2` will now
point to the individual blueprints, which allows the creation of *sub-sites*
for each API version.

```python
# main.py
from sanic import Sanic
from blueprints import blueprint_v1, blueprint_v2

app = Sanic(__name__)
app.blueprint(blueprint_v1)
app.blueprint(blueprint_v2)

app.run(host='0.0.0.0', port=8000, debug=True)
```

**Previous:** [Exceptions](exceptions.html)

**Next:** [Class-based views](class_based_views.html)
