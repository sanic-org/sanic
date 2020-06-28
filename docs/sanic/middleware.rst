Middleware And Listeners
========================

Middleware are functions which are executed before or after requests to the
server. They can be used to modify the *request to* or *response from*
user-defined handler functions.

Additionally, Sanic provides listeners which allow you to run code at various points of your application's lifecycle.

Middleware
----------

There are two types of middleware: request and response. Both are declared
using the `@app.middleware` decorator, with the decorator's parameter being a
string representing its type: `'request'` or `'response'`.

* Request middleware receives only the `request` as an argument and are executed in the order they were added.
* Response middleware receives both the `request` and `response` and are executed in *reverse* order.

The simplest middleware doesn't modify the request or response at all:

.. code-block:: python

    @app.middleware('request')
    async def print_on_request(request):
        print("I print when a request is received by the server")

    @app.middleware('response')
    async def print_on_response(request, response):
        print("I print when a response is returned by the server")

Modifying the request or response
---------------------------------

Middleware can modify the request or response parameter it is given, *as long
as it does not return it*. The following example shows a practical use-case for
this.

.. code-block:: python

    app = Sanic(__name__)


    @app.middleware('request')
    async def add_key(request):
        # Arbitrary data may be stored in request context:
        request.ctx.foo = 'bar'


    @app.middleware('response')
    async def custom_banner(request, response):
        response.headers["Server"] = "Fake-Server"


    @app.middleware('response')
    async def prevent_xss(request, response):
        response.headers["x-xss-protection"] = "1; mode=block"


    @app.get("/")
    async def index(request):
        return sanic.response.text(request.ctx.foo)


    app.run(host="0.0.0.0", port=8000)

The three middlewares are executed in the following order:

1. The first request middleware **add_key** adds a new key `foo` into request context.
2. Request is routed to handler **index**, which gets the key from context and returns a text response.
3. The second response middleware **prevent_xss** adds the HTTP header for preventing Cross-Site-Scripting (XSS) attacks.
4. The first response middleware **custom_banner** changes the HTTP response header *Server* to say *Fake-Server*

Responding early
----------------

If middleware returns a `HTTPResponse` object, the request will stop processing
and the response will be returned. If this occurs to a request before the
relevant user route handler is reached, the handler will never be called.
Returning a response will also prevent any further middleware from running.

.. code-block:: python

    @app.middleware('request')
    async def halt_request(request):
        return text('I halted the request')

    @app.middleware('response')
    async def halt_response(request, response):
        return text('I halted the response')

Custom context
--------------

Arbitrary data may be stored in `request.ctx`. A typical use case
would be to store the user object acquired from database in an authentication
middleware. Keys added are accessible to all later middleware as well as
the handler over the duration of the request.

Custom context is reserved for applications and extensions. Sanic itself makes
no use of it.

Listeners
---------

If you want to execute startup/teardown code as your server starts or closes, you can use the following listeners:

- `before_server_start`
- `after_server_start`
- `before_server_stop`
- `after_server_stop`

These listeners are implemented as decorators on functions which accept the app object as well as the asyncio loop.

For example:

.. code-block:: python

    @app.listener('before_server_start')
    async def setup_db(app, loop):
        app.db = await db_setup()

    @app.listener('after_server_start')
    async def notify_server_started(app, loop):
        print('Server successfully started!')

    @app.listener('before_server_stop')
    async def notify_server_stopping(app, loop):
        print('Server shutting down!')

    @app.listener('after_server_stop')
    async def close_db(app, loop):
        await app.db.close()

Note:

The listeners are deconstructed in the reverse order of being constructed.

For example:

If the first listener in before_server_start handler setups a database connection,
ones registered after it can rely on that connection being alive both when they are started
and stopped, because stopping is done in reverse order, and the database connection is
torn down last.

It's also possible to register a listener using the `register_listener` method.
This may be useful if you define your listeners in another module besides
the one you instantiate your app in.

.. code-block:: python

    app = Sanic(__name__)

    async def setup_db(app, loop):
        app.db = await db_setup()

    app.register_listener(setup_db, 'before_server_start')

If you want to schedule a background task to run after the loop has started,
Sanic provides the `add_task` method to easily do so.

.. code-block:: python

    async def notify_server_started_after_five_seconds():
        await asyncio.sleep(5)
        print('Server successfully started!')

    app.add_task(notify_server_started_after_five_seconds())

Sanic will attempt to automatically inject the app, passing it as an argument to the task:

.. code-block:: python

    async def notify_server_started_after_five_seconds(app):
        await asyncio.sleep(5)
        print(app.name)

    app.add_task(notify_server_started_after_five_seconds)

Or you can pass the app explicitly for the same effect:

.. code-block:: python

    async def notify_server_started_after_five_seconds(app):
        await asyncio.sleep(5)
        print(app.name)

    app.add_task(notify_server_started_after_five_seconds(app))
