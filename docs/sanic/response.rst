Response
========

Use functions in `sanic.response` module to create responses.

Plain Text
----------

.. code-block:: python

    from sanic import response


    @app.route('/text')
    def handle_request(request):
        return response.text('Hello world!')

HTML
----

.. code-block:: python

    from sanic import response


    @app.route('/html')
    def handle_request(request):
        return response.html('<p>Hello world!</p>')

JSON
----


.. code-block:: python

    from sanic import response


    @app.route('/json')
    def handle_request(request):
        return response.json({'message': 'Hello world!'})

File
----

.. code-block:: python

    from sanic import response


    @app.route('/file')
    async def handle_request(request):
        return await response.file('/srv/www/whatever.png')

Streaming
---------

.. code-block:: python

    from sanic import response

    @app.route("/streaming")
    async def index(request):
        async def streaming_fn(response):
            await response.write('foo')
            await response.write('bar')
        return response.stream(streaming_fn, content_type='text/plain')

See `Streaming <streaming.html>`_ for more information.

File Streaming
--------------

For large files, a combination of File and Streaming above

.. code-block:: python

    from sanic import response

    @app.route('/big_file.png')
    async def handle_request(request):
        return await response.file_stream('/srv/www/whatever.png')

Redirect
--------

.. code-block:: python

    from sanic import response


    @app.route('/redirect')
    def handle_request(request):
        return response.redirect('/json')

Raw
---

Response without encoding the body

.. code-block:: python

    from sanic import response


    @app.route('/raw')
    def handle_request(request):
        return response.raw(b'raw data')

Empty
--------------

For responding with an empty message as defined by `RFC 2616 <https://tools.ietf.org/search/rfc2616#section-7.2.1>`_

.. code-block:: python

    from sanic import response

    @app.route('/empty')
    async def handle_request(request):
        return response.empty()

Modify headers or status
------------------------

To modify headers or status code, pass the `headers` or `status` argument to those functions:

.. code-block:: python

    from sanic import response


    @app.route('/json')
    def handle_request(request):
        return response.json(
            {'message': 'Hello world!'},
            headers={'X-Served-By': 'sanic'},
            status=200
        )
