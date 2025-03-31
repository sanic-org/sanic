# 信号(Signals)

信号提供了一种方式，使得应用程序的一部分能够通知另一部分发生了某件事情。

```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    await send_email(context["email"], template="registration")

@app.post("/register")
async def handle_registration(request):
    await do_registration(request)
    await request.app.dispatch(
        "user.registration.created",
        context={"email": request.json.email}
    })
```

## 添加信号(Adding a signal)

.. column::

```
添加信号的 API 与添加路由非常相似。
```

.. column::

````
```python
async def my_signal_handler():
    print("something happened")

app.add_signal(my_signal_handler, "something.happened.ohmy")
```
````

.. column::

```
但是，也许使用内置装饰器的方法更为便捷一些。
```

.. column::

````
```python
@app.signal("something.happened.ohmy")
async def my_signal_handler():
    print("something happened")
```
````

.. column::

```
如果信号需要满足某些条件，请确保在添加处理器时添加这些条件。
```

.. column::

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

.. column::

```
信号也可以在蓝图上声明
```

.. column::

````
```python
bp = Blueprint("foo")

@bp.signal("something.happened.ohmy")
async def my_signal_handler():
    print("something happened")
```
````

## 内置信号(Built-in signals)

除了创建新的信号外，Sanic 自身还分发了一些内置信号。 这些信号的存在是为了为开发者提供更多机会在请求和服务器生命周期中添加功能。

\*添加于 v21.9 \*

.. column::

```
您可以像对待其他任何信号一样，将它们附加到应用或蓝图实例上。
```

.. column::

````
```python
@app.signal("http.lifecycle.complete")
async def my_signal_handler(conn_info):
    print("Connection has been closed")
```
````

这些信号是可用的信号，包括处理器所需处理的参数以及（如果有）附带的条件。

| 事件名称（Event name）           | 参数（Arguments）                   | 条件（Conditions）                                            |
| -------------------------- | ------------------------------- | --------------------------------------------------------- |
| `http.routing.before`      | request                         |                                                           |
| `http.routing.after`       | request, route, kwargs, handler |                                                           |
| `http.handler.before`      | request                         |                                                           |
| `http.handler.after`       | request                         |                                                           |
| `http.lifecycle.begin`     | conn_info  |                                                           |
| `http.lifecycle.read_head` | head                            |                                                           |
| `http.lifecycle.request`   | request                         |                                                           |
| `http.lifecycle.handle`    | request                         |                                                           |
| `http.lifecycle.read_body` | body                            |                                                           |
| `http.lifecycle.exception` | request, exception              |                                                           |
| `http.lifecycle.response`  | request, response               |                                                           |
| `http.lifecycle.send`      | data                            |                                                           |
| `http.lifecycle.complete`  | conn_info  |                                                           |
| `http.middleware.before`   | request, response               | `{"attach_to": "request"}` or `{"attach_to": "response"}` |
| `http.middleware.after`    | request, response               | `{"attach_to": "request"}` or `{"attach_to": "response"}` |
| `server.exception.report`  | app, exception                  |                                                           |
| `server.init.before`       | app, loop                       |                                                           |
| `server.init.after`        | app, loop                       |                                                           |
| `server.shutdown.before`   | app, loop                       |                                                           |
| `server.shutdown.after`    | app, loop                       |                                                           |

22.9版本增加了  `http.handler.before` 和  `http.handler.after` 。

版本23.6增加了  `server.exception.report` 。

.. column::

```
为了更方便地使用内置信号，这里有一个包含所有允许内置信号的 `Enum` 对象。在现代 IDE 中，这将有助于您无需记忆作为字符串形式的所有事件名称列表。

*从 v21.12 版本开始新增*
```

.. column::

````
```python
from sanic.signals import Event

@app.signal(Event.HTTP_LIFECYCLE_COMPLETE)
async def my_signal_handler(conn_info):
    print("Connection has been closed")
```
````

## 事件(Events)

.. column::

```
信号基于某个 _事件_ 。事件实际上就是一个遵循以下模式的字符串：
```

