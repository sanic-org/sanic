# Logging


Sanic allows you to do different types of logging (access log, error log) on the requests based on the [python3 logging API](https://docs.python.org/3/howto/logging.html). You should have some basic knowledge on python3 logging if you want do create a new configuration.

### Quck Start

A simple example using default setting would be like this:

```python
from sanic import Sanic
from sanic.config import LOGGING

# The default logging handlers are ['accessStream', 'errorStream']
# but we change it to use other handlers here for demo purpose
LOGGING['loggers']['network']['handlers'] = [
    'accessTimedRotatingFile', 'errorTimedRotationgFile']

app = Sanic('test')

@app.route('/')
async def test(request):
    return response.text('Hello World!')

if __name__ == "__main__":
  app.run(log_config=LOGGING)
```

After the program starts, it will log down all the information/requests in access.log and error.log in your working directory.

And to close logging, simply assign log_config=None:

```python
if __name__ == "__main__":
  app.run(log_config=None)
```

This would skip calling logging functions when handling requests.
And you could even do further in production to gain extra speed:

```python
if __name__ == "__main__":
  # disable internal messages
  app.run(debug=False, log_config=None)
```

### Configuration

By default, log_config parameter is set to use sanic.config.LOGGING dictionary for configuration. The default configuration provides several predefined `handlers`:

- internal (using [logging.StreamHandler](https://docs.python.org/3/library/logging.handlers.html#logging.StreamHandler))<br>
  For internal information console outputs.


- accessStream (using [logging.StreamHandler](https://docs.python.org/3/library/logging.handlers.html#logging.StreamHandler))<br>
  For requests information logging in console


- errorStream (using [logging.StreamHandler](https://docs.python.org/3/library/logging.handlers.html#logging.StreamHandler))<br>
  For error message and traceback logging in console.


- accessSysLog (using [logging.handlers.SysLogHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.SysLogHandler))<br>
  For requests information logging to syslog.
  Currently supports Windows (via localhost:514), Darwin (/var/run/syslog),
  Linux (/dev/log) and FreeBSD (/dev/log).<br>
  You would not be able to access this property if the directory doesn't exist.
  (Notice that in Docker you have to enable everything by yourself)


- errorSysLog (using [logging.handlers.SysLogHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.SysLogHandler))<br>
  For error message and traceback logging to syslog.
  Currently supports Windows (via localhost:514), Darwin (/var/run/syslog),
  Linux (/dev/log) and FreeBSD (/dev/log).<br>
  You would not be able to access this property if the directory doesn't exist.
  (Notice that in Docker you have to enable everything by yourself)


- accessTimedRotatingFile (using [logging.handlers.TimedRotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler))<br>
  For requests information logging to file with daily rotation support.


- errorTimedRotatingFile (using [logging.handlers.TimedRotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler))<br>
  For error message and traceback logging to file with daily rotation support.

And `filters`:

- accessFilter (using sanic.defaultFilter.DefaultFilter)<br>
  The filter that allows only levels in `DEBUG`, `INFO`, and `NONE(0)`


- errorFilter (using sanic.defaultFilter.DefaultFilter)<br>
  The filter taht allows only levels in `WARNING`, `ERROR`, and `CRITICAL`

There are two `loggers` used in sanic, and **must be defined if you want to create your own logging configuration**:

- sanic:<br>
  Used to log internal messages.


- network:<br>
  Used to log requests from network, and any information from those requests.

#### Log format:

In addition to default parameters provided by python (asctime, levelname, message),
Sanic provides additional parameters for network logger with accessFilter:

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
