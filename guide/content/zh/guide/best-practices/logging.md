# 日志记录

Sanic 允许您根据[Python log, 错误日志](https://docs.python.org/3/howto/logging.html)对请求进行不同类型的日志(访问日志, 错误日志)。 如果您想要创建一个新的配置，您应该在 Python 日志记录中获得一些基本知识。

## 快速开始

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

if __name__ == "__main__":
  app.run(debug=True, access_log=True)
```
````

在服务器运行后，你应该看到像这样的日志。

```text
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Starting worker [1929659]
```

您可以向服务器发送请求，它将打印日志消息。

```text
[2021-01-04 15:26:28 +0200] [1929659] [INFO] Here is your log
[2021-01-04 15:26:28 +0200] - (sanic.access)[INFO][127.0.0.1:44228]: GET http://localhost:8000/  200 -1
```

## 正在更改 Sanic logger

要使用您自己的日志配置，只需使用 `logging.config.dictConfig`，或通过 `log_config` 来初始化Sanic 应用程序。

```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
  app.run(access_log=False)
```

.. tip:: FYI

```
在 Python 中登录是一个相对便宜的操作。 然而，如果你正在满足大量的请求，执行情况令人关切。 所有这些时间都增加了访问日志，费用都很高。  

这是一个很好的机会，可以将 Sanic 放置在代理背后(如nginx)，并在那里进行访问日志。 您将通过禁用 `access_log` 来看到整体性能的大幅提高。  

为了最佳生产性能，建议运行 Sanic，禁用了 `debug` 和 `access_log` ：`app.run(debug=False, access_log=False)`
```

## 配置

Sanic默认日志配置为：`sanic.log.LOGING_CONFIG_DEFAULTS`。

.. 列:

```
有三名伐木者用于卫生系统。 如果您想要创建自己的日志配置，则必须定义：

| **日志名称** | **使用案例** |
|-----------------|-----------------------|
| `sanic。 oot` | 用于记录内部消息.
| `sanic.error` | 用于日志错误日志. |
| `sanic.access` | 用于日志访问日志
```

.. 列:

### 日志格式

除了Python提供的默认参数外(`asctime`, `levelname`, `message`)，Sanic还提供了访问日志的额外参数。

| 日志上下文参数   | 参数值                                 | Datatype |
| --------- | ----------------------------------- | -------- |
| `host`    | `request.ip`                        | `str`    |
| `request` | `request.methods + " + request.url` | `str`    |
| `status`  | `response`                          | `int`    |
| `byte`    | `len(response.body)`                | `int`    |

默认访问日志格式是：

```text
%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: %(request)s %(message)s %(status)d %(byte)d
```
