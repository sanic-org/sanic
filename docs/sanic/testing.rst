Testing
=======

Sanic endpoints can be tested locally using the `test_client` object, which
depends on an additional package: `httpx <https://www.encode.io/httpx/>`_
library, which implements an API that mirrors the `requests` library.

The `test_client` exposes `get`, `post`, `put`, `delete`, `patch`, `head` and `options` methods
for you to run against your application. A simple example (using pytest) is like follows:

.. code-block:: python

    # Import the Sanic app, usually created with Sanic(__name__)
    from external_server import app

    def test_index_returns_200():
        request, response = app.test_client.get('/')
        assert response.status == 200

    def test_index_put_not_allowed():
        request, response = app.test_client.put('/')
        assert response.status == 405

Internally, each time you call one of the `test_client` methods, the Sanic app is run at `127.0.0.1:42101` and
your test request is executed against your application, using `httpx`.

The `test_client` methods accept the following arguments and keyword arguments:

- `uri` *(default `'/'`)* A string representing the URI to test.
- `gather_request` *(default `True`)* A boolean which determines whether the
  original request will be returned by the function. If set to `True`, the
  return value is a tuple of `(request, response)`, if `False` only the
  response is returned.
- `server_kwargs` *(default `{}`)* a dict of additional arguments to pass into `app.run` before the test request is run.
- `debug` *(default `False`)* A boolean which determines whether to run the server in debug mode.

The function further takes the `*request_args` and `**request_kwargs`, which are passed directly to the request.

For example, to supply data to a GET request, you would do the following:

.. code-block:: python

    def test_get_request_includes_data():
        params = {'key1': 'value1', 'key2': 'value2'}
        request, response = app.test_client.get('/', params=params)
        assert request.args.get('key1') == 'value1'

And to supply data to a JSON POST request:

.. code-block:: python

    def test_post_json_request_includes_data():
        data = {'key1': 'value1', 'key2': 'value2'}
        request, response = app.test_client.post('/', data=json.dumps(data))
        assert request.json.get('key1') == 'value1'

More information about
the available arguments to `httpx` can be found
[in the documentation for `httpx <https://www.encode.io/httpx/>`_.

.. code-block:: python
    @pytest.mark.asyncio
    async def test_index_returns_200():
        request, response = await app.asgi_client.put('/')
        assert response.status == 200
.. note::

    Whenever one of the test clients run, you can test your app instance to determine if it is in testing mode:
    `app.test_mode`.

Additionally, Sanic has an asynchronous testing client. The difference is that the async client will not stand up an
instance of your application, but will instead reach inside it using ASGI. All listeners and middleware are still
executed.

.. code-block:: python

    @pytest.mark.asyncio
    async def test_index_returns_200():
        request, response = await app.asgi_client.put('/')
        assert response.status == 200

.. note::

    Whenever one of the test clients run, you can test your app instance to determine if it is in testing mode:
    `app.test_mode`.


Using a random port
-------------------

If you need to test using a free unpriveleged port chosen by the kernel
instead of the default with `SanicTestClient`, you can do so by specifying
`port=None`. On most systems the port will be in the range 1024 to 65535.

.. code-block:: python

    # Import the Sanic app, usually created with Sanic(__name__)
    from external_server import app
    from sanic.testing import SanicTestClient

    def test_index_returns_200():
        request, response = SanicTestClient(app, port=None).get('/')
        assert response.status == 200

pytest-sanic
------------

`pytest-sanic <https://github.com/yunstanford/pytest-sanic>`_ is a pytest plugin, it helps you to test your code asynchronously.
Just write tests like,

.. code-block:: python

    async def test_sanic_db_find_by_id(app):
        """
        Let's assume that, in db we have,
            {
                "id": "123",
                "name": "Kobe Bryant",
                "team": "Lakers",
            }
        """
        doc = await app.db["players"].find_by_id("123")
        assert doc.name == "Kobe Bryant"
        assert doc.team == "Lakers"

`pytest-sanic <https://github.com/yunstanford/pytest-sanic>`_ also provides some useful fixtures, like loop, unused_port,
test_server, test_client.

.. code-block:: python

    @pytest.yield_fixture
    def app():
        app = Sanic("test_sanic_app")

        @app.route("/test_get", methods=['GET'])
        async def test_get(request):
            return response.json({"GET": True})

        @app.route("/test_post", methods=['POST'])
        async def test_post(request):
            return response.json({"POST": True})

        yield app


    @pytest.fixture
    def test_cli(loop, app, test_client):
        return loop.run_until_complete(test_client(app, protocol=WebSocketProtocol))


    #########
    # Tests #
    #########

    async def test_fixture_test_client_get(test_cli):
        """
        GET request
        """
        resp = await test_cli.get('/test_get')
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json == {"GET": True}

    async def test_fixture_test_client_post(test_cli):
        """
        POST request
        """
        resp = await test_cli.post('/test_post')
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json == {"POST": True}
