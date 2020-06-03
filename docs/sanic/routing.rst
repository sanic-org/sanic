Routing
-------

Routing allows the user to specify handler functions for different URL endpoints.

A basic route looks like the following, where `app` is an instance of the
`Sanic` class:

.. code-block:: python

    from sanic.response import json

    @app.route("/")
    async def test(request):
        return json({ "hello": "world" })

When the url `http://server.url/` is accessed (the base url of the server), the
final `/` is matched by the router to the handler function, `test`, which then
returns a JSON object.

Sanic handler functions must be defined using the `async def` syntax, as they
are asynchronous functions.

Request parameters
==================

Sanic comes with a basic router that supports request parameters.

To specify a parameter, surround it with angle quotes like so: `<PARAM>`.
Request parameters will be passed to the route handler functions as keyword
arguments.

.. code-block:: python

    from sanic.response import text

    @app.route('/tag/<tag>')
    async def tag_handler(request, tag):
        return text('Tag - {}'.format(tag))

To specify a type for the parameter, add a `:type` after the parameter name,
inside the quotes. If the parameter does not match the specified type, Sanic
will throw a `NotFound` exception, resulting in a `404: Page not found` error
on the URL.

Supported types
~~~~~~~~~~~~~~~

* `string`
    * "Bob"
    * "Python 3"
* `int`
    * 10
    * 20
    * 30
    * -10
    * (No floats work here)
* `number`
    * 1
    * 1.5
    * 10
    * -10
* `alpha`
    * "Bob"
    * "Python"
    * (If it contains a symbol or a non alphanumeric character it will fail)
* `path`
    * "hello"
    * "hello.text"
    * "hello world"
* `uuid`
    * 123a123a-a12a-1a1a-a1a1-1a12a1a12345 (UUIDv4 Support)
* `regex expression`

If no type is set then a string is expected. The argument given to the function will always be a string, independent of the type.

.. code-block:: python

    from sanic.response import text

    @app.route('/string/<string_arg:string>')
    async def string_handler(request, string_arg):
        return text('String - {}'.format(string_arg))

    @app.route('/int/<integer_arg:int>')
    async def integer_handler(request, integer_arg):
        return text('Integer - {}'.format(integer_arg))

    @app.route('/number/<number_arg:number>')
    async def number_handler(request, number_arg):
        return text('Number - {}'.format(number_arg))

    @app.route('/alpha/<alpha_arg:alpha>')
    async def number_handler(request, alpha_arg):
        return text('Alpha - {}'.format(alpha_arg))

    @app.route('/path/<path_arg:path>')
    async def number_handler(request, path_arg):
        return text('Path - {}'.format(path_arg))

    @app.route('/uuid/<uuid_arg:uuid>')
    async def number_handler(request, uuid_arg):
        return text('Uuid - {}'.format(uuid_arg))

    @app.route('/person/<name:[A-z]+>')
    async def person_handler(request, name):
        return text('Person - {}'.format(name))

    @app.route('/folder/<folder_id:[A-z0-9]{0,4}>')
    async def folder_handler(request, folder_id):
        return text('Folder - {}'.format(folder_id))

.. warning::

    `str` is not a valid type tag. If you want `str` recognition then you must use `string`

HTTP request types
==================

By default, a route defined on a URL will be available for only GET requests to that URL.
However, the `@app.route` decorator accepts an optional parameter, `methods`,
which allows the handler function to work with any of the HTTP methods in the list.

.. code-block:: python

    from sanic.response import text

    @app.route('/post', methods=['POST'])
    async def post_handler(request):
        return text('POST request - {}'.format(request.json))

    @app.route('/get', methods=['GET'])
    async def get_handler(request):
        return text('GET request - {}'.format(request.args))

There is also an optional `host` argument (which can be a list or a string). This restricts a route to the host or hosts provided. If there is a also a route with no host, it will be the default.

.. code-block:: python

    @app.route('/get', methods=['GET'], host='example.com')
    async def get_handler(request):
        return text('GET request - {}'.format(request.args))

    # if the host header doesn't match example.com, this route will be used
    @app.route('/get', methods=['GET'])
    async def get_handler(request):
        return text('GET request in default - {}'.format(request.args))

There are also shorthand method decorators:

