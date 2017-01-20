# Deploying

Deploying Sanic is made simple by the inbuilt webserver. After defining an
instance of `sanic.Sanic`, we can call the `run` method with the following
keyword arguments:

- `host` *(default `"127.0.0.1"`)*: Address to host the server on.
- `port` *(default `8000`)*: Port to host the server on.
- `debug` *(default `False`)*: Enables debug output (slows server).
- `before_start` *(default `None`)*: Function or list of functions to be executed
                           before the server starts accepting connections.
- `after_start` *(default `None`)*: Function or list of functions to be executed
                    after the server starts accepting connections.
- `before_stop` *(default `None`)*: Function or list of functions to be
                    executed when a stop signal is received before it is
                    respected.
- `after_stop` *(default `None`)*: Function or list of functions to be executed
                    when all requests are complete.
- `ssl` *(default `None`)*: `SSLContext` for SSL encryption of worker(s).
- `sock` *(default `None`)*: Socket for the server to accept connections from.
- `workers` *(default `1`)*: Number of worker processes to spawn.
- `loop` *(default `None`)*: An `asyncio`-compatible event loop. If none is
                             specified, Sanic creates its own event loop.
- `protocol` *(default `HttpProtocol`)*: Subclass
  of
  [asyncio.protocol](https://docs.python.org/3/library/asyncio-protocol.html#protocol-classes).

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

**Previous:** [Request Data](request_data.md)

**Next:** [Static Files](static_files.md)
