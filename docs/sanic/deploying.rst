Deploying
=========

Sanic has three serving options: the inbuilt webserver,
an `ASGI webserver <https://asgi.readthedocs.io/en/latest/implementations.html>`_, or `gunicorn`.

Sanic's own webserver is the fastest option, and it can be securely run on
the Internet. Still, it is also very common to place Sanic behind a reverse
proxy, as shown in :ref:`nginx`.

Running via Sanic webserver
---------------------------

After defining an instance of `sanic.Sanic`, we can call the `run` method with the following
keyword arguments:

- `host` *(default `"127.0.0.1"`)*: Address to host the server on.
- `port` *(default `8000`)*: Port to host the server on.
- `debug` *(default `False`)*: Enables debug output (slows server).
- `ssl` *(default `None`)*: `SSLContext` for SSL encryption of worker(s).
- `sock` *(default `None`)*: Socket for the server to accept connections from.
- `workers` *(default `1`)*: Number of worker processes to spawn.
- `loop` *(default `None`)*: An `asyncio`-compatible event loop. If none is specified, Sanic creates its own event loop.
- `protocol` *(default `HttpProtocol`)*: Subclass of `asyncio.protocol <https://docs.python.org/3/library/asyncio-protocol.html#protocol-classes>`_.
- `access_log` *(default `True`)*: Enables log on handling requests (significantly slows server).

.. code-block:: python

    app.run(host='0.0.0.0', port=1337, access_log=False)

In the above example, we decided to turn off the access log in order to increase performance.

Workers
~~~~~~~

By default, Sanic listens in the main process using only one CPU core. To crank
up the juice, just specify the number of workers in the `run` arguments.

.. code-block:: python

    app.run(host='0.0.0.0', port=1337, workers=4)

Sanic will automatically spin up multiple processes and route traffic between
them. We recommend as many workers as you have available cores.

Running via command
~~~~~~~~~~~~~~~~~~~

If you like using command line arguments, you can launch a Sanic webserver by
executing the module. For example, if you initialized Sanic as `app` in a file
named `server.py`, you could run the server like so:

.. python -m sanic server.app --host=0.0.0.0 --port=1337 --workers=4

With this way of running sanic, it is not necessary to invoke `app.run` in your
Python file. If you do, make sure you wrap it so that it only executes when
directly run by the interpreter.

.. code-block:: python

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=1337, workers=4)

Running via ASGI
----------------

Sanic is also ASGI-compliant. This means you can use your preferred ASGI webserver
to run Sanic. The three main implementations of ASGI are
`Daphne <http://github.com/django/daphne>`_, `Uvicorn <https://www.uvicorn.org/>`_,
and `Hypercorn <https://pgjones.gitlab.io/hypercorn/index.html>`_.

Follow their documentation for the proper way to run them, but it should look
something like:

::

    daphne myapp:app
    uvicorn myapp:app
    hypercorn myapp:app

A couple things to note when using ASGI:

1. When using the Sanic webserver, websockets will run using the `websockets <https://websockets.readthedocs.io/>`_ package.
In ASGI mode, there is no need for this package since websockets are managed in the ASGI server.
2. The ASGI `lifespan protocol <https://asgi.readthedocs.io/en/latest/specs/lifespan.html>`, supports
only two server events: startup and shutdown. Sanic has four: before startup, after startup,
before shutdown, and after shutdown. Therefore, in ASGI mode, the startup and shutdown events will
run consecutively and not actually around the server process beginning and ending (since that
is now controlled by the ASGI server). Therefore, it is best to use `after_server_start` and
`before_server_stop`.

Sanic has experimental support for running on `Trio <https://trio.readthedocs.io/en/stable/>`_ with::

    hypercorn -k trio myapp:app


Running via Gunicorn
--------------------

`Gunicorn <http://gunicorn.org/>`_ ‘Green Unicorn’ is a WSGI HTTP Server for UNIX.
It’s a pre-fork worker model ported from Ruby’s Unicorn project.

In order to run Sanic application with Gunicorn, you need to use the special `sanic.worker.GunicornWorker`
for Gunicorn `worker-class` argument:

::

    gunicorn myapp:app --bind 0.0.0.0:1337 --worker-class sanic.worker.GunicornWorker


If your application suffers from memory leaks, you can configure Gunicorn to gracefully restart a worker
after it has processed a given number of requests. This can be a convenient way to help limit the effects
of the memory leak.

See the `Gunicorn Docs <http://docs.gunicorn.org/en/latest/settings.html#max-requests>`_ for more information.

Other deployment considerations
-------------------------------

Disable debug logging for performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To improve the performance add `debug=False` and `access_log=False` in the `run` arguments.

.. code-block:: python

    app.run(host='0.0.0.0', port=1337, workers=4, debug=False, access_log=False)

Running via Gunicorn you can set Environment variable `SANIC_ACCESS_LOG="False"`

::

    env SANIC_ACCESS_LOG="False" gunicorn myapp:app --bind 0.0.0.0:1337 --worker-class sanic.worker.GunicornWorker --log-level warning

Or you can rewrite app config directly

.. code-block:: python

    app.config.ACCESS_LOG = False

Asynchronous support and sharing the loop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is suitable if you *need* to share the Sanic process with other applications, in particular the `loop`.
However, be advised that this method does not support using multiple processes, and is not the preferred way
to run the app in general.

Here is an incomplete example (please see `run_async.py` in examples for something more practical):

.. code-block:: python

    server = app.create_server(host="0.0.0.0", port=8000, return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(server)
    loop.run_forever()

Caveat: using this method, calling `app.create_server()` will trigger "before_server_start" server events, but not
"after_server_start", "before_server_stop", or "after_server_stop" server events.

For more advanced use-cases, you can trigger these events using the AsyncioServer object, returned by awaiting
the server task.

Here is an incomplete example (please see `run_async_advanced.py` in examples for something more complete):

.. code-block:: python

    serv_coro = app.create_server(host="0.0.0.0", port=8000, return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    serv_task = asyncio.ensure_future(serv_coro, loop=loop)
    server = loop.run_until_complete(serv_task)
    server.after_start()
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        loop.stop()
    finally:
        server.before_stop()

        # Wait for server to close
        close_task = server.close()
        loop.run_until_complete(close_task)

        # Complete all tasks on the loop
        for connection in server.connections:
            connection.close_if_idle()
        server.after_stop()