.. code-block:: python

    from sanic.response import text

    @app.post('/post')
    async def post_handler(request):
        return text('POST request - {}'.format(request.json))

    @app.get('/get')
    async def get_handler(request):
        return text('GET request - {}'.format(request.args))

The `add_route` method
======================

As we have seen, routes are often specified using the `@app.route` decorator.
However, this decorator is really just a wrapper for the `app.add_route`
method, which is used as follows:

.. code-block:: python

    from sanic.response import text

    # Define the handler functions
    async def handler1(request):
        return text('OK')

    async def handler2(request, name):
        return text('Folder - {}'.format(name))

    async def person_handler2(request, name):
        return text('Person - {}'.format(name))

    # Add each handler function as a route
    app.add_route(handler1, '/test')
    app.add_route(handler2, '/folder/<name>')
    app.add_route(person_handler2, '/person/<name:[A-z]>', methods=['GET'])

URL building with `url_for`
===========================

Sanic provides a `url_for` method, to generate URLs based on the handler method name. This is useful if you want to avoid hardcoding url paths into your app; instead, you can just reference the handler name. For example:

.. code-block:: python

    from sanic.response import redirect

    @app.route('/')
    async def index(request):
        # generate a URL for the endpoint `post_handler`
        url = app.url_for('post_handler', post_id=5)
        # the URL is `/posts/5`, redirect to it
        return redirect(url)

    @app.route('/posts/<post_id>')
    async def post_handler(request, post_id):
        return text('Post - {}'.format(post_id))

Other things to keep in mind when using `url_for`:

- Keyword arguments passed to `url_for` that are not request parameters will be included in the URL's query string. For example:

.. code-block:: python

    url = app.url_for('post_handler', post_id=5, arg_one='one', arg_two='two')
    # /posts/5?arg_one=one&arg_two=two

- Multivalue argument can be passed to `url_for`. For example:

.. code-block:: python

    url = app.url_for('post_handler', post_id=5, arg_one=['one', 'two'])
    # /posts/5?arg_one=one&arg_one=two

- Also some special arguments (`_anchor`, `_external`, `_scheme`, `_method`, `_server`) passed to `url_for` will have special url building (`_method` is not supported now and will be ignored). For example:

.. code-block:: python

    url = app.url_for('post_handler', post_id=5, arg_one='one', _anchor='anchor')
    # /posts/5?arg_one=one#anchor

    url = app.url_for('post_handler', post_id=5, arg_one='one', _external=True)
    # //server/posts/5?arg_one=one
    # _external requires you to pass an argument _server or set SERVER_NAME in app.config if not url will be same as no _external

    url = app.url_for('post_handler', post_id=5, arg_one='one', _scheme='http', _external=True)
    # http://server/posts/5?arg_one=one
    # when specifying _scheme, _external must be True

    # you can pass all special arguments at once
    url = app.url_for('post_handler', post_id=5, arg_one=['one', 'two'], arg_two=2, _anchor='anchor', _scheme='http', _external=True, _server='another_server:8888')
    # http://another_server:8888/posts/5?arg_one=one&arg_one=two&arg_two=2#anchor

- All valid parameters must be passed to `url_for` to build a URL. If a parameter is not supplied, or if a parameter does not match the specified type, a `URLBuildError` will be raised.

WebSocket routes
================

Routes for the WebSocket protocol can be defined with the `@app.websocket`
decorator:

.. code-block:: python

    @app.websocket('/feed')
    async def feed(request, ws):
        while True:
            data = 'hello!'
            print('Sending: ' + data)
            await ws.send(data)
            data = await ws.recv()
            print('Received: ' + data)

Alternatively, the `app.add_websocket_route` method can be used instead of the
decorator:

.. code-block:: python

    async def feed(request, ws):
        pass

    app.add_websocket_route(my_websocket_handler, '/feed')

Handlers to a WebSocket route are invoked with the request as first argument, and a
WebSocket protocol object as second argument. The protocol object has `send`
and `recv` methods to send and receive data respectively.

WebSocket support requires the `websockets <https://github.com/aaugustin/websockets>`_
package by Aymeric Augustin.


About `strict_slashes`
======================

You can make `routes` strict to trailing slash or not, it's configurable.

