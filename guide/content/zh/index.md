---
title: 闪电般快速的异步 Python Web 框架
layout: 首页
features:
  - title: 简单轻便
    details: 直观的 API 具有智能默认设置且无臃肿，让您可以直接开始构建应用程序。
  - title: 灵巧无束
    details: 按照您的意愿进行自由开发，而不是让工具约束你
  - title: 易于拓展
    details: 关注应用的速度和可伸缩性 随时为大大小小的网络应用程序提供支持
  - title: 生产就绪
    details: 开箱即用，Sanic 配有一个 Web 服务器组件，并随时准备驱动您的 Web 应用
  - title: 备受信赖
    details: Sanic 是 PyPI 最受欢迎的框架之一，是顶级的异步兼容 Web 框架
  - title: 社区驱动
    details: 从社区来，到社区去。Sanic 由社区维护和管理
---

### :hig_voltag: 闪电般快速的异步 Python Web 框架

.. attrs::
:class: columns is-multiline mt-6

```
.. attrs::
    :class: column is-4

    #### 简单轻便

    开箱即用，直观无臃肿且具有智能默认设置的框架 API 可以使您直接构建应用程序

.. attrs::
    :class: column is-4

    #### 灵巧无束

    按照您的意愿进行自由创建，不会对您造成任何约束

.. attrs::
    :class: column is-4

    #### 易于拓展

    关注应用的速度和可伸缩性，可随时为大大小小的网络应用程序提供支持

.. attrs::
    :class: column is-4

    #### 生产环境预备

    Sanic 不仅是一个框架，也是一个服务器，它可以随时为您编写的 Web 应用程序提供部署服务

.. attrs::
    :class: column is-4

    #### 备受信赖

    Sanic 是 PyPI 最受欢迎的框架之一，是顶级的异步 Web 框架

.. attrs::
    :class: column is-4

    #### 社区驱动

    从社区来，到社区去，拥有大量的活跃贡献者
```

.. attrs::
:class: is-size-3 mt-6

```
**使用您所期望的功能和工具。**
```

.. attrs::
:class: is-size-3 ml-6

```
**还有一些{span:has-text-primary:您甚至不敢相信的}。**
```

.. tab:: 生产级别（Production-grade）

````
在安装后，Sanic 将为您提供开箱即用的可扩展生产级服务器所需的所有工具！

甚至包括[完整的 TLS 支持](/zh/guide/how-to/tls)。

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
在启用 TLS 的情况下运行 Sanic 就像向其传递文件路径一样简单......
```sh
sanic path.to.server:app --cert=/path/to/bundle。 rt --key=/path/to/privkey.pem
``

... 或是包含`fullchain.pem` 和 `privkey.pem`的目录

```sh
sanic path.to. erver:app --tls=/path/to/certs
```

**甚至更好地**，在开发中，让Sanic处理设置本地TLS证书，以便您可以通过 TLS 访问 [https://localhost:8443](https://localhost:8443)

```sh
sanic path.to.server:app --dev --auto-tls
```
````

.. tab:: Websockets

````
通过 [websockets](https://websockets.readthedocs.io) 库，可以马上实现的 WebSockets。

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
建立静态文件服务当然是既直观又容易。只需要给一个端点以及一个需要被服务的文件或目录命名即可。

```python
app.static("/", "/path/to/index.html")
app.static("/uploads/", "/path/to/uploads/")
```

此外，为目录提供服务还有两个附加功能：自动提供索引和自动提供文件浏览器。

Sanic 可以自动将 `index.html` (或任何其他命名文件) 作为目录或其子目录中的索引页。

```python
app.static(
    "/uploads/",
    "/path/to/uploads/",
    index="index.html"
)
```

之后，设置 Sanic 以显示文件浏览器。


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
添加一个装饰器，就能够应用一个在请求开始或是响应结束时的功能性的路由。

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

除此之外，Sanic 还允许您绑定一系列内置事件（称为信号），或创建和调度自己的事件。

```python
@app.signal("http.lifecycle.complete")  # 内建
async def my_signal_handler(conn_info):
    print("Connection has been closed")

@app.signal("something.happened.ohmy")  # 定制
async def my_signal_handler():
    print("something happened")

await app.dispatch("something.happened.ohmy")
```
````

.. tab:: 智能错误处理（Smart error handling）

````
出错后，会出现直观且准确的 HTTP 错误：

```python
raise sanic.exceptions.NotFound  # 自动响应 HTTP 404
```

或是实现您自己的：

```python
from sanic.exceptions import SanicException

class TeapotError(SanicException):
    status_code = 418
    message = "抱歉，我不能煮咖啡Orz"

raise TeapotError
```

如果出现错误，Sanic 美观的开发模式错误页面将帮助您快速定位到错误所在。

![image](../assets/images/error-div-by-zero.png)

无论如何，Sanic 自带的算法都会根据情况尝试响应 HTML、JSON 或基于文本的错误。不要担心，根据您的具体需求设置和自定义错误处理非常简单。
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
- 预定义的特定端点响应**序列化器**（serializers）
- 请求查询参数和正文输入的**验证器**（validation）
- **自动创建** HEAD、OPTIONS 和 TRACE 端点（auto create）
- 实时**健康监控**（health monitor）
```

.. tab:: 开发体验（Developer Experience）

```
Sanic **为构建而生**。

从安装的那一刻起，Sanic 就包含帮助开发人员完成工作的有用工具。

- **单个服务器** - 在将运行生产应用程序的同一服务器上以开发模式进行本地开发
- **自动重载** - 每次保存 Python 文件时重载正在运行的应用程序，也可在**任意目录**下自动重载，如 HTML 模板目录。
- **调试工具** - 超级有用（而且漂亮）的[错误页面](/zh/guide/best-practices/exceptions)，帮助你轻松遍历跟踪堆栈
- **自动 TLS** - 使用 "https" 运行本地主机网站可能很困难，但是 [Sanic 让它变得简单](/zh/guide/how-to/tls)
- **简化测试** - 内置测试功能，使开发人员更容易创建和运行测试，确保服务的质量和可靠性
- **现代 Python**- 体贴地使用类型提示，帮助开发人员获得集成开发环境体验
```
