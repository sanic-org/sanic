# 日志记录

Sanic 允许您根据[Python log, 错误日志](https://docs.python.org/3/howto/logging.html)对请求进行不同类型的日志(访问日志, 错误日志)。 如果您想要创建一个新的配置，您应该在 Python 日志记录中获得一些基本知识。

但不要担心的是，沙尼克船在箱子里有一些合理的日志缺失。 在方框中，它使用一个 `AutoFormatter` 来格式化日志，取决于您是否处于调试模式。 我们将告诉你如何稍后强制这个操作。

## 快速开始

让我们首先看看本地开发中日志可能看起来像是什么。 为此，我们将使用 Sanic 提供的默认日志配置，并确保在开发模式中运行 Sanic。

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
因为我们正在特别试图查看发展记录，因此我们将确保在发展模式中运行萨尼克。
```

.. 列:

````
```sh
sanic path.to.server:app --dev
```    
````

在服务器运行后，你应该看到像这样的日志。

![Sanic Logging Star](/assets/images/logging-debug-start.png)

您可以向服务器发送请求，它将打印日志消息。

![Sanic 日志Access](/assets/images/logging-debug-access.png)

需要注意的一些重要要点：

- **production** 模式下的默认日志级别是 `INFO` 。
- **debug** 模式下的默认日志级别是 `DEBUG` 。
- 在 **debug** 模式中，日志消息将没有时间戳(访问日志除外)。
- 如果终端支持它，Sanic将尝试对日志进行颜色。 如果你正在Docker中使用docker-compose，你可能需要在你的`docker-compose.yml`文件中设置`tty：true`来查看颜色。

## Sanic伐木者

在箱子里，有五艘伐木船的萨尼克船：

| **Logger Name**    | **使用大小写**       |
| ------------------ | --------------- |
| `sanic.root`       | 用于记录内部消息。       |
| `sanic.error`      | 用于记录错误日志。       |
| `sanic.access`     | 用于日志访问日志。       |
| `sanic.server`     | 用于记录服务器日志。      |
| `sanic.websockets` | 用于记录 Web 套接字日志。 |

.. 列:

```
如果你想要自己使用这些记录器，你可以从 `sanic.log`中导入它们。
```

.. 列:

````
```python
来自sanic.log logger, error_logger, access_logger, server_logger, websockets_logger

logger.info('这是一个root logger message')
```
````

.. 警告：:

```
请随时使用您自己的Root日志和错误日志。 但您可能不想直接使用访问日志、服务器记录器或Websockets记录器。 这些是由 Sanic 内部使用的，并被配置为以特定方式登录。 如果你想要更改这些日志记录的方式，你应该更改日志的配置。
```

## 默认日志配置

当您不提供自己的时候，默认日志配置为 Sanic 飞船。 此配置存储在 `sanic.log.LOGGING_CONFIG_DEFAULTS` 中。

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

.. 列:

```
要使用您自己的日志配置，只需使用 `logging.config.dictConfig`，或通过 `log_config` 来初始化Sanic 应用程序。
```

.. 列:

````
```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
    app.run(access_log=False)
```
````

.. 列:

```
但是，如果你不想完全控制日志记录, 那么如何改变格式化程序？ 在这里，我们将导入默认的日志配置，并且只修改我们想要随时使用 "ProdFormatter" 的部件。
```

.. 列:

````
```python
from sanic.log import LOGING_CONFIGG_DEFAULTS

LOGING_CONFIG_DEFAULTS ['formations']['generic']['class'] = 'sanic.logging.formter.ProdFormatter'
LOGING_CONFIG_DEFAULTS['格式']['access']['class'] = 'sanic.logging.form.ter.ProdAccessFormatter'

app = Sanic('logging_example', log_config=LOGING_CONFIG_FAULTS)
```
````

.. tip:: FYI

```
在 Python 中登录是一个相对便宜的操作。 然而，如果你正在满足大量的请求，执行情况令人关切。 所有这些时间都增加了访问日志，费用都很高。  

这是一个很好的机会，可以将 Sanic 放置在代理背后(如nginx)，并在那里进行访问日志。 您将通过禁用 `access_log` 来看到整体性能的大幅提高。  

为了最佳生产性能，建议运行 Sanic，禁用了 `debug` 和 `access_log` ：`app.run(debug=False, access_log=False)`
```

## 访问记录器附加参数

Sanic 为访问日志提供额外参数。

| 日志上下文参数   | 参数值                                 | Datatype |
| --------- | ----------------------------------- | -------- |
| `host`    | `request.ip`                        | `str`    |
| `request` | `request.methods + " + request.url` | `str`    |
| `status`  | `response`                          | `int`    |
| `byte`    | `len(response.body)`                | `int`    |
| `持续时间`    | <calculated>                        | `float`  |

## 旧日志记录

Sanic 24.3引入了许多伐木变化。 主要的变动与伐木格式有关。 如果你喜欢旧版日志格式，你可以使用 `sanic.logging.formter.LegacyFormatter` 和 `sanic.logging.formter.LegacyAccessFormatter` 格式。
