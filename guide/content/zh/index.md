---
title: 快如闪电的异步 Python Web 框架
layout: 首页
features:
  - title: 简单轻便
    details: 直观、智能、精简的API，让您可以直接开始构建应用程序。
  - title: 灵巧无束
    details: 可以用您自己的方式进行创作，不会对您造成任何约束
  - title: 高效且可拓展
    details: 关注应用的速度和可扩展性 随时为大大小小的网络应用程序提供支持
  - title: 生产就绪
    details: 开箱即用，Sanic 不仅是一个框架，也是一个服务器，并随时准备驱动您的 Web 应用
  - title: 备受信赖
    details: Sanic 是 PyPI 最受欢迎的框架之一，是顶级的异步python Web 框架
  - title: 社区驱动
    details: 从社区来，到社区去。Sanic 由社区共同维护和管理
---

### ⚡ 快如闪电的异步 Python Web 框架

.. attrs::
:class: columns is-multiline mt-6

```
.. attrs::
    :class: column is-4

    #### 简单轻便

    直观、智能、精简的API，让您可以直接开始构建应用程序。

.. attrs::
    :class: column is-4

    #### 灵巧无束

    可以用您自己的方式进行创作，不会对您造成任何约束

.. attrs::
    :class: column is-4

    #### 高效且可拓展

    关注应用的速度和可扩展性，可随时为大大小小的网络应用程序提供支持

.. attrs::
    :class: column is-4

    #### 生产就绪

    开箱即用，Sanic 不仅是一个框架，也是一个服务器，并随时准备驱动您的 Web 应用

.. attrs::
    :class: column is-4

    #### 备受信赖

    Sanic 是 PyPI 最受欢迎的框架之一，是顶级的异步python Web 框架

.. attrs::
    :class: column is-4

    #### 社区驱动

    从社区来，到社区去。Sanic 由社区共同维护和管理
```

.. attrs::
:class: is-size-3 mt-6

```
**有你所期待的功能和工具。**
```

.. attrs::
:class: is-size-3 ml-6

```
**还有一些{span:has-text-primary:意料之外的惊喜}。**
```

.. tab:: 生产级别（Production-grade）

````
After installing, Sanic has all the tools you need for a scalable, production-grade server—out of the box!

Including [full TLS support](/en/guide/how-to/tls.md).

```python
from sanic import Sanic
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```

```sh
sanic path.to.server:app
[2023-01-31 12:34:56 +0000] [999996] [INFO] Sanic v22.12.0
[2023-01-31 12:34:56 +0000] [999996] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2023-01-31 12:34:56 +0000] [999996] [INFO] mode: production, single worker
[2023-01-31 12:34:56 +0000] [999996] [INFO] server: sanic, HTTP/1.1
[2023-01-31 12:34:56 +0000] [999996] [INFO] python: 3.10.9
[2023-01-31 12:34:56 +0000] [999996] [INFO] platform: SomeOS-9.8.7
[2023-01-31 12:34:56 +0000] [999996] [INFO] packages: sanic-routing==22.8.0
[2023-01-31 12:34:56 +0000] [999997] [INFO] Starting worker [999997]
```
````

.. tab:: TLS 服务器（TLS server）

````
使用 带 TLS 的 Sanic 就像向其设置文件路径一样简单......
```sh
sanic path.to.server:app --cert=/path/to/bundle。 rt --key=/path/to/privkey.pem
``

... 或是包含`fullchain.pem` 和 `privkey.pem`的目录文件夹

```sh
sanic path.to. erver:app --tls=/path/to/certs
```

**除此之外**，在开发中，让Sanic处理设置本地TLS证书，以便您可以通过 TLS 访问 [https://localhost:8443](https://localhost:8443)

```sh
sanic path.to.server:app --dev --auto-tls
```
````

.. tab:: Websockets

````
得益于 [websockets](https://websockets.readthedocs.io) 库，可以无缝实现的 WebSockets。

```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    async for msg in ws:
        await ws.send(msg)
```
````

.. tab:: 静态文件（Static files）

````
为静态文件服务当然是既直观又容易。只需配置一个入口并且指定一个文件或一个目录文件夹即可。

```python
app.static("/", "/path/to/index.html")
app.static("/uploads/", "/path/to/uploads/")
```

此外，当参数是目录时，还有两个附加功能：自动提供索引和自动提供文件浏览器。

Sanic 可以自动将 `index.html` (或任何其他命名文件) 作为目录或其子目录中的索引页。

```python
app.static(
    "/uploads/",
    "/path/to/uploads/",
    index="index.html"
)
```

让 Sanic 以显示文件浏览器需要这样设置。


![image](/assets/images/directory-view.png)

```python
app.static(
    "/uploads/",
    "/path/to/uploads/",
    directory_view=True
)
```
````

.. tab:: 生命周期（Lifecycle）

````
添加一个装饰器，就能在应用生命周期开始或结束时插入自定义的处理函数

```python
@app.on_request
async def add_key(request):
    request.ctx.foo = "bar"

