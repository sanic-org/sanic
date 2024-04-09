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

1. 你可以不用直接使用 :class:`sanic.response.HTTPresponse` 实例去返回数据 使用一些内置封装好的[返回函数](./response#methods)将会变的更加简单。

   - `from sanic import json`
   - `from sanic import html`
   - `from sanic import redirect`
   - _etc_
2. 我们会在[流媒体部分](../advanced/streaming#response-streaming)中看到的，您并不总是需要返回一个对象。 如果您使用此较低级别的 API，您可以控制处理器内响应的流量，并且返回对象未被使用。

.. 提示：浮动通知

```
如果你想了解更多关于封装你的逻辑的信息，结帐[基于类的视图](../advanced/class-based-views.md)。现在，我们将继续只是基于函数的视图。
```

### 一个简单的基于功能的处理程序

创建路由处理程序的最常见方式是装饰函数。 它为路线定义建立简单的视觉标识。 我们将了解更多关于[路由](./routing.md)

.. 列:

```
Let's look at a practical example.

- We use a convenience decorator on our app instance: `@app.get()`
- And a handy convenience method for generating out response object: `text()`

Mission accomplished 💪
```

.. 列:

````
```python
from sanic import text

@app.get("/foo")
async def foo_handler(request):
    return text("我说了！")
```
````

---

## 关于 _async_...

.. 列:

```
完全可以写入同步处理程序。

在此示例中，我们正在使用 _blocking_ `time.sleep()` 模拟100毫秒的处理时间。 也许这意味着从数据库或第三方网站获取数据。

使用四(4)个工序和一个共同的基准工具：

- **956** 在 30.10s
- 或大约**31.76** 请求/秒
```

.. 列:

````
```python
@app.get("/sync")
def sync_handler(request):
    time.sleep(0.1)
    return text("完成")
```
````

.. 列:

```
Just by changing to the asynchronous alternative `asyncio.sleep()`, we see an incredible change in performance. 🚀

Using the same four (4) worker processes:

- **115,590** requests in 30.08s
- Or, about **3,843.17** requests/second

.. attrs::
    :class: is-size-2

    🤯
```

.. 列:

````
```python
@app.get("/async")
async def async_handler(request):
    等待asyncio.sleep(0.1)
    return text("完成")
```
````

好的... 这是一个荒谬的过于戏剧性的结果。 你们所看到的任何基准都本质上是非常偏颇的。 这个示例是为了在网上显示`async/await`的好处。 结果肯定会有所不同。 诸如Sanic和其他异步Python图书馆之类的工具不是使事情变得更快的神奇子弹。 它们使它们更有效率。

在我们的例子中，异步版本要好得多，因为当一个请求正在睡觉时， 它能够开始另一个和另一个，以及另一个...

但这是要点！ 沙漠之所以迅速，是因为它需要现有的资源，并挤压了可用资源的业绩。 它可以同时处理许多请求，这意味着每秒要有更多的请求。

.. 提示：常见错误！

```
Don't do this! You need to ping a website. What do you use? `pip install your-fav-request-library` 🙈

Instead, try using a client that is `async/await` capable. Your server will thank you. Avoid using blocking tools, and favor those that play well in the asynchronous ecosystem. If you need recommendations, check out [Awesome Sanic](https://github.com/mekicha/awesome-sanic).

Sanic uses [httpx](https://www.python-httpx.org/) inside of its testing package (sanic-testing) 😉.
```

---

## 一个完整注释的处理程序

对于那些使用类型注释的人...

```python
from sanic.response import HTTPResponse, text
from sanic.request import Request

@app.get("/typed")
async def typed_handler(request: Request) -> HTTPResponse:
    return text("Done.")
```

## 命名您的处理程序

所有处理程序都是自动命名的。 这对调试和生成模板中的 URL非常有用。 未指定时，将使用的名称是函数的名称。

.. 列:

```
例如，这个处理程序将被命名为“foo_handler”。
```

.. 列:

````
```python
# Handler 名称将是“foo_handler”
@app.get("/foo")
async def foo_handler(request):
    return text("我说了！")
```
````

.. 列:

```
然而，你可以把`name`的参数传递给装饰师来覆盖这个问题。
```

.. 列:

````
```python
# Handler 名称将是“foo”
@app.get("/foo", name="foo")
async def foo_handler(request):
    return text("我说了！")
```
````

.. 列:

```
事实上，正如你将要做的那样，可能有时候你**MUST** 提供一个名称。 例如，如果你在同一函数上使用两个装饰器，你需要为其中至少一个提供一个名称。

如果您不这样做，您将会遇到一个错误，您的应用程序将不会启动。名称**必须** 在您的应用程序中是唯一的。
```

.. 列:

````
```python
# 两个处理器，相同的函数，
# 不同的名字：
# - "foo_arg"
# - "foo"
@app。 et("/foo/<arg>", name="foo_arg")
@app.get("/foo")
异步脚(请求，arg=Non):
    return text("我说了！")
```
````
