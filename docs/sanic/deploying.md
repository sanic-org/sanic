# Deploying

Deploying Sanic is made simple by the inbuilt webserver. After defining an
instance of `sanic.Sanic`, we can call the `run` method with the following
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

## Workers

By default, Sanic listens in the main process using only one CPU core. To crank
up the juice, just specify the number of workers in the `run` arguments.

```python
app.run(host='0.0.0.0', port=1337, workers=4)
```

Sanic will automatically spin up multiple processes and route traffic between
them. We recommend as many workers as you have available cores.

## Running via command

If you like using command line arguments, you can launch a Sanic server by
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

## Disable debug logging

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

## Asynchronous support
This is suitable if you *need* to share the sanic process with other applications, in particular the `loop`.
However be advised that this method does not support using multiple processes, and is not the preferred way
to run the app in general.

Here is an incomplete example (please see `run_async.py` in examples for something more practical):

```python
server = app.create_server(host="0.0.0.0", port=8000)
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(server)
loop.run_forever()
```