@app.on_response
async def custom_banner(request, response):
    response.headers["X-Foo"] = request.ctx.foo
```

服务器事件（server events）也是一样的。

```python
@app.before_server_start
async def setup_db(app):
    app.ctx.db_pool = await db_setup()

@app.after_server_stop
async def setup_db(app):
    await app.ctx.db_pool.shutdown()
```

除此之外，Sanic 还允许您绑定一系列官方内置事件（称为信号），或创建和调度自己的事件。

```python
@app.signal("http.lifecycle.complete")  # built-in (官方内置的)
async def my_signal_handler(conn_info):
    print("Connection has been closed")

@app.signal("something.happened.ohmy")  # custom (自定义的)
async def my_signal_handler():
    print("something happened")

await app.dispatch("something.happened.ohmy")
```
````

.. tab:: 智能错误处理（Smart error handling）

````
出错后，会出现直观且合适的 HTTP 错误：

```python
raise sanic.exceptions.NotFound # Automatically responds with HTTP 404
```

或是实现您自己的错误处理方法：

```python
from sanic.exceptions import SanicException

class TeapotError(SanicException):
    status_code = 418
    message = "Sorry, I cannot brew coffee"

raise TeapotError
```

如果出现错误，Sanic 美观的开发模式错误页面将帮助您快速定位到错误所在。

![image](../assets/images/error-div-by-zero.png)

无论如何，Sanic 自带的算法都会根据情况尝试响应 HTML、JSON 或 text-based 的错误。不要担心，您可以根据您的具体需求，非常简单的设置和自定义错误处理的方法。
````

.. tab:: 应用查看器（App Inspector）

````
不管是在本地还是在远程，Sanic 都可以检查你正在运行的应用。
```sh
sanic inspect      

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                        Sanic                                                        │
│                                          Inspecting @ http://localhost:6457                                         │
├───────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────┤
│                       │     mode: production, single worker                                                         │
│     ▄███ █████ ██     │   server: unknown                                                                           │
│    ██                 │   python: 3.10.9                                                                            │
│     ▀███████ ███▄     │ platform: SomeOS-9.8.7
│                 ██    │ packages: sanic==22.12.0, sanic-routing==22.8.0, sanic-testing==22.12.0, sanic-ext==22.12.0 │
│    ████ ████████▀     │                                                                                             │
│                       │                                                                                             │
│ Build Fast. Run Fast. │                                                                                             │
└───────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────┘

Sanic-Main
    pid: 999996

Sanic-Server-0-0
    server: True
    state: ACKED
    pid: 999997
    start_at: 2023-01-31T12:34:56.00000+00:00
    starts: 1

Sanic-Inspector-0
    server: False
    state: STARTED
    pid: 999998
    start_at: 2023-01-31T12:34:56.00000+00:00
    starts: 1
```

并且可以使用像是 `reload`, `shutdown`, `scale` 的命令...

```sh
sanic inspect scale 4
```

... 甚至是创建你自己的！

```sh
sanic inspect migrations
```
````

.. tab:: 可扩展（Extendable）

```
除了 Sanic 自带的工具外，官方支持的 [Sanic 扩展](./plugins/sanic-ext/getting-started.md) 还提供了许多额外的好东西，使您的开发更加轻松。

- **CORS** 保护
- 使用 **Jinja** 进行模板渲染
- 将其他对象通过 **Dependency injection** （依赖注入）到路由处理程序中
- 使用 **Redoc** 和/或 **Swagger** 编写 OpenAPI 文档
- 预先定义好的**序列化函数**(eg `json`  `text`)、作用于不同的路由入口（serializers）
- 请求查询参数和正文输入的**验证器**（validation）
- **自动创建** HEAD、OPTIONS 和 TRACE 入口（auto create）
- 实时**健康监控**（health monitor）
```

.. tab:: 开发体验（Developer Experience）

```
Sanic is **built for building**.

From the moment it is installed, Sanic includes helpful tools to help the developer get their job done.

- **One server** - Develop locally in DEV mode on the same server that will run your PRODUCTION application
- **Auto reload** - Reload running applications every time you save a Python file, but also auto-reload **on any arbitrary directory** like HTML template directories
- **Debugging tools** - Super helpful (and beautiful) [error pages](/en/guide/best-practices/exceptions) that help you traverse the trace stack easily
- **Auto TLS** - Running a localhost website with `https` can be difficult, [Sanic makes it easy](/en/guide/how-to/tls.md)
- **Streamlined testing** - Built-in testing capabilities, making it easier for developers to create and run tests, ensuring the quality and reliability of their services
- **Modern Python** - Thoughtful use of type hints to help the developer IDE experience
```