.. column::

````
```
namespace.reference.action
```
````

.. tip:: 事件必须包含三个部分。 如果您不确定该如何使用，请尝试以下模式：

```
- `my_app.something.happened`
- `sanic.notice.hello`
```

### 事件参数(Event parameters)

.. column::

```
事件可以是“动态”的，并使用与[路径参数](../basics/routing.md#path-parameters)相同的语法进行声明。这样就可以基于任意值进行匹配。
```

.. column::

````
```python
@app.signal("foo.bar.<thing>")
async def signal_handler(thing):
    print(f"[signal_handler] {thing=}")

@app.get("/")
async def trigger(request):
    await app.dispatch("foo.bar.baz")
    return response.text("Done.")
```
````

有关允许的类型定义的更多信息，请查阅[路径参数](../basics/routing.md#path-parameters)。

.. info:: 只有事件的第三部分（动作）可以是动态的：

```
- `foo.bar.<thing>` 🆗
- `foo.<bar>.baz` ❌
```

### 等待(Waiting)

.. column::

```
除了执行信号处理器之外，您的应用程序还可以等待某个事件被触发。
```

.. column::

````
```python
await app.event("foo.bar.baz")
```
````

.. column::

```
**重要提示**：等待是一个阻塞函数。因此，您可能希望将其在一个[后台任务](../basics/tasks.md)中运行。
```

.. column::

````
```python
async def wait_for_event(app):
    while True:
        print("> waiting")
        await app.event("foo.bar.baz")
        print("> event found\n")

@app.after_server_start
async def after_server_start(app, loop):
    app.add_task(wait_for_event(app))
```
````

.. column::

```
如果您的事件使用了动态路径定义，您可以使用 `*` 来捕获任何动作。
```

.. column::

````
```python
@app.signal("foo.bar.<thing>")

...

await app.event("foo.bar.*")
```
````

## 触发/派发/分发(Dispatching)

_在未来，Sanic 将自动分发一些事件以帮助开发者接入生命周期事件。_

.. column::

```
触发一个事件将会执行两件事：

1. 执行该事件上定义的所有信号处理器，
2. 处理所有正在“等待”该事件完成的任务。
```

.. column::

````
```python
@app.signal("foo.bar.<thing>")
async def foo_bar(thing):
    print(f"{thing=}")

await app.dispatch("foo.bar.baz")
```
```
thing=baz
```
````

### 上下文(Context)

.. column::

```
有时您可能会发现有必要向信号处理器传递额外信息。在上面的第一个示例中，我们希望电子邮件注册过程能拥有用户的电子邮件地址。
```

.. column::

````
```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    print(context)

await app.dispatch(
    "user.registration.created",
    context={"hello": "world"}
)
```
```
{'hello': 'world'}
```
````

.. tip:: 提示一下

```
信号是在后台任务中分发的。
```

### 蓝图(Blueprints)

触发蓝图信号的概念类似于 [中间件](../basics/middleware.md). 从应用级别所做的任何操作都将传递到蓝图。 然而，在蓝图上触发信号时，只会执行该蓝图上定义的信号。

.. column::

```
或许来个例子更容易解释：
```

.. column::

````
```python
bp = Blueprint("bp")

app_counter = 0
bp_counter = 0

@app.signal("foo.bar.baz")
def app_signal():
    nonlocal app_counter
    app_counter += 1

@bp.signal("foo.bar.baz")
def bp_signal():
    nonlocal bp_counter
    bp_counter += 1
```
````

.. column::

```
运行 `app.dispatch("foo.bar.baz")` 将会执行两个信号。
```

.. column::

````
```python
await app.dispatch("foo.bar.baz")
assert app_counter == 1
assert bp_counter == 1
```
````

.. column::

```
运行 `bp.dispatch("foo.bar.baz")` 将只执行蓝图上的信号。
```

.. column::

````
```python
await bp.dispatch("foo.bar.baz")
assert app_counter == 1
assert bp_counter == 2
```
````

