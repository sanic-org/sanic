# Deploying

Deploying Sanic is very simple using one of three options: the inbuilt webserver,
an [ASGI webserver](https://asgi.readthedocs.io/en/latest/implementations.html), or `gunicorn`.
It is also very common to place Sanic behind a reverse proxy, like `nginx`. 

## Running via Sanic webserver

After defining an instance of `sanic.Sanic`, we can call the `run` method with the following
keyword arguments:

- `host` *(default `"127.0.0.1"`)*: Address to host the server on.
- `port` *(default `8000`)*: Port to host the server on.
- `debug` *(default `False`)*: Enables debug output (slows server).
- `ssl` *(default `None`)*: `SSLContext` for SSL encryption of worker(s).
- `sock` *(default `None`)*: Socket for the server to accept connections from.
- `workers` *(default `1`)*: Number of worker processes to spawn.
- `loop` *(default `None`)*: An `asyncio`-compatible event loop. If none is
                             specified, Sanic creates its own event loop.
- `protocol` *(default `HttpProtocol`)*: Subclass
  of
  [asyncio.protocol](https://docs.python.org/3/library/asyncio-protocol.html#protocol-classes).
- `access_log` *(default `True`)*: Enables log on handling requests (significantly slows server).

```python
app.run(host='0.0.0.0', port=1337, access_log=False)
```

In the above example, we decided to turn off the access log in order to increase performance.

### Workers

By default, Sanic listens in the main process using only one CPU core. To crank
up the juice, just specify the number of workers in the `run` arguments.

```python
app.run(host='0.0.0.0', port=1337, workers=4)
```

Sanic will automatically spin up multiple processes and route traffic between
them. We recommend as many workers as you have available cores.

### Running via command

If you like using command line arguments, you can launch a Sanic webserver by
executing the module. For example, if you initialized Sanic as `app` in a file
named `server.py`, you could run the server like so:

`python -m sanic server.app --host=0.0.0.0 --port=1337 --workers=4`

With this way of running sanic, it is not necessary to invoke `app.run` in your
Python file. If you do, make sure you wrap it so that it only executes when
directly run by the interpreter.

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, workers=4)
```

## Running via ASGI

Sanic is also ASGI-compliant. This means you can use your preferred ASGI webserver
to run Sanic. The three main implementations of ASGI are
[Daphne](http://github.com/django/daphne), [Uvicorn](https://www.uvicorn.org/),
and [Hypercorn](https://pgjones.gitlab.io/hypercorn/index.html).

Follow their documentation for the proper way to run them, but it should look
something like:

```
daphne myapp:app
uvicorn myapp:app
hypercorn myapp:app
```

A couple things to note when using ASGI:

1. When using the Sanic webserver, websockets will run using the [`websockets`](https://websockets.readthedocs.io/) package. In ASGI mode, there is no need for this package since websockets are managed in the ASGI server.
1. The ASGI [lifespan protocol](https://asgi.readthedocs.io/en/latest/specs/lifespan.html) supports
only two server events: startup and shutdown. Sanic has four: before startup, after startup, 
before shutdown, and after shutdown. Therefore, in ASGI mode, the startup and shutdown events will 
run consecutively and not actually around the server process beginning and ending (since that 
is now controlled by the ASGI server). Therefore, it is best to use `after_server_start` and 
`before_server_stop`.
1. ASGI mode is still in "beta" as of Sanic v19.6.

## Running via Gunicorn

[Gunicorn](http://gunicorn.org/) ‘Green Unicorn’ is a WSGI HTTP Server for UNIX.
It’s a pre-fork worker model ported from Ruby’s Unicorn project.

In order to run Sanic application with Gunicorn, you need to use the special `sanic.worker.GunicornWorker`
for Gunicorn `worker-class` argument:

```
gunicorn myapp:app --bind 0.0.0.0:1337 --worker-class sanic.worker.GunicornWorker
```

If your application suffers from memory leaks, you can configure Gunicorn to gracefully restart a worker
after it has processed a given number of requests. This can be a convenient way to help limit the effects
of the memory leak.

See the [Gunicorn Docs](http://docs.gunicorn.org/en/latest/settings.html#max-requests) for more information.

## Other deployment considerations

### Running behind a reverse proxy

Sanic can be used with a reverse proxy (e.g. nginx). There's a simple example of nginx configuration:

```
server {
  listen 80;
  server_name example.org;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

If you want to get real client ip, you should configure `X-Real-IP` and `X-Forwarded-For` HTTP headers and set `app.config.PROXIES_COUNT` to `1`; see the configuration page for more information.

### Disable debug logging for performance

To improve the performance add `debug=False` and `access_log=False` in the `run` arguments.

```python
app.run(host='0.0.0.0', port=1337, workers=4, debug=False, access_log=False)
```

Running via Gunicorn you can set Environment variable `SANIC_ACCESS_LOG="False"`

```
env SANIC_ACCESS_LOG="False" gunicorn myapp:app --bind 0.0.0.0:1337 --worker-class sanic.worker.GunicornWorker --log-level warning
```

Or you can rewrite app config directly

```python
app.config.ACCESS_LOG = False
```

### Asynchronous support and sharing the loop

This is suitable if you *need* to share the Sanic process with other applications, in particular the `loop`.
However, be advised that this method does not support using multiple processes, and is not the preferred way
to run the app in general.

Here is an incomplete example (please see `run_async.py` in examples for something more practical):

```python
server = app.create_server(host="0.0.0.0", port=8000, return_asyncio_server=True)
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(server)
loop.run_forever()
```