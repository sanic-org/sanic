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
[Route(handler=<function bp_root at 0x7f908382f9d8>, methods=frozenset({'GET'}), pattern=re.compile('^/$'), parameters=[], name='my_blueprint.bp_root', uri='/')]
```

## Blueprint groups and nesting

Blueprints may also be registered as part of a list or tuple, where the registrar will recursively cycle through any sub-sequences of blueprints and register them accordingly. The `Blueprint.group` method is provided to simplify this process, allowing a 'mock' backend directory structure mimicking what's seen from the front end. Consider this (quite contrived) example:

```
api/
├──content/
│  ├──authors.py
│  ├──static.py
│  └──__init__.py
├──info.py
└──__init__.py
app.py
```

Initialization of this app's blueprint hierarchy could go as follows:

```python
# api/content/authors.py
from sanic import Blueprint

authors = Blueprint('content_authors', url_prefix='/authors')
```
```python
# api/content/static.py
from sanic import Blueprint

static = Blueprint('content_static', url_prefix='/static')
```
```python
# api/content/__init__.py
from sanic import Blueprint

from .static import static
from .authors import authors

content = Blueprint.group(static, authors, url_prefix='/content')
```
```python
# api/info.py
from sanic import Blueprint

info = Blueprint('info', url_prefix='/info')
```
```python
# api/__init__.py
from sanic import Blueprint

from .content import content
from .info import info

api = Blueprint.group(content, info, url_prefix='/api')
```

And registering these blueprints in `app.py` can now be done like so:

```python
# app.py
from sanic import Sanic

from .api import api

app = Sanic(__name__)

app.blueprint(api)
```

## Using Blueprints

Blueprints have almost the same functionality as an application instance.

### WebSocket routes

WebSocket handlers can be registered on a blueprint using the `@bp.websocket`
decorator or `bp.add_websocket_route` method.

### Middleware

Using blueprints allows you to also register middleware globally.

```python
@bp.middleware
async def print_on_request(request):
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

# suppose bp.name == 'bp'

bp.static('/web/path', '/folder/to/serve')
# also you can pass name parameter to it for url_for
bp.static('/web/path', '/folder/to/server', name='uploads')
app.url_for('static', name='bp.uploads', filename='file.txt') == '/bp/web/path/file.txt'

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

@bp.listener('before_server_start')
async def setup_connection(app, loop):
    global database
    database = mysql.connect(host='127.0.0.1'...)

@bp.listener('after_server_stop')
async def close_connection(app, loop):
    await database.close()
```

## Use-case: API versioning

Blueprints can be very useful for API versioning, where one blueprint may point
at `/v1/<routes>`, and another pointing at `/v2/<routes>`.

When a blueprint is initialised, it can take an optional `version` argument,
which will be prepended to all routes defined on the blueprint. This feature
can be used to implement our API versioning scheme.

```python
# blueprints.py
from sanic.response import text
from sanic import Blueprint

blueprint_v1 = Blueprint('v1', url_prefix='/api', version="v1")
blueprint_v2 = Blueprint('v2', url_prefix='/api', version="v2")

@blueprint_v1.route('/')
async def api_v1_root(request):
    return text('Welcome to version 1 of our documentation')

@blueprint_v2.route('/')
async def api_v2_root(request):
    return text('Welcome to version 2 of our documentation')
```

When we register our blueprints on the app, the routes `/v1/api` and `/v2/api` will now
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

## URL Building with `url_for`

If you wish to generate a URL for a route inside of a blueprint, remember that the endpoint name
takes the format `<blueprint_name>.<handler_name>`. For example:

```python
@blueprint_v1.route('/')
async def root(request):
    url = request.app.url_for('v1.post_handler', post_id=5) # --> '/v1/api/post/5'
    return redirect(url)


@blueprint_v1.route('/post/<post_id>')
async def post_handler(request, post_id):
    return text('Post {} in Blueprint V1'.format(post_id))
```
