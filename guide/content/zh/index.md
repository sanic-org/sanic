---
title: 闪电般快速的异步 Python 网络框架
layout: 首页
features:
  - title: 简单轻便
    details: 智能默认和没有博客的直观API允许您直接建立您的应用程序。
  - title: 无意见和灵活的
    details: 构建你想要构建的方式而不让你的工具约束你。
  - title: 性能和可缩放
    details: 以速度和可伸缩性作为主要关切事项。 它已经准备好为无论大小的网络应用程序供电。
  - title: 生产已准备好
    details: 在盒子中，它被捆绑在一个网络服务器上，可以为您的网络应用程序提供电力。
  - title: 受数以百万计的信任的
    details: Sanic 是 PyPI 最受欢迎的框架之一，是启用异步的顶部框架
  - title: 社区驱动的
    details: 该项目由社区为社区维护和管理。
---

### :hig_voltag: lightning-fast asynchronous Python web Framework

.. attrs::
:class: columns is-multiline mt-6

```
.. attrs::
    :class: column is-4

    #### Simple and lightweight

    Intuitive API with smart defaults and no bloat allows you to get straight to work building your app.

.. attrs::
    :class: column is-4

    #### Unopinionated and flexible

    Build the way you want to build without letting your tooling constrain you.

.. attrs::
    :class: column is-4

    #### Performant and scalable

    Built from the ground up with speed and scalability as a main concern. It is ready to power web applications big and small.

.. attrs::
    :class: column is-4

    #### Production ready

    Out of the box, it comes bundled with a web server ready to power your web applications.

.. attrs::
    :class: column is-4

    #### Trusted by millions

    Sanic is one of the overall most popular frameworks on PyPI, and the top async enabled framework

.. attrs::
    :class: column is-4

    #### Community driven

    The project is maintained and run by the community for the community.
```

.. attrs::
:class: is-size-3 mt-6

```
**使用您所期望的功能和工具。**
```

.. attrs::
:class: is-size-3 ml-6

```
**和一些 {span:has-text-primary:you wouldn't believe}.**
```

.. 标签：生产等级

````
After installing, Sanic has all the tools you need for a scalable, production-grade server—out of the box!

Including [full TLS support](/en/guide/how-to/tls).

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

.. 标签：TLS服务器

````
启用 TLS 来运行Sanic与传递文件路径一样简单...
```sh
sanic path.to.server:app --cert=/path/to/bundle。 rt --key=/path/to/privkey.pem
``

... 或包含`fullchain.pem` 和 `privkey.pem`

```sh
sanic path.to. erver:app --tls=/path/to/certs
```

**甚至更好地**，正在开发中。 让Sanic处理设置本地TLS证书，以便您可以通过 TLS 访问 [https://localhost:8443](https://localhost:8443)

```sh
sanic 路径。 o.server:app --dev --auto-tls
```
````

.. 标签：Websockets

````
Up and running with websockets in no time using the [websockets](https://websockets.readthedocs.io) package.
```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    async for msg in ws:
        await ws.send(msg)
```
````

.. 标签：静态文件

````
服务静态文件当然是直观和容易的。只需命名一个端点和一个应该服务的文件或目录。

```python
app.static("/", "/path/to/index.html")
应用。 tatic("/uploads/", "/path/to/uploads/")
```

此外，服务目录还有两个额外功能：自动服务索引，自动服务于文件浏览器。

Sanic 可以自动将 `index.html` (或任何其他命名文件) 作为目录或其子目录中的索引页。

```python
app.static(
    "/uploads/",
    "/path/to/uploads/",
    index="索引。
()
```

And/or 设置Sanic 以显示文件浏览器。


！[image](/assets/images/directory-view.png)

```python
app tatic(
    "/uploads/",
    "/path/to/uploads/",
    directory_view=True
)
```
````

.. tab：生命周期：

````
Beginning or ending a route with functionality is as simple as adding a decorator.

```python
@app.on_request
async def add_key(request):
    request.ctx.foo = "bar"

@app.on_response
async def custom_banner(request, response):
    response.headers["X-Foo"] = request.ctx.foo
```

Same with server events.

```python
@app.before_server_start
async def setup_db(app):
    app.ctx.db_pool = await db_setup()

@app.after_server_stop
async def setup_db(app):
    await app.ctx.db_pool.shutdown()
```

But, Sanic also allows you to tie into a bunch of built-in events (called signals), or create and dispatch your own.

```python
@app.signal("http.lifecycle.complete")  # built-in
async def my_signal_handler(conn_info):
    print("Connection has been closed")

@app.signal("something.happened.ohmy")  # custom
async def my_signal_handler():
    print("something happened")

await app.dispatch("something.happened.ohmy")
```
````

.. 标签：智能错误处理

````
提升错误会直观地导致正确的 HTTP 错误：

``python
raising sanic.exception。 ootFound # 自动响应HTTP 404
``

或是你自己：

```python
xceptions import SanicException

class TeapotError(SanicException):
    status_code = 418
    message = “对不起，” 我不能酿造咖啡”

提高Teapot错误
```

当发生错误时， Sanic美丽的 DEV 模式错误页面将帮助您快速钻到漏洞。

！[image](../assets/images/error-div-zero.png)

不管怎样，Sanic带有一个算法，尝试使用HTML，JSON或文本错误作为相应答复。 别担心，设置和自定义您的错误处理符合您的具体需要是非常简单的。
````

.. 选项卡：应用查看器

````
Check in on your live, running applications (whether local or remote).
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

And, issue commands like `reload`, `shutdown`, `scale`...

```sh
sanic inspect scale 4
```

... or even create your own!

```sh
sanic inspect migrations
```
````

.. 标签：可扩展

```
In addition to the tools that Sanic comes with, the officially supported [Sanic Extensions](./plugins/sanic-ext/getting-started.md) provides lots of extra goodies to make development easier.

- **CORS** protection
- Template rendering with **Jinja**
- **Dependency injection** into route handlers
- OpenAPI documentation with **Redoc** and/or **Swagger**
- Predefined, endpoint-specific response **serializers**
- Request query arguments and body input **validation**
- **Auto create** HEAD, OPTIONS, and TRACE endpoints
- Live **health monitor**
```

.. 标签：开发者体验

```
Sanic is **built for building**.

From the moment it is installed, Sanic includes helpful tools to help the developer get their job done.

- **One server** - Develop locally in DEV mode on the same server that will run your PRODUCTION application
- **Auto reload** - Reload running applications every time you save a Python file, but also auto-reload **on any arbitrary directory** like HTML template directories
- **Debugging tools** - Super helpful (and beautiful) [error pages](/en/guide/best-practices/exceptions) that help you traverse the trace stack easily
- **Auto TLS** - Running a localhost website with `https` can be difficult, [Sanic makes it easy](/en/guide/how-to/tls)
- **Streamlined testing** - Built-in testing capabilities, making it easier for developers to create and run tests, ensuring the quality and reliability of their services
- **Modern Python** - Thoughtful use of type hints to help the developer IDE experience
```
