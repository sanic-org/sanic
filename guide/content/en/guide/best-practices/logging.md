# Logging

Sanic allows you to do different types of logging (access log, error log) on the requests based on the [Python logging API](https://docs.python.org/3/howto/logging.html). You should have some basic knowledge on Python logging if you want to create a new configuration.

## Quick Start

.. column::

    A simple example using default settings would be like this:

.. column::

    ```python
    from sanic import Sanic
    from sanic.log import logger
    from sanic.response import text

    app = Sanic('logging_example')

    @app.route('/')
    async def test(request):
        logger.info('Here is your log')
        return text('Hello World!')

    if __name__ == "__main__":
      app.run(debug=True, access_log=True)
    ```

After the server is running, you should see logs like this.
```text
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Starting worker [1929659]
```

You can send a request to server and it will print the log messages.
```text
[2021-01-04 15:26:28 +0200] [1929659] [INFO] Here is your log
[2021-01-04 15:26:28 +0200] - (sanic.access)[INFO][127.0.0.1:44228]: GET http://localhost:8000/  200 -1
```

## Changing Sanic loggers

To use your own logging config, simply use `logging.config.dictConfig`, or pass `log_config` when you initialize Sanic app.

```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
  app.run(access_log=False)
```


.. tip:: FYI

    Logging in Python is a relatively cheap operation. However, if you are serving a high number of requests and performance is a concern, all of that time logging out access logs adds up and becomes quite expensive.  

    This is a good opportunity to place Sanic behind a proxy (like nginx) and to do your access logging there. You will see a *significant* increase in overall performance by disabling the `access_log`.  

    For optimal production performance, it is advised to run Sanic with `debug` and `access_log` disabled: `app.run(debug=False, access_log=False)`


## Configuration

Sanic's default logging configuration is: `sanic.log.LOGGING_CONFIG_DEFAULTS`.

.. column::

    There are three loggers used in sanic, and must be defined if you want to create your own logging configuration:

    | **Logger Name** | **Use Case**                  |
    |-----------------|-------------------------------|
    | `sanic.root`    | Used to log internal messages. |
    | `sanic.error`   | Used to log error logs.       |
    | `sanic.access`  | Used to log access logs.      |

.. column::



### Log format

In addition to default parameters provided by Python (`asctime`, `levelname`, `message`), Sanic provides additional parameters for access logger with.

| Log Context Parameter | Parameter Value                       | Datatype |
|-----------------------|---------------------------------------|----------|
| `host`                | `request.ip`                          | `str`    |
| `request`             | `request.method + " " + request.url`  | `str`    |
| `status`              | `response`                            | `int`    |
| `byte`                | `len(response.body)`                  | `int`    |



The default access log format is:

```text
%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: %(request)s %(message)s %(status)d %(byte)d
```
