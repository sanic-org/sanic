# 例外

## 使用 Sanic 异常

有时，你只需要告诉Sanic停止执行处理程序并发送状态代码回复。 你可以为此举出一个 'SanicException' ，萨尼克将为你做其他事情。

您可以通过一个可选的 `status_code` 参数。 默认情况下，一个 SanicException 将返回一个内部服务器错误500。

```python
从 sanic.exception 导入SanicException

@app.route("/youshallnotpass")
async def no_no(request):
        raising SanicException("出了错", status_code=501)
```

Sanic提供了一些标准例外情况。 他们将自动在您的响应中提取适当的 HTTP 状态代码。 [请参阅API参考](https://sanic.readthedocs.io/enage/sanic/api_reference.html#module-sanic.exceptions) 了解更多详情。

.. 列:

```
The more common exceptions you _should_ implement yourself include:

- `BadRequest` (400)
- `Unauthorized` (401)
- `Forbidden` (403)
- `NotFound` (404)
- `ServerError` (500)
```

.. 列:

````
```python
from sanic import exceptions

@app.route("/login")
async def login(request):
    user = await some_login_func(request)
    if not user:
        raise exceptions.NotFound(
            f"Could not find user with username={request.json.username}"
        )
```
````

## 异常属性

所有萨尼克例外情况都源于“SanicException”。 该类具有几个属性，可以帮助开发者始终如一地报告他们在应用程序中的异常情况。

- `message`
- `status_code`
- 安静\`
- `headers`
- `context`
- `extra`

所有这些属性都可以在创建时传递到异常。 但前三个也可以用作我们所看到的类变量。

.. 列:

```
### `message`

`message` 属性显然控制了将会像Python中任何其他异常一样显示的消息。 尤其有用的是，您可以在类定义中设置`message`属性，以便于所有应用程序的语言标准化
```

.. 列:

````
```python
class CustomError(SanicException):
    message = "出了错误"

raising Custom错误
# 或
raw customError("用其他东西覆盖默认消息")
```
````

.. 列:

```
### `status_code`

这个属性用于设置异常时的响应代码。 这在创建习惯400系列异常时尤其有用，这些异常通常是为了对客户端提供的坏信息作出反应。
```

.. 列:

````
```python
class TeapotError(SanicException):
    status_code = 418
    message = “对不起，” 我不能酿造咖啡”

提高Teapot错误
# 或
提高TeapotError(status_code=400)
```
````

.. 列:

```
### `quiet`

默认情况下，例外情况将由 Sanic 输出到 `error_logger` 。 有时这可能是不可取的，特别是如果你在异常处理程序中使用异常来触发事件(见以下章节) 。 异常.md#handling)。您可以使用 "quiot=True" 来抑制日志输出。
```

.. 列:

````
```python
class SilentError(SanicException):
    message = "发生了什么, 但未显示在日志中。
    安静=True

引起静音错误
# 或
引起无效使用("blah blah", 安静=True)
```
````

.. 列:

```
有时候在调试时，你可能想要全局忽略`quiet=True`属性。 您可以使用 `NOISY_EXCEPIONS`

强制从 v21.12中添加的 Sanic 注销所有异常，无论这个属性如何。
```

.. 列:

````
```python
app.config.NOISY_EXCEPTIONS = True
```
````

.. 列:

```
### `headers`

使用 `SanicException` 作为创建响应的工具是超强大的。 这部分是因为你不仅可以控制 `status_code`，而且你也可以直接从异常中控制回复头部。
```

.. 列:

````
```python
class MyException(SanicException):
    headers =
      "X-Foo": "bar"
    }

raising MyException
# 或
raising InvalidUsage("blah blah", headers=leaders=
    "X-Foo": "bar"
})
```
````

.. 列:

```
### `extran`

