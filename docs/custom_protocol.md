# Custom Protocol

You can change the behavior of protocol by using custom protocol.
If you want to use custom protocol, you should put subclass of [protocol class](https://docs.python.org/3/library/asyncio-protocol.html#protocol-classes) in the protocol keyword argument of `sanic.run()`. The constructor of custom protocol class gets following keyword arguments from Sanic.

* loop
`loop` is an asyncio compatible event loop.

* connections
`connections` is a `set object`  to  store protocol objects.
When Sanic receives `SIGINT` or `SIGTERM`, Sanic executes `protocol.close_if_idle()` for a `protocol objects` stored in connections.

* signal
`signal` is a `sanic.server.Signal object` with `stopped attribute`.
When Sanic receives `SIGINT` or `SIGTERM`, `signal.stopped` becomes `True`.

* request_handler
`request_handler` is a coroutine that takes a `sanic.request.Request` object and a `response callback` as arguments.

* error_handler
`error_handler` is a `sanic.exceptions.Handler` object.

* request_timeout
`request_timeout` is seconds for timeout.

* request_max_size
`request_max_size` is bytes of max request size.

## Example

```python
from sanic import Sanic
from sanic.server import HttpProtocol
from sanic.response import text

app = Sanic(__name__)


class CustomHttpProtocol(HttpProtocol):

    def __init__(self, *, loop, request_handler, error_handler,
                 signal, connections, request_timeout, request_max_size):
        super().__init__(
            loop=loop, request_handler=request_handler,
            error_handler=error_handler, signal=signal,
            connections=connections, request_timeout=request_timeout,
            request_max_size=request_max_size)

    def write_response(self, response):
        if isinstance(response, str):
            response = text(response)
        self.transport.write(
            response.output(self.request.version)
        )
        self.transport.close()


@app.route('/')
async def string(request):
    return 'string'


@app.route('/1')
async def response(request):
    return text('response')

app.run(host='0.0.0.0', port=8000, protocol=CustomHttpProtocol)
```
