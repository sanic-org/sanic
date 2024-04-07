# 日志记录

Sanic 允许您根据[Python log, 错误日志](https://docs.python.org/3/howto/logging.html)对请求进行不同类型的日志(访问日志, 错误日志)。 如果您想要创建一个新的配置，您应该在 Python 日志记录中获得一些基本知识。

But, don't worry, out of the box Sanic ships with some sensible logging defaults. 在方框中，它使用一个 `AutoFormatter` 来格式化日志，取决于您是否处于调试模式。 我们将告诉你如何稍后强制这个操作。

## 快速开始

Let's start by looking at what logging might look like in local development. 为此，我们将使用 Sanic 提供的默认日志配置，并确保在开发模式中运行 Sanic。

.. 列:

```
一个使用默认设置的简单示例就是这样：
```

.. 列:

````
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
````

.. 列:

```
Because we are specifically trying to look at the development logs, we will make sure to run Sanic in development mode.
```

.. 列:

````
```sh
sanic path.to.server:app --dev
```    
````

在服务器运行后，你应该看到像这样的日志。

![Sanic Logging Start](/assets/images/logging-debug-start.png)

您可以向服务器发送请求，它将打印日志消息。

![Sanic Logging Access](/assets/images/logging-debug-access.png)

Some important points to note:

- The default log level in **production** mode is `INFO`.
- The default log level in **debug** mode is `DEBUG`.
- When in **debug** mode, the log messages will not have a timestamp (except on access logs).
- Sanic will try to colorize the logs if the terminal supports it. If you are running in Docker with docker-compose, you may need to set `tty: true` in your `docker-compose.yml` file to see the colors.

## Sanic's loggers

Out of the box, Sanic ships with five loggers:

| **Logger Name**    | **Use Case**                                   |
| ------------------ | ---------------------------------------------- |
| `sanic.root`       | Used to log internal messages. |
| `sanic.error`      | Used to log error logs.        |
| `sanic.access`     | Used to log access logs.       |
| `sanic.server`     | Used to log server logs.       |
| `sanic.websockets` | Used to log websocket logs.    |

.. column::

```
If you want to use these loggers yourself, you can import them from `sanic.log`.
```

.. column::

````
```python
from sanic.log import logger, error_logger, access_logger, server_logger, websockets_logger

logger.info('This is a root logger message')
```
````

.. warning::

```
Feel free to use the root logger and the error logger yourself. But, you probably don't want to use the access logger, server logger, or websockets logger directly. These are used internally by Sanic and are configured to log in a specific way. If you want to change the way these loggers log, you should change the logging configuration.
```

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

## 正在更改 Sanic logger

.. column::

```
要使用您自己的日志配置，只需使用 `logging.config.dictConfig`，或通过 `log_config` 来初始化Sanic 应用程序。
```

.. column::

````
```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
    app.run(access_log=False)
```
````

.. column::

```
But, what if you do not want to control the logging completely, just change the formatter for example? Here, we will import the default logging config and modify only the parts that we want to force (for example) to use the `ProdFormatter` all of the time.
```

.. column::

````
```python
from sanic.log import LOGGING_CONFIG_DEFAULTS

LOGGING_CONFIG_DEFAULTS['formatters']['generic']['class'] = 'sanic.logging.formatter.ProdFormatter'
LOGGING_CONFIG_DEFAULTS['formatters']['access']['class'] = 'sanic.logging.formatter.ProdAccessFormatter'

app = Sanic('logging_example', log_config=LOGGING_CONFIG_DEFAULTS)
```
````

.. tip:: FYI

```
在 Python 中登录是一个相对便宜的操作。 然而，如果你正在满足大量的请求，执行情况令人关切。 所有这些时间都增加了访问日志，费用都很高。  

这是一个很好的机会，可以将 Sanic 放置在代理背后(如nginx)，并在那里进行访问日志。 您将通过禁用 `access_log` 来看到整体性能的大幅提高。  

为了最佳生产性能，建议运行 Sanic，禁用了 `debug` 和 `access_log` ：`app.run(debug=False, access_log=False)`
```

## Access logger additional parameters

Sanic provides additional parameters to the access logger.

| 日志上下文参数    | 参数值                                 | Datatype |
| ---------- | ----------------------------------- | -------- |
| `host`     | `request.ip`                        | `str`    |
| `request`  | `request.methods + " + request.url` | `str`    |
| `status`   | `response`                          | `int`    |
| `byte`     | `len(response.body)`                | `int`    |
| `duration` | <calculated>                        | `float`  |

## Legacy logging

Many logging changes were introduced in Sanic 24.3. The main changes were related to logging formats. If you prefer the legacy logging format, you can use the `sanic.logging.formatter.LegacyFormatter` and `sanic.logging.formatter.LegacyAccessFormatter` formatters.
