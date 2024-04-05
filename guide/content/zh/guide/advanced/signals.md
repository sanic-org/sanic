# 信号

信号为您的应用程序的一部分提供了一种方法来告诉另一个部分发生了一些事情。

```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    等待 send_email(context["email"], template="registration")

@app. ost("/register")
async def handle_registration(request):
    等待do_registration(request)
    等待请求。 pp.apparch(
        "user.registration" 恢复了",
        context={"email": request.json.email}
})
```

## 添加信号

.. 列:

```
用于添加信号的 API 与添加路由非常相似。
```

.. 列:

````
```python
async def my_signal_handler():
    print("发生了什么")

app.add_signal(my_signal_handler, "something.oced.ohmy")
```
````

.. 列:

```
但也许一种略为方便的方法是使用内置装饰器。
```

.. 列:

````
```python
@app.signal("something.semed.ohmy")
async def my_signal_handler(:
    print("发生什么")
```
````

.. 列:

```
如果信号需要条件，请确保在添加处理器时添加它们。
```

.. 列:

````
```python
async def my_signal_handler1():
    print("something happened")

app.add_signal(
    my_signal_handler,
    "something.happened.ohmy1",
    conditions={"some_condition": "value"}
)

@app.signal("something.happened.ohmy2", conditions={"some_condition": "value"})
async def my_signal_handler2():
    print("something happened")
```
````

.. 列:

```
信号也可以在蓝图上声明
```

.. 列:

````
```python
bp = Blueprint("foo")

@bp.signal("something.semed.ohmy")
async def my_signal_handler():
    print("发生什么")
```
````

## 内置信号

除了发出新的信号外，还有一些内在信号是从萨尼克本身发出的。 这些信号的存在为开发者提供了更多的机会，可以将功能添加到请求和服务器的周期中。

\*添加于 v21.9 \*

.. 列:

```
您可以像其他任何信号一样将它们附加到应用程序或蓝图实例。
```

.. 列:

````
```python
@app.signal("http.lifecycle.complete")
async def my_signal_handler(conn_info):
    print("连接已关闭")
```
````

这些信号是现有的信号，以及处理者的论据和附加条件（如有）。

| 事件名称                       | 参数                             | 条件                                                                                                                                  |
| -------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `http.routing.before`      | 请求                             |                                                                                                                                     |
| `http.routing.after `      | 请求, 路由, kwargs, 处理程序           |                                                                                                                                     |
| `http.handler.befor`       | 请求                             |                                                                                                                                     |
| `http.handler.after `      | 请求                             |                                                                                                                                     |
| `http.lifecycle.begin`     | conn_info |                                                                                                                                     |
| `http.lifecycle.read_head` | 头部                             |                                                                                                                                     |
| `http.lifecycle.request`   | 请求                             |                                                                                                                                     |
| `http.lifecycle.handle`    | 请求                             |                                                                                                                                     |
| `http.lifecycle.read_body` | 正文内容                           |                                                                                                                                     |
| `http.lifecycle.excition`  | 请求异常                           |                                                                                                                                     |
| `http.lifecycle.response`  | 请求回复                           |                                                                                                                                     |
| `http.lifecycle.send`      | 数据                             |                                                                                                                                     |
| `http.lifecycle.complete`  | conn_info |                                                                                                                                     |
| `http.midleware.before`    | 请求回复                           | \`{"attach_to": "request"}" 或 "{"attach_to": "response"}" |
| `http.midleware.after `    | 请求回复                           | \`{"attach_to": "request"}" 或 "{"attach_to": "response"}" |
| `server.exception.report`  | 应用，异常                          |                                                                                                                                     |
| `server.init.before`       | 应用，循环                          |                                                                                                                                     |
| `server.init.after `       | 应用，循环                          |                                                                                                                                     |
| `server.shutdown.before`   | 应用，循环                          |                                                                                                                                     |
| `server.shutdown.after `   | 应用，循环                          |                                                                                                                                     |

22.9版本增加了`http.handler.before`和`http.handler.after`。

版本23.6增加了“server.exception.report”。

.. 列:

```
为了更容易使用内置信号，有一个 `Enum` 对象包含所有允许的内嵌。 使用现代IDE，这将有助于您不需要记住事件名称的完整列表作为字符串。

