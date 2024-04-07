# ログ

Sanicはformat@@0(https://docs.python.org/3/howto/logging.html)に基づいてリクエストの異なるタイプのログ(アクセスログ、エラーログ)を行うことができます。 新しい設定を作成したい場合は、Pythonロギングに関する基本的な知識を持っている必要があります。

But, don't worry, out of the box Sanic ships with some sensible logging defaults. デバッグモードであるかどうかに応じてログをフォーマットする `AutoFormatter` を使用します。 これを後で強制する方法をお見せします。

## クイックスタート

Let's start by looking at what logging might look like in local development. このために、Sanicが提供するデフォルトのロギング設定を使用し、開発モードでSanicを実行するようにします。

.. 列::

```
デフォルト設定を使用した簡単な例は次のようになります。
```

.. 列::

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

.. 列::

```
Because we are specifically trying to look at the development logs, we will make sure to run Sanic in development mode.
```

.. 列::

````
```sh
sanic path.to.server:app --dev
```    
````

サーバーが実行されると、このようなログが表示されます。

![Sanic Logging Start](/assets/images/logging-debug-start.png)

サーバーにリクエストを送信すると、ログメッセージが出力されます。

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

## サイニックロガーの変更

.. column::

```
独自のロギング設定を使用するには、`logging.config.dictConfig` を使用するか、Sanic アプリを初期化する際に `log_config` を使用します。
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
Logging in Python is a relatively cheap operation. However, if you are serving a high number of requests and performance is a concern, all of that time logging out access logs adds up and becomes quite expensive.  

This is a good opportunity to place Sanic behind a proxy (like nginx) and to do your access logging there. You will see a *significant* increase in overall performance by disabling the `access_log`.  

For optimal production performance, it is advised to run Sanic with `debug` and `access_log` disabled: `app.run(debug=False, access_log=False)`
```

## Access logger additional parameters

Sanic provides additional parameters to the access logger.

| ログのコンテキストパラメータ | パラメータの値                              | Datatype |
| -------------- | ------------------------------------ | -------- |
| `host`         | `request.ip`                         | `str`    |
| `request`      | `request.method + " " + request.url` | `str`    |
| `status`       | `response`                           | `int`    |
| `byte`         | `len(response.body)`                 | `int`    |
| `duration`     | <calculated>                         | `float`  |

## Legacy logging

Many logging changes were introduced in Sanic 24.3. The main changes were related to logging formats. If you prefer the legacy logging format, you can use the `sanic.logging.formatter.LegacyFormatter` and `sanic.logging.formatter.LegacyAccessFormatter` formatters.