查看[contextual explitions](./exceptions.md#contextual-exceptions)

*添加于v21.12*
```

.. 列:

````
```python
raising SanicException(..., extrade={"name": "Adam"})
```
````

.. 列:

```
### `context`

见 [contextual explositions](./exceptions.md#contextual-异常)

*添加于v21.12*
```

.. 列:

````
```python
raising SanicException(..., context={"foo": "bar"})
```
````

## 处理

通过渲染错误页自动处理异常，所以在许多情况下您不需要自己处理。 然而，如果你想要更多地控制在提出异常时做什么，你可以自己实现一个处理程序。

Sanic为此提供了一个装饰器，它不仅适用于Sanic标准例外情况，而且**任何**你的应用程序可能丢弃的例外情况。

.. 列:

```
添加处理程序的最简单方法是使用 `@app.expition()` 并传递一个或多个异常。
```

.. 列:

````
```python
from sanic.exceptions import NotFound

@app.exception(NotFound, Some CustomException)
async def ignore_404s(request, exception):
    return text("Yep, 我完全发现页面: {}".format (crequest.url))
```
````

.. 列:

```
你也可以通过捕捉"异常"来创建一个捕获器处理器。
```

.. 列:

````
```python
@app.exception(Exception)
async def catch_any thing(request, exception):
    ...
```
````

.. 列:

```
您也可以使用 `app.error_handler.add()` 添加错误处理器。
```

.. 列:

````
```python
async def server_error_handler(请求异常):
    return text("Ops, server error", status=500)

app.error_handler.add(Exception, server_error_handler)
```
````

## 内置错误处理

有三种异常模式的神秘船只：HTML、JSON和文本。 你可以在下面的[回退处理程序](#回退处理程序)部分看到他们的例子。

.. 列:

```
You can control _per route_ which format to use with the `error_format` keyword argument.

*Added in v21.9*
```

.. 列:

````
```python
@app.request("/", error_form="text")
async def handler(request):
    ...
```
````

## 自定义错误处理

在某些情况下，您可能想要将一些更多的错误处理功能添加到默认提供的功能。 在这种情况下，你可以将亚类Sanic的默认错误处理程序作为这样：

```python
from sanic.handlers import ErrorHandler

class CustomErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        ''' handles errors that have no error handlers assigned '''
        # You custom error handling logic...
        status_code = getattr(exception, "status_code", 500)
        return json({
          "error": str(exception),
          "foo": "bar"
        }, status=status_code)

app.error_handler = CustomErrorHandler()
```

## Fallback handler

Sanic带有三个回退异常处理器：

1. HTML
2. 文本
3. JSON

这些处理程序根据您的应用程序是否处于[调试模式](../running/development.md)来提供不同的详细程度。

默认情况下，Sanic将处于“自动”模式， 这意味着它将使用传入的请求和潜在的匹配处理程序来选择适当的响应格式。 例如，在浏览器中，它应该始终提供一个 HTML 错误页面。 当使用curl时，您可能会看到JSON或纯文本。

### HTML

```python
app.config.FALLBACK_ERROR_FORMAT = "html"
```

.. 列:

````
```python
app.config.DEBUG = True
``

！[Error](/assets/images/error-display-html-debug.png)
````

.. 列:

````
```python
app.config.DEBUG = False
``

！[Error](/assets/images/error-disply-html-prod.png)
````

### 文本

```python
app.config.FALLBACK_ERROR_FORMAT = “文本”
```

.. 列:

````
```python
app.config.DEBUG = True
``

```sh
curl localhost:8000/exc -i
HTTP/1。 500 服务器内部错误
内容长度：620
连接：保持存活
内容类型：text/plain； charset=utf-8

:警告：500-内部服务器错误
=================================
那段时间当那个事情打破了那个其他事情吗？ 发生了这种情况。

服务器错误：那个时候那件事情打破了那个东西吗？那就发生了。 处理路径/exc
追踪TestApp (最近一次通话时间):

  服务器错误: 那个时候那个东西打破了那个其他东西？ 发生了这种情况。
    文件 /path/to/sanic/app y, line 979, in handle_request
    response = requiring response

    file /path/to/server. y, line 16, in handler
    do_something(cause_error=True)

    files/path/to/something。 y, line 9, in do_some
    raising ServerError(
```
````

.. 列:

````
```python
app.config.DEBUG = False
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 134
connection: keep-alive
content-type: text/plain; charset=utf-8

⚠️ 500 — Internal Server Error
==============================
That time when that thing broke that other thing? That happened.
```
````

### JSON

```python
app.config.FALLBACK_ERROR_FORMAT = "json"
```

.. 列:

````
```python
app.config.DEBUG = True
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 572
connection: keep-alive
content-type: application/jso

{
  "description": "Internal Server Error",
  "status": 500,
  "message": "That time when that thing broke that other thing? That happened.",
  "path": "/exc",
  "args": {},
  "exceptions": [
    {
      "type": "ServerError",
      "exception": "That time when that thing broke that other thing? That happened.",
      "frames": [
        {
          "file": "/path/to/sanic/app.py",
          "line": 979,
          "name": "handle_request",
          "src": "response = await response"
        },
        {
          "file": "/path/to/server.py",
          "line": 16,
          "name": "handler",
          "src": "do_something(cause_error=True)"
        },
        {
          "file": "/path/to/something.py",
          "line": 9,
          "name": "do_something",
          "src": "raise ServerError("
        }
      ]
    }
  ]
}
```
````

.. 列:

````
```python
app.config.DEBUG = False
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 129
connection: keep-alive
content-type: application/json

{
  "description": "Internal Server Error",
  "status": 500,
  "message": "That time when that thing broke that other thing? That happened."
}

```
````

### 自动操作

Sanic还提供了一种猜测的选项，这种猜测可以使用后退选项。

```python
app.config.FALLBACK_ERROR_FORMAT = "自动"
```

## 上下文异常

默认异常消息简化了在整个应用程序中始终如一地提出异常的能力。

```python
class TeapotError(SanicException):
    status_code = 418
    message = “对不起，我不能酿造咖啡”

rappot错误
```

但这缺少两件事：

1. 动态和可预测的信息格式
2. 添加附加上下文到错误消息的能力 (暂时更多)

_添加于 v21.12_

使用 Sanic的一个异常，您有两个选项在运行时提供额外细节：

```python
升起TeapotError(extrade={"foo": "bar"}, context={"foo": "bar"})
```

两者之间有什么区别，何时决定使用？

- `extran` - 对象本身将**永远不**发送到生产客户端。 它仅供内部使用。 它可以用于什么？
  - 正在生成一个动态错误消息 (我们将在一分钟后看到)
  - 为记录器提供运行时间详情
  - 调试信息(在开发模式中，它会提供)
- `context` - 此对象总是\*\*总是发送给生产客户。 一般用来提供关于所发生情况的更多细节。 它可以用于什么？
  - 在 `BadRequest` 验证问题上提供替代值
  - 回答您的客户有帮助的详细信息来打开支持工单
  - 显示当前登录用户信息等状态信息

### 使用 "额外" 的动态和可预测消息

可使用 `extran`关键字参数来提起无声异常，为一个引起的异常实例提供额外信息。

```python
class TeapotError(SanicException):
    status_code = 418

    @property
    def message(self):
        return f"对不起{self.extr['name']}, 我不能让你咖啡”

raising TeapotError(extranti={"name": "Adam"})
```

新功能允许将 `extran`meta 传递给异常实例。 这可能与上面的例子一样对将动态数据传递到电文文本中特别有用。 这个“额外”信息对象 **将在 `PRODUCTION` 模式下被抑制** ，但将以`DevelopMENT` 模式显示。

.. 列:

```
**DEVELOPMENT**

![image](~@assets/images/error-extra-debug.png)
```

.. 列:

```
**PRODUCTION**

![image](~@assets/images/error-extra-prod.png)
```

### 附加“context”到错误消息

还可以用`context`的参数来提出无声异常，将预定的信息传递给用户关于所发生事件的信息。 这在创建微型服务或旨在以 JSON 格式传递错误消息的 API 时特别有用。 在这种情况下，我们想要围绕例外的某些上下文，而不仅仅是一个可解析的错误信息来返回客户端。

```python
raised TeapotError(context={"foot": "bar"})
```

这是**我们想要**总是错误传递的信息(当它可用时)。 以下是它应该看起来的样子：

.. 列:

````
**PRODUCTION**

```json
{
  "description": "I'm a teapot",
  "status": 418,
  "message": "Sorry Adam, I cannot make you coffee",
  "context": {
    "foo": "bar"
  }
}
```
````

.. 列:

````
**DEVELOPMENT**

```json
{
  "description": "I'm a teapot",
  "status": 418,
  "message": "Sorry Adam, I cannot make you coffee",
  "context": {
    "foo": "bar"
  },
  "path": "/",
  "args": {},
  "exceptions": [
    {
      "type": "TeapotError",
      "exception": "Sorry Adam, I cannot make you coffee",
      "frames": [
        {
          "file": "handle_request",
          "line": 83,
          "name": "handle_request",
          "src": ""
        },
        {
          "file": "/tmp/p.py",
          "line": 17,
          "name": "handler",
          "src": "raise TeapotError("
        }
      ]
    }
  ]
}
```
````

## 错误报告

Sanic 有一个 [signal](../advanced/signals.md#内置信号)，允许您绑定到异常报告过程。 如果您想要向 Sentry 或 Rollbar等第三方服务发送异常信息，这是有用的。 这可以通过附加错误报告处理程序来方便地完成，如下所示：

```python
@app.report_exception
async def catch_any_exception(app: Sanic, exception):
print("捕捉异常:", 异常)
```

.. 注：

```
此处理程序将被发送到一个后台任务中，**IS NOT** 将被用于操纵任何响应数据。 它仅用于伐木或报告目的。 并且不应影响您的应用程序返回错误响应客户端的能力。
```

_添加于 v23.6_

