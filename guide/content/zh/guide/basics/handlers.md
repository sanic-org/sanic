# 响应函数(Handlers)

下一个重要的构件块是你的 _handlers_。 它们有时也被称为“视图”。

在 Sanic 中，响应函数可以是任何一个可调用程序，它至少以一个 :class:`sanic.request.Request`  实例作为参数，并返回一个 :class:`sanic.response.HTTPResponse` 实例或一个执行其他操作的协同程序作为响应。

.. column::

```
嗯哼？😕

响应函数仅仅是一个 **函数**，可以是同步的，也可以是异步的。

响应函数的任务是响应一个请求入口并做一些数据操作。 这是您的大多数业务逻辑将要走的地方。
```

.. column::

````
```python
def i_am_a_handler(request):
    return HTTPResponse()

async def i_am_ALSO_a_handler(request):
    return HTTPResponse()
```
````

还有另外两个点需要注意一下：

1. 你可以不用直接使用 :class:`sanic.response.HTTPresponse` 实例去返回数据 使用一些内置封装好的[便捷方法](./response#methods)，将会变的更加简单。

    - `from sanic import json`
    - `from sanic import html`
    - `from sanic import redirect`
    - _etc_
2. 我们会在[流媒体部分](../advanced/streaming#response-streaming)中看到的，您并不总是需要返回一个对象。 如果您使用这个底层的 API，您可以在处理程序内部控制响应的流程，并且不需要使用返回对象。

.. tip:: 提示

```
如果你想了解更多关于封装逻辑的内容，可以查阅[基于类的视图](../advanced/class-based-views.md)。现在，我们将继续仅基于函数的视图讲解。
```

### 一个简单的基于函数的处理器

创建路由处理程序的最常见方式是装饰函数。 它为路由定义创建了一个视觉上简洁的标识。 我们稍后将了解更多关于[路由](./routing.md)

.. column::

```
让我们来看一个实际的例子。

- 我们在应用实例上使用了一个便捷装饰器：`@app.get()`
- 以及一个用于生成响应对象的便捷方法：`text()`

任务完成💪
```

.. column::

````
```python
from sanic import text

@app.get("/foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

---

## 关于 _async_...

.. column::

```
完全可以写入同步处理程序。

在此示例中，我们正在使用 _blocking_ `time.sleep()` 模拟100毫秒的处理时间。 也许这意味着从数据库或第三方网站获取数据。

使用四(4)个工序和一个共同的基准工具：

- **956** 在 30.10s
- 或大约**31.76** 请求/秒
```

.. column::

````
```python
@app.get("/sync")
def sync_handler(request):
    time.sleep(0.1)
    return text("Done.")
```
````

.. column::

```
只需将 `time.sleep()` 更改为异步替代方案 `asyncio.sleep()`，我们就能看到性能有了显著提升。 🚀

同样使用四个（4）工作进程：

- 在30.08秒内处理了 **115,590** 个请求
- 或者说，大约每秒处理 **3,843.17** 个请求

.. attrs::
    :class: is-size-2

    🤯
```

.. column::

````
```python
@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)
    return text("Done.")
```
````

好的... 这是一个夸张得离谱的结果。 你们所看到的任何基准都本质上是非常偏颇的。 这个例子旨在极度展示`async/await`在web开发领域的优势。 结果肯定会有所不同。 像Sanic和其他异步Python库并非神奇的解决方案，能自动让程序运行更快。 它们使程序执行更加高效。

在我们的示例中，异步版本之所以表现优秀，是因为当一个请求在“睡眠”（等待）时，它可以开始处理另一个请求，然后再处理下一个、下一个、下一个……以此类推，实现并行处理多个请求，从而大大提高服务器的吞吐量。

但是，这就是关键所在！ Sanic之所以快，是因为它充分利用可用资源并榨取其性能潜力。 它可以同时处理大量请求，这就意味着每秒能够处理更多的请求。

.. 提示：一个常见的误区！

```
当你你需要对一个网站进行ping操作。你会用什么工具？`pip install 你最爱的请求库 `，我劝你不要这样做🙈

而应该尝试使用支持`async/await`功能的客户端。你的服务器会因此说`谢谢你`，避免使用阻塞型工具，尽量选择能良好适应异步生态系统中的工具。如果你需要推荐，可以查看[Awesome Sanic](https://github.com/mekicha/awesome-sanic).。

Sanic在其测试包（sanic-testing）中使用了[httpx](https://www.python-httpx.org/) 😜。
```

---

## 一个带完整注解的处理器

对于那些使用类型注解的人...

```python
from sanic.response import HTTPResponse, text
from sanic.request import Request

@app.get("/typed")
async def typed_handler(request: Request) -> HTTPResponse:
    return text("Done.")
```

## 为您的处理器命名

所有处理器都会自动命名。 这对于调试和在模板中生成URL非常有用。 如果不特别指定，将使用的名称就是函数的名

.. column::

```
例如，这个处理程序将被命名为“foo_handler”。
```

.. column::

````
```python
# Handler name will be "foo_handler"
@app.get("/foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

.. column::

```
同样，您可以通过向装饰器传递`name`参数来指定名称。
```

.. column::

````
```python
# Handler name will be "foo"
@app.get("/foo", name="foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

.. column::

```
事实上，正如你将会遇到的情况，有时您**必须**提供名称。例如，如果您在同一函数上使用两个装饰器，那么至少需要为其中一个提供名称。

如果不这样做，您将收到错误，并且您的应用将无法启动。在您的应用中，名称**必须**是唯一的。
```

.. column::

````
```python
# Two handlers, same function,
# different names:
# - "foo_arg"
# - "foo"
@app.get("/foo/<arg>", name="foo_arg")
@app.get("/foo")
async def foo(request, arg=None):
    return text("I said foo!")
```
````
