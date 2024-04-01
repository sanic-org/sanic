# Logging

Sanic allows you to do different types of logging (access log, error log) on the requests based on the [Python logging API](https://docs.python.org/3/howto/logging.html). You should have some basic knowledge on Python logging if you want to create a new configuration.

But, don't worry, out of the box Sanic ships with some sensible logging defaults. Out of the box it uses an `AutoFormatter` that will format the logs depending upon whether you are in debug mode or not. We will show you how to force this later on.

## Quick Start

Let's start by looking at what logging might look like in local development. For this, we will use the default logging configuration that Sanic provides and make sure to run Sanic in development mode.

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
    ```

.. column::

    Because we are specifically trying to look at the development logs, we will make sure to run Sanic in development mode.

.. column::

    ```sh
    sanic path.to.server:app --dev
    ```    
    

After the server is running, you should see logs like this.

![Sanic Logging Start](/assets/images/logging-debug-start.png)

You can send a request to server and it will print the log messages.

![Sanic Logging Access](/assets/images/logging-debug-access.png)

Some important points to note:

- The default log level in **production** mode is `INFO`.
- The default log level in **debug** mode is `DEBUG`.
- When in **debug** mode, the log messages will not have a timestamp (except on access logs).
- Sanic will try to colorize the logs if the terminal supports it. If you are running in Docker with docker-compose, you may need to set `tty: true` in your `docker-compose.yml` file to see the colors.

## Sanic's loggers

Out of the box, Sanic ships with five loggers:

| **Logger Name**   | **Use Case**                  |
|-------------------|-------------------------------|
| `sanic.root`      | Used to log internal messages. |
| `sanic.error`     | Used to log error logs.       |
| `sanic.access`    | Used to log access logs.      |
| `sanic.server`    | Used to log server logs.      |
| `sanic.websockets`| Used to log websocket logs.   |

.. column::

    If you want to use these loggers yourself, you can import them from `sanic.log`.
    
.. column::

    ```python
    from sanic.log import logger, error_logger, access_logger, server_logger, websockets_logger
    
    logger.info('This is a root logger message')
    ```
    
.. warning::

    Feel free to use the root logger and the error logger yourself. But, you probably don't want to use the access logger, server logger, or websockets logger directly. These are used internally by Sanic and are configured to log in a specific way. If you want to change the way these loggers log, you should change the logging configuration.
    
## Default logging configuration

Sanic ships with a default logging configuration that is used when you do not provide your own. This configuration is stored in `sanic.log.LOGGING_CONFIG_DEFAULTS`.

```python
{
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'sanic.root': {'level': 'INFO', 'handlers': ['console']},
        'sanic.error': {
            'level': 'INFO',
            'handlers': ['error_console'],
            'propagate': True,
            'qualname': 'sanic.error'
        },
        'sanic.access': {
            'level': 'INFO',
            'handlers': ['access_console'],
            'propagate': True,
            'qualname': 'sanic.access'
        },
        'sanic.server': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
            'qualname': 'sanic.server'
        },
        'sanic.websockets': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
            'qualname': 'sanic.websockets'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': sys.stdout
        },
        'error_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': sys.stderr
        },
        'access_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'stream': sys.stdout
        }
    },
    'formatters': {
        'generic': {'class': 'sanic.logging.formatter.AutoFormatter'},
        'access': {'class': 'sanic.logging.formatter.AutoAccessFormatter'}
    }
}
```

## Changing Sanic loggers

.. column::

    To use your own logging config, simply use `logging.config.dictConfig`, or pass `log_config` when you initialize Sanic app.

.. column::

    ```python
    app = Sanic('logging_example', log_config=LOGGING_CONFIG)

    if __name__ == "__main__":
        app.run(access_log=False)
    ```

.. column::

    But, what if you do not want to control the logging completely, just change the formatter for example? Here, we will import the default logging config and modify only the parts that we want to force (for example) to use the `ProdFormatter` all of the time.
    
.. column::

    ```python
    from sanic.log import LOGGING_CONFIG_DEFAULTS
    
    LOGGING_CONFIG_DEFAULTS['formatters']['generic']['class'] = 'sanic.logging.formatter.ProdFormatter'
    LOGGING_CONFIG_DEFAULTS['formatters']['access']['class'] = 'sanic.logging.formatter.ProdAccessFormatter'
    
    app = Sanic('logging_example', log_config=LOGGING_CONFIG_DEFAULTS)
    ```


.. tip:: FYI

    Logging in Python is a relatively cheap operation. However, if you are serving a high number of requests and performance is a concern, all of that time logging out access logs adds up and becomes quite expensive.  

    This is a good opportunity to place Sanic behind a proxy (like nginx) and to do your access logging there. You will see a *significant* increase in overall performance by disabling the `access_log`.  

    For optimal production performance, it is advised to run Sanic with `debug` and `access_log` disabled: `app.run(debug=False, access_log=False)`


## Access logger additional parameters

Sanic provides additional parameters to the access logger.

| Log Context Parameter | Parameter Value                       | Datatype |
|-----------------------|---------------------------------------|----------|
| `host`                | `request.ip`                          | `str`    |
| `request`             | `request.method + " " + request.url`  | `str`    |
| `status`              | `response`                            | `int`    |
| `byte`                | `len(response.body)`                  | `int`    |
| `duration`            | <calculated>                          | `float`  |

## Legacy logging

Many logging changes were introduced in Sanic 24.3. The main changes were related to logging formats. If you prefer the legacy logging format, you can use the `sanic.logging.formatter.LegacyFormatter` and `sanic.logging.formatter.LegacyAccessFormatter` formatters.
