# Logging


Sanic allows you to do different types of logging (access log, error log) on the requests based on the [python3 logging API](https://docs.python.org/3/howto/logging.html). You should have some basic knowledge on python3 logging if you want to create a new configuration.

### Quick Start

A simple example using default settings would be like this:

```python
from sanic import Sanic
from sanic.log import logger
from sanic.response import text

app = Sanic('test')

@app.route('/')
async def test(request):
    logger.info('Here is your log')
    return text('Hello World!')

if __name__ == "__main__":
  app.run(debug=True, access_log=True)
```

After the server is running, you can see some messages looks like:
```
[2018-11-06 21:16:53 +0800] [24622] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2018-11-06 21:16:53 +0800] [24667] [INFO] Starting worker [24667]
```

You can send a request to server and it will print the log messages:
```
[2018-11-06 21:18:53 +0800] [25685] [INFO] Here is your log
[2018-11-06 21:18:53 +0800] - (sanic.access)[INFO][127.0.0.1:57038]: GET http://localhost:8000/  200 12
```

To use your own logging config, simply use `logging.config.dictConfig`, or
pass `log_config` when you initialize `Sanic` app:

```python
app = Sanic('test', log_config=LOGGING_CONFIG)
```

And to close logging, simply assign access_log=False:

```python
if __name__ == "__main__":
  app.run(access_log=False)
```

This would skip calling logging functions when handling requests.
And you could even do further in production to gain extra speed:

```python
if __name__ == "__main__":
  # disable debug messages
  app.run(debug=False, access_log=False)
```

### Configuration

By default, log_config parameter is set to use sanic.log.LOGGING_CONFIG_DEFAULTS dictionary for configuration.

There are three `loggers` used in sanic, and **must be defined if you want to create your own logging configuration**:

- sanic.root:<br>
  Used to log internal messages.

- sanic.error:<br>
  Used to log error logs.

- sanic.access:<br>
  Used to log access logs.

#### Log format:

In addition to default parameters provided by python (asctime, levelname, message),
Sanic provides additional parameters for access logger with:

- host (str)<br>
  request.ip


- request (str)<br>
  request.method + " " + request.url


- status (int)<br>
  response.status


- byte (int)<br>
  len(response.body)


The default access log format is 
```python
%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: %(request)s %(message)s %(status)d %(byte)d
```
