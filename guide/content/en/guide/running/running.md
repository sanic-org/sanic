---
title: Running Sanic
---

# Running Sanic

Sanic ships with its own internal web server. Under most circumstances, this is the preferred method for deployment. In addition, you can also deploy Sanic as an ASGI app bundled with an ASGI-able web server.

## Sanic Server

The main way to run Sanic is to use the included [CLI](#sanic-cli).

```sh
sanic path.to.server:app
```

In this example, Sanic is instructed to look for a python module called `path.to.server`. Inside of that module, it will look for a global variable called `app`, which should be an instance of `Sanic(...)`.

```python
# ./path/to/server.py
from sanic import Sanic, Request, json

app = Sanic("TestApp")

@app.get("/")
async def handler(request: Request):
    return json({"foo": "bar"})
```

You may also dropdown to the [lower level API](#low-level-apprun) to call `app.run` as a script. However, if you choose this option you should be more comfortable handling issues that may arise with `multiprocessing`.

### Workers

.. column::

    By default, Sanic runs a main process and a single worker process (see [worker manager](./manager.md) for more details).

    To crank up the juice, just specify the number of workers in the run arguments.

.. column::

    ```sh
    sanic server:app --host=0.0.0.0 --port=1337 --workers=4
    ```

Sanic will automatically spin up multiple processes and route traffic between them. We recommend as many workers as you have available processors.

.. column::

    The easiest way to get the maximum CPU performance is to use the `--fast` option. This will automatically run the maximum number of workers given the system constraints.

    *Added in v21.12*

.. column::

    ```sh
    sanic server:app --host=0.0.0.0 --port=1337 --fast
    ```

In version 22.9, Sanic introduced a new worker manager to provide more consistency and flexibility between development and production servers. Read [about the manager](./manager.md) for more details about workers.

.. column::

    If you only want to run Sanic with a single process, specify `single_process` in the run arguments. This means that auto-reload, and the worker manager will be unavailable.

    *Added in v22.9*

.. column::

    ```sh
    sanic server:app --host=0.0.0.0 --port=1337 --single-process
    ```

### Running via command

#### Sanic CLI

Use `sanic --help` to see all the options.


.. attrs::
    :title: Sanic CLI help output
    :class: details

    ```text
    $ sanic --help

       ▄███ █████ ██      ▄█▄      ██       █   █   ▄██████████
      ██                 █   █     █ ██     █   █  ██
       ▀███████ ███▄    ▀     █    █   ██   ▄   █  ██
                   ██  █████████   █     ██ █   █  ▄▄
      ████ ████████▀  █         █  █       ██   █   ▀██ ███████

     To start running a Sanic application, provide a path to the module, where
     app is a Sanic() instance:

         $ sanic path.to.server:app

     Or, a path to a callable that returns a Sanic() instance:

         $ sanic path.to.factory:create_app --factory

     Or, a path to a directory to run as a simple HTTP server:

         $ sanic ./path/to/static --simple

    Required
    ========
      Positional:
        module              Path to your Sanic app. Example: path.to.server:app
                            If running a Simple Server, path to directory to serve. Example: ./

    Optional
    ========
      General:
        -h, --help          show this help message and exit
        --version           show program's version number and exit

      Application:
        --factory           Treat app as an application factory, i.e. a () -> <Sanic app> callable
        -s, --simple        Run Sanic as a Simple Server, and serve the contents of a directory
                            (module arg should be a path)
        --inspect           Inspect the state of a running instance, human readable
        --inspect-raw       Inspect the state of a running instance, JSON output
        --trigger-reload    Trigger worker processes to reload
        --trigger-shutdown  Trigger all processes to shutdown

      HTTP version:
        --http {1,3}        Which HTTP version to use: HTTP/1.1 or HTTP/3. Value should
                            be either 1, or 3. [default 1]
        -1                  Run Sanic server using HTTP/1.1
        -3                  Run Sanic server using HTTP/3

      Socket binding:
        -H HOST, --host HOST
                            Host address [default 127.0.0.1]
        -p PORT, --port PORT
                            Port to serve on [default 8000]
        -u UNIX, --unix UNIX
                            location of unix socket

      TLS certificate:
        --cert CERT         Location of fullchain.pem, bundle.crt or equivalent
        --key KEY           Location of privkey.pem or equivalent .key file
        --tls DIR           TLS certificate folder with fullchain.pem and privkey.pem
                            May be specified multiple times to choose multiple certificates
        --tls-strict-host   Only allow clients that send an SNI matching server certs

      Worker:
        -w WORKERS, --workers WORKERS
                            Number of worker processes [default 1]
        --fast              Set the number of workers to max allowed
        --single-process    Do not use multiprocessing, run server in a single process
        --legacy            Use the legacy server manager
        --access-logs       Display access logs
        --no-access-logs    No display access logs

      Development:
        --debug             Run the server in debug mode
        -r, --reload, --auto-reload
                            Watch source directory for file changes and reload on changes
        -R PATH, --reload-dir PATH
                            Extra directories to watch and reload on changes
        -d, --dev           debug + auto reload
        --auto-tls          Create a temporary TLS certificate for local development (requires mkcert or trustme)

      Output:
        --coffee            Uhm, coffee?
        --no-coffee         No uhm, coffee?
        --motd              Show the startup display
        --no-motd           No show the startup display
        -v, --verbosity     Control logging noise, eg. -vv or --verbosity=2 [default 0]
        --noisy-exceptions  Output stack traces for all exceptions
        --no-noisy-exceptions
                            No output stack traces for all exceptions

    ```


#### As a module

.. column::

    Sanic applications can also be called directly as a module.

.. column::

    ```bash
    python -m sanic server.app --host=0.0.0.0 --port=1337 --workers=4
    ```

#### Using a factory

A very common solution is to develop your application *not* as a global variable, but instead using the factory pattern. In this context, "factory" means a function that returns an instance of `Sanic(...)`.

.. column::

    Suppose that you have this in your `server.py`

.. column::

    ```python
    from sanic import Sanic

    def create_app() -> Sanic:
        app = Sanic("MyApp")

        return app
    ```


.. column::

    You can run this application now by referencing it in the CLI explicitly as a factory:

.. column::

    ```sh
    sanic server:create_app --factory
    ```
    Or, explicitly like this:
    ```sh
    sanic "server:create_app()"
    ```
    Or, implicitly like this:
    ```sh
    sanic server:create_app
    ```

    *Implicit command added in v23.3*

### Low level `app.run`

When using `app.run` you will just call your Python file like any other script.

.. column::

    `app.run` must be properly nested inside of a name-main block.

.. column::

    ```python
    # server.py
    app = Sanic("MyApp")

    if __name__ == "__main__":
        app.run()
    ```



.. danger:: 

    Be *careful* when using this pattern. A very common mistake is to put too much logic inside of the `if __name__ == "__main__":` block.

    🚫 This is a mistake

    ```python
    from sanic import Sanic
    from my.other.module import bp

    app = Sanic("MyApp")

    if __name__ == "__main__":
        app.blueprint(bp)
        app.run()
    ```

    If you do this, your [blueprint](../best-practices/blueprints.md) will not be attached to your application. This is because the `__main__` block will only run on Sanic's main worker process, **NOT** any of its [worker processes](../deployment/manager.md). This goes for anything else that might impact your application (like attaching listeners, signals, middleware, etc). The only safe operations are anything that is meant for the main process, like the `app.main_*` listeners.

    Perhaps something like this is more appropriate:

    ```python
    from sanic import Sanic
    from my.other.module import bp

    app = Sanic("MyApp")

    if __name__ == "__mp_main__":
        app.blueprint(bp)
    elif __name__ == "__main__":
        app.run()
    ```


To use the low-level `run` API, after defining an instance of `sanic.Sanic`, we can call the run method with the following keyword arguments:

|       Parameter       |     Default      |                                           Description                                     |
| :-------------------: | :--------------: | :---------------------------------------------------------------------------------------- |
|  **host**             | `"127.0.0.1"`    | Address to host the server on.                                                            |
|  **port**             | `8000`           | Port to host the server on.                                                               |
|  **unix**             | `None`           | Unix socket name to host the server on (instead of TCP).                                  |
|  **dev**              | `False`          | Equivalent to `debug=True` and `auto_reload=True`.                                        |
|  **debug**            | `False`          | Enables debug output (slows server).                                                      |
|  **ssl**              | `None`           | SSLContext for SSL encryption of worker(s).                                               |
|  **sock**             | `None`           | Socket for the server to accept connections from.                                         |
|  **workers**          | `1`              | Number of worker processes to spawn. Cannot be used with fast.                            |
|  **loop**             | `None`           | An asyncio-compatible event loop. If none is specified, Sanic creates its own event loop. |
|  **protocol**         | `HttpProtocol`   | Subclass of asyncio.protocol.                                                             |
|  **version**          | `HTTP.VERSION_1` | The HTTP version to use (`HTTP.VERSION_1` or `HTTP.VERSION_3`).                           |
|  **access_log**       | `True`           | Enables log on handling requests (significantly slows server).                            |
|  **auto_reload**      | `None`           | Enables auto-reload on the source directory.                                              |
|  **reload_dir**       | `None`           | A path or list of paths to directories the auto-reloader should watch.                    |
|  **noisy_exceptions** | `None`           | Whether to set noisy exceptions globally. None means leave as default.                    |
|  **motd**             | `True`           | Whether to display the startup message.                                                   |
|  **motd_display**     | `None`           | A dict with extra key/value information to display in the startup message                 |
|  **fast**             | `False`          | Whether to maximize worker processes.  Cannot be used with workers.                       |
|  **verbosity**        | `0`              | Level of logging detail. Max is 2.                                                        |
|  **auto_tls**         | `False`          | Whether to auto-create a TLS certificate for local development. Not for production.       |
|  **single_process**   | `False`          | Whether to run Sanic in a single process.                                                 |

.. column::

    For example, we can turn off the access log in order to increase performance, and bind to a custom host and port.

.. column::

    ```python
    # server.py
    app = Sanic("MyApp")

    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=1337, access_log=False)
    ```


.. column::

    Now, just execute the python script that has `app.run(...)`

.. column::

    ```sh
    python server.py
    ```

For a slightly more advanced implementation, it is good to know that `app.run` will call `app.prepare` and `Sanic.serve` under the hood.

.. column::

    Therefore, these are equivalent:

.. column::

    ```python
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=1337, access_log=False)
    ```
    ```python
    if __name__ == "__main__":
        app.prepare(host='0.0.0.0', port=1337, access_log=False)
        Sanic.serve()
    ```

.. column::

    This can be useful if you need to bind your appliction(s) to multiple ports.

.. column::

    ```python
    if __name__ == "__main__":
        app1.prepare(host='0.0.0.0', port=9990)
        app1.prepare(host='0.0.0.0', port=9991)
        app2.prepare(host='0.0.0.0', port=5555)
        Sanic.serve()
    ```

### Sanic Simple Server

.. column::

    Sometimes you just have a directory of static files that need to be served. This especially can be handy for quickly standing up a localhost server. Sanic ships with a Simple Server, where you only need to point it at a directory.

.. column::

    ```sh
    sanic ./path/to/dir --simple
    ```


.. column::

    This could also be paired with auto-reloading.

.. column::

    ```sh
    sanic ./path/to/dir --simple --reload --reload-dir=./path/to/dir
    ```

*Added in v21.6*

### HTTP/3

Sanic server offers HTTP/3 support using [aioquic](https://github.com/aiortc/aioquic). This **must** be installed to use HTTP/3:

```sh
pip install sanic aioquic
```

```sh
pip install sanic[http3]
```

To start HTTP/3, you must explicitly request it when running your application.

.. column::

    ```sh
    sanic path.to.server:app --http=3
    ```

    ```sh
    sanic path.to.server:app -3
    ```

.. column::

    ```python
    app.run(version=3)
    ```

To run both an HTTP/3 and HTTP/1.1 server simultaneously, you can use [application multi-serve](../release-notes/v22.3.html#application-multi-serve) introduced in v22.3. This will automatically add an [Alt-Svc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Alt-Svc) header to your HTTP/1.1 requests to let the client know that it is also available as HTTP/3.


.. column::

    ```sh
    sanic path.to.server:app --http=3 --http=1
    ```

    ```sh
    sanic path.to.server:app -3 -1
    ```

.. column::

    ```python
    app.prepare(version=3)
    app.prepare(version=1)
    Sanic.serve()
    ```

Because HTTP/3 requires TLS, you cannot start a HTTP/3 server without a TLS certificate. You should [set it up yourself](../how-to/tls.html) or use `mkcert` if in `DEBUG` mode. Currently, automatic TLS setup for HTTP/3 is not compatible with `trustme`. See [development](./development.md) for more details.

*Added in v22.6*

## ASGI

Sanic is also ASGI-compliant. This means you can use your preferred ASGI webserver to run Sanic. The three main implementations of ASGI are [Daphne](http://github.com/django/daphne), [Uvicorn](https://www.uvicorn.org/), and [Hypercorn](https://pgjones.gitlab.io/hypercorn/index.html).


.. warning:: 

    Daphne does not support the ASGI `lifespan` protocol, and therefore cannot be used to run Sanic. See [Issue #264](https://github.com/django/daphne/issues/264) for more details.



Follow their documentation for the proper way to run them, but it should look something like:

```sh
uvicorn myapp:app
```
```sh
hypercorn myapp:app
```

A couple things to note when using ASGI:

1. When using the Sanic webserver, websockets will run using the `websockets` package. In ASGI mode, there is no need for this package since websockets are managed in the ASGI server. 
2. The ASGI lifespan protocol <https://asgi.readthedocs.io/en/latest/specs/lifespan.html>, supports only two server events: startup and shutdown. Sanic has four: before startup, after startup, before shutdown, and after shutdown. Therefore, in ASGI mode, the startup and shutdown events will run consecutively and not actually around the server process beginning and ending (since that is now controlled by the ASGI server). Therefore, it is best to use `after_server_start` and `before_server_stop`.

### Trio

Sanic has experimental support for running on Trio with:

```sh
hypercorn -k trio myapp:app
```

## Gunicorn

[Gunicorn](http://gunicorn.org/) ("Green Unicorn") is a WSGI HTTP Server for UNIX based operating systems. It is a pre-fork worker model ported from Ruby’s Unicorn project.

In order to run Sanic application with Gunicorn, you need to use it with the adapter from [uvicorn](https://www.uvicorn.org/). Make sure uvicorn is installed and run it with `uvicorn.workers.UvicornWorker` for Gunicorn worker-class argument:

```sh
gunicorn myapp:app --bind 0.0.0.0:1337 --worker-class uvicorn.workers.UvicornWorker
```

See the [Gunicorn Docs](http://docs.gunicorn.org/en/latest/settings.html#max-requests) for more information.


.. warning:: 

    It is generally advised to not use `gunicorn` unless you need it. The Sanic Server is primed for running Sanic in production. Weigh your considerations carefully before making this choice. Gunicorn does provide a lot of configuration options, but it is not the best choice for getting Sanic to run at its fastest.



## Performance considerations

.. column::

    When running in production, make sure you turn off `debug`.

.. column::

    ```sh
    sanic path.to.server:app
    ```


.. column::

    Sanic will also perform fastest if you turn off `access_log`.

    If you still require access logs, but want to enjoy this performance boost, consider using [Nginx as a proxy](./nginx.md), and letting that handle your access logging. It will be much faster than anything Python can handle.

.. column::

    ```sh
    sanic path.to.server:app --no-access-logs
    ```