*添加于 v21.12*
```

.. 列:

````
```python
from sanic.signs import Event

@app.signal(Event.HTTP_LIFECYCLE_COMPerTE)
async def my_signal_handler(conn_info):
    print("连接已关闭")
```
````

## 事件

.. 列:

```
信号来自一个 _event_。事件只是以下模式中的一个字符串：
```

.. 列:

````
```
namespace.reference.action
```
````

.. 提示：事件必须有三个部分。 如果您不知道要使用什么，请尝试这些模式：

```
- `my_app.something.oced`
- `sanic.notific.hello`
```

### 事件参数

.. 列:

```
事件可以是“动态”并声明使用与 [路径参数] (../basics/routing.md#path参数)相同的语法。这允许根据任意值进行匹配。
```

.. 列:

````
```python
@app.signal("foo.bar.<thing>")
async def signal_handler(thing):
    print(f"[signal_handler] {thing=}")

@appp. et("/")
async def 触发器(请求):
    等待app.prespatch("foo.bar.baz")
    return response.text("完成")
```
````

签出[路径参数](../basics/routing.md#path参数)以获取关于允许类型定义的更多信息。

.. 信息：事件的第三部分 (动作) 可能是动态的：

```
- `foo.bar.<thing>` 🆗
- `foo.<bar>.baz` ❌
```

### 等待中

.. 列:

```
除了执行信号处理程序外，您的应用程序可以等待事件触发的时间。
```

.. 列:

````
```python
等待app.event("foo.bar.baz")

````

.. 列:

```
**IMPORTANT**：等待是一个阻止函数。因此，你很可能想要这个函数在[背景任务](../basics/tasks.md)中运行。
```

.. 列:

````
```python
async def wait_for_event(app):
    while True:
        print("> 等待")
        等待应用。 vent("foo.bar. 日")
        print("> event found\n")

@app. fter_server_start
async def after _server_start(app, loop):
    app.add_task(wait_for_event(app))
```
````

.. 列:

```
如果你的事件是用动态路径定义的，你可以使用 "*" 来捕捉任何动作。
```

.. 列:

````
```python
@app.signal("foo.bar.<thing>

...

等待app.event("foo.bar.*")
```
````

## 正在发送

_今后，Sanic将自动发送一些事件以帮助开发人员将其绑定到生命周期活动中。_

.. 列:

```
调度一个事件会做两个事情：

1，执行事件定义的任何信号处理和
2。 解决“等待”事件完成的任何问题。
```

.. 列:

````
```python
@app.signal("foo.bar.<thing>")
async def foo_bar(thing):
    print(f"{thing=}")

等待app.appailch("foo.bar.baz")
```
```
thing=baz
```
````

### 二. 背景

.. 列:

```
有时您可能会发现需要将额外信息传递到信号处理器。 在我们上面的第一个例子中，我们希望我们的电子邮件注册过程有用户的电子邮件地址。
```

.. 列:

````
```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    print(context)

等待应用。 ispatch(
    "user.registration" 恢复了",
    context={"hello": "world"}
)
```
```
{'hello': 'world'}
```
````

.. tip:: FYI

```
在后台任务中发出信号。
```

### 蓝图

正在发送蓝图信号的概念与 [middleware]相似(../basics/midleware.md)。 从应用层面做的任何事情都会被推到蓝图。 然而，在蓝图上派遣部队只会执行该蓝图上所确定的信号。

.. 列:

```
或许一个例子更容易解释：
```

.. 列:

````
```python
bp = Blueprint("bp")

app_count = 0
bp_count = 0

@app.signal("foo). ar.baz")
def app_signal():
    non-local app_count
    app_count += 1

@bp. ignal("foo.bar.baz")
def bp_signal():
    non-local bp_count
    bp_count += 1
```
````

.. 列:

```
正在运行 `app.appotich("foo.bar.baz")` 将执行两个信号。
```

.. 列:

````
```python
正在等待 app.appoquarch("foo.bar.baz")
确认app_count == 1
申述bp_count == 1
```
````

.. 列:

```
运行 `bp.apparch("foo.bar.baz")` 只会执行蓝图信号。
```

.. 列:

````
```python
等待bp.apparch("foo.bar.baz")
conflict app_count == 1
conflict bp_count == 2
```
````