.. code-block:: python

    # provide default strict_slashes value for all routes
    app = Sanic('test_route_strict_slash', strict_slashes=True)

    # you can also overwrite strict_slashes value for specific route
    @app.get('/get', strict_slashes=False)
    def handler(request):
        return text('OK')

    # It also works for blueprints
    bp = Blueprint('test_bp_strict_slash', strict_slashes=True)

    @bp.get('/bp/get', strict_slashes=False)
    def handler(request):
        return text('OK')

    app.blueprint(bp)

The behavior of how the `strict_slashes` flag follows a defined hierarchy which decides if a specific route
falls under the `strict_slashes` behavior.

|    Route/
|    ├──Blueprint/
|       ├──Application/

Above hierarchy defines how the `strict_slashes` flag will behave. The first non `None` value of the `strict_slashes`
found in the above order will be applied to the route in question.

.. code-block:: python

    from sanic import Sanic, Blueprint
    from sanic.response import text

    app = Sanic("sample_strict_slashes", strict_slashes=True)

    @app.get("/r1")
    def r1(request):
        return text("strict_slashes is applicable from App level")

    @app.get("/r2", strict_slashes=False)
    def r2(request):
        return text("strict_slashes is not applicable due to  False value set in route level")

    bp = Blueprint("bp", strict_slashes=False)

    @bp.get("/r3", strict_slashes=True)
    def r3(request):
        return text("strict_slashes applicable from blueprint route level")

    bp1 = Blueprint("bp1", strict_slashes=True)

    @bp.get("/r4")
    def r3(request):
        return text("strict_slashes applicable from blueprint level")

User defined route name
=======================

A custom route name can be used by passing a `name` argument while registering the route which will
override the default route name generated using the `handler.__name__` attribute.

.. code-block:: python

    app = Sanic('test_named_route')

    @app.get('/get', name='get_handler')
    def handler(request):
        return text('OK')

    # then you need use `app.url_for('get_handler')`
    # instead of # `app.url_for('handler')`

    # It also works for blueprints
    bp = Blueprint('test_named_bp')

    @bp.get('/bp/get', name='get_handler')
    def handler(request):
        return text('OK')

    app.blueprint(bp)

    # then you need use `app.url_for('test_named_bp.get_handler')`
    # instead of `app.url_for('test_named_bp.handler')`

    # different names can be used for same url with different methods

    @app.get('/test', name='route_test')
    def handler(request):
        return text('OK')

    @app.post('/test', name='route_post')
    def handler2(request):
        return text('OK POST')

    @app.put('/test', name='route_put')
    def handler3(request):
        return text('OK PUT')

    # below url are the same, you can use any of them
    # '/test'
    app.url_for('route_test')
    # app.url_for('route_post')
    # app.url_for('route_put')

    # for same handler name with different methods
    # you need specify the name (it's url_for issue)
    @app.get('/get')
    def handler(request):
        return text('OK')

    @app.post('/post', name='post_handler')
    def handler(request):
        return text('OK')

    # then
    # app.url_for('handler') == '/get'
    # app.url_for('post_handler') == '/post'

Build URL for static files
==========================

Sanic supports using `url_for` method to build static file urls. In case if the static url
is pointing to a directory, `filename` parameter to the `url_for` can be ignored.

.. code-block:: python

    app = Sanic('test_static')
    app.static('/static', './static')
    app.static('/uploads', './uploads', name='uploads')
    app.static('/the_best.png', '/home/ubuntu/test.png', name='best_png')

    bp = Blueprint('bp', url_prefix='bp')
    bp.static('/static', './static')
    bp.static('/uploads', './uploads', name='uploads')
    bp.static('/the_best.png', '/home/ubuntu/test.png', name='best_png')
    app.blueprint(bp)

    # then build the url
    app.url_for('static', filename='file.txt') == '/static/file.txt'
    app.url_for('static', name='static', filename='file.txt') == '/static/file.txt'
    app.url_for('static', name='uploads', filename='file.txt') == '/uploads/file.txt'
    app.url_for('static', name='best_png') == '/the_best.png'

    # blueprint url building
    app.url_for('static', name='bp.static', filename='file.txt') == '/bp/static/file.txt'
    app.url_for('static', name='bp.uploads', filename='file.txt') == '/bp/uploads/file.txt'
    app.url_for('static', name='bp.best_png') == '/bp/static/the_best.png'
