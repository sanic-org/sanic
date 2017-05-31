# Troubleshooting

## ERROR: NoneType: None in console

The message `ERROR: NoneType: None` is caused by timeout error caused by request not occuring in Keep-Alive.
There are two methods not to display a message.

* Invalidating Keep-Alive.

```python
from sanic.config import Config
Config.KEEP_ALIVE = False
```

* Setting custom protocol.

```python
from time import time
from sanic import Sanic
from sanic.response import json
from sanic.config import Config
from sanic.server import HttpProtocol
from sanic.exceptions import RequestTimeout


class CustomHttpProtocol(HttpProtocol):

    def connection_timeout(self):
        current_time = time()
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._timeout_handler = ( 
                self.loop.call_later(time_left, self.connection_timeout))
        else:
            if self._request_handler_task:
                self._request_handler_task.cancel()
            if self._total_request_size == 0:
                self.transport.close()
            else:
                exception = RequestTimeout('Request Timeout')
                self.write_error(exception)


app = Sanic()


@app.route("/")
async def handler(request):
        return json({"hello": "world"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, protocol=CustomHttpProtocol)
```
