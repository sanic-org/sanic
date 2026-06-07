---
title: 正在运行 Sanic
---

# 正在运行 Sanic

Sanic船上有自己的网络服务器。 在大多数情况下，这是最好的部署方法。 此外，您还可以将 Sanic 部署为 ASGI 应用，并且将其绑定到 ASGI-able Web 服务器。

## Sanic 服务器

运行Sanic的主要方式是使用包含 [CLI](#sanic-clik).

```sh
sanic path.to.server:app
```

在这个示例中，已指示Sanic寻找一个名为 `path.to.server` 的 python 模块。 在该模块中，它将寻找一个叫做`app`的全球变量，它应该是`Sanic(...)`的实例。

```python
# ./path/to/server.py
来自Sanic import Sanic, Request, json

app = Sanic("TestApp")

@app.get("/")
async def handler(request):
    return json({"foo": "bar"})
```

你也可以下拉到[较低级别的 API](#low-level-apprun)来调用 `app.run` 作为脚本。 然而，如果您选择此选项，您应该比较舒适地处理可能因“多处理”而产生的问题。

### A. 工 人

.. 列:

```
By default, Sanic runs a main process and a single worker process (see [worker manager](./manager.md) for more details).

To crank up the juice, just specify the number of workers in the run arguments.
```

.. 列:

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --workers=4
```
````

Sanic将自动旋转多个进程和它们之间的路由流量。 我们推荐像您现有的处理器一样多的工人。

.. 列:

```
获取最大CPU性能的最简单方法是使用“--fast”选项。 由于系统限制，此操作将自动运行最大数量的员工。

*在 v21.12* 中添加。
```

.. 列:

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --fast
```
````

在第22.9版中，Sanic引入了一个新的工人经理，以便在开发服务机和生产服务机之间提供更大的一致性和灵活性。 阅读[关于经理](./manager.md)了解更多有关工人的详情。

.. 列:

```
If you only want to run Sanic with a single process, specify `single_process` in the run arguments. This means that auto-reload, and the worker manager will be unavailable.

*Added in v22.9*
```

.. 列:

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --sin-process
```
````

### 通过命令运行

#### Sanic CLI

使用 'sanic --help' 查看所有选项。

.. attrs::
:title: Sanic CLI help output
:class: details

````
```text
$ sanic --help

   ▄███ █████ ██      ▄█▄      ██       █   █   ▄██████████
  ██                 █   █     █ ██     █   █  ██
   ▀███████ ███▄    ▀     █    █   ██   ▄   █  ██
               ██  █████████   █     ██ █   █  ▄▄
  ████ ████████▀  █         █  █       ██   █   ▀██ ███████

 To start running a Sanic application, provide a path to the module, where
 app is a Sanic() instance:

     $ sanic path.to.server:app

 Or, a path to a callable that returns a Sanic() instance:

     $ sanic path.to.factory:create_app --factory

 Or, a path to a directory to run as a simple HTTP server:

     $ sanic ./path/to/static --simple

Required
========
  Positional:
    module              Path to your Sanic app. Example: path.to.server:app
                        If running a Simple Server, path to directory to serve. Example: ./

Optional
========
  General:
    -h, --help          show this help message and exit
    --version           show program's version number and exit

  Application:
    --factory           Treat app as an application factory, i.e. a () -> <Sanic app> callable
    -s, --simple        Run Sanic as a Simple Server, and serve the contents of a directory
                        (module arg should be a path)
    --inspect           Inspect the state of a running instance, human readable
    --inspect-raw       Inspect the state of a running instance, JSON output
    --trigger-reload    Trigger worker processes to reload
    --trigger-shutdown  Trigger all processes to shutdown

  HTTP version:
    --http {1,3}        Which HTTP version to use: HTTP/1.1 or HTTP/3. Value should
                        be either 1, or 3. [default 1]
    -1                  Run Sanic server using HTTP/1.1
    -3                  Run Sanic server using HTTP/3

  Socket binding:
    -H HOST, --host HOST
                        Host address [default 127.0.0.1]
    -p PORT, --port PORT
                        Port to serve on [default 8000]
    -u UNIX, --unix UNIX
                        location of unix socket

  TLS certificate:
    --cert CERT         Location of fullchain.pem, bundle.crt or equivalent
    --key KEY           Location of privkey.pem or equivalent .key file
    --tls DIR           TLS certificate folder with fullchain.pem and privkey.pem
                        May be specified multiple times to choose multiple certificates
    --tls-strict-host   Only allow clients that send an SNI matching server certs

  Worker:
    -w WORKERS, --workers WORKERS
                        Number of worker processes [default 1]
    --fast              Set the number of workers to max allowed
    --single-process    Do not use multiprocessing, run server in a single process
    --legacy            Use the legacy server manager
    --access-logs       Display access logs
    --no-access-logs    No display access logs

  Development:
    --debug             Run the server in debug mode
    -r, --reload, --auto-reload
                        Watch source directory for file changes and reload on changes
    -R PATH, --reload-dir PATH
                        Extra directories to watch and reload on changes
    -d, --dev           debug + auto reload
    --auto-tls          Create a temporary TLS certificate for local development (requires mkcert or trustme)

  Output:
    --coffee            Uhm, coffee?
    --no-coffee         No uhm, coffee?
    --motd              Show the startup display
    --no-motd           No show the startup display
    -v, --verbosity     Control logging noise, eg. -vv or --verbosity=2 [default 0]
    --noisy-exceptions  Output stack traces for all exceptions
    --no-noisy-exceptions
                        No output stack traces for all exceptions

```
````

#### 作为一个模块

.. 列:

```
Sanic 应用程序也可以直接调用为模块。
```

.. 列:

````
```bash
python -m sanic server.app --host=0.0.0.0 --port=1337 --workers=4
```
````

#### 使用一个工厂。

一个非常常见的解决办法是开发你的应用程序_不是_作为一个全局变量，而是使用出厂模式。 在这个上下文中，"factory" 是指返回一个 `Sanic(...)` 实例的函数。

.. 列:

```
假定你在 `server.py` 里有这个内容
```

.. 列:

````
```python
from sanic import Sanic

def create_app() -> Sanic:
    app = Sanic("MyApp")

    return app
```
````

.. 列:

```
您现在可以在 CLI 中明确地将其作为一个工厂来运行此应用程序：
```

.. 列:

````
```sh
sanic server:create_app --frant
```
Or, 明示类似于:
```sh
sanic "server:create_app()"
```
Or, 默示类似于：
```sh
sanic server:create_app
```

*默示命令添加于v23.3*
````

### 低级别 `app.run`

当使用 `app.run` 时，你会像其他脚本一样调用 Python 文件。

.. 列:

```
`app.run`必须正确嵌套在一个名称的主块内。
```

.. 列:

````
```python
# server.py
app = Sanic("MyApp")

if __name__ == "__main__":
    app.run()
```
````

.. 危险：:

````
Be *careful* when using this pattern. A very common mistake is to put too much logic inside of the `if __name__ == "__main__":` block.

🚫 This is a mistake

```python
from sanic import Sanic
from my.other.module import bp

app = Sanic("MyApp")

if __name__ == "__main__":
    app.blueprint(bp)
    app.run()
```

If you do this, your [blueprint](../best-practices/blueprints.md) will not be attached to your application. This is because the `__main__` block will only run on Sanic's main worker process, **NOT** any of its [worker processes](../deployment/manager.md). This goes for anything else that might impact your application (like attaching listeners, signals, middleware, etc). The only safe operations are anything that is meant for the main process, like the `app.main_*` listeners.

Perhaps something like this is more appropriate:

```python
from sanic import Sanic
from my.other.module import bp

app = Sanic("MyApp")

if __name__ == "__mp_main__":
    app.blueprint(bp)
elif __name__ == "__main__":
    app.run()
```
````

要使用低级别的 `run` API，在定义一个 `sanic.Sanic` 实例后，我们可以使用以下关键词参数来调用运行方法：

|                     参数                    |       默认设置      | 描述                                                                                     |
| :---------------------------------------: | :-------------: | :------------------------------------------------------------------------------------- |
|                   **主机**                  |  `"127.0.0.1"`  | 服务器主机地址已开启。                                                                            |
|                   **端口**                  |      `8000`     | 服务器端口已开启。                                                                              |
|                  **unix**                 |       `无`       | 服务器主机的 Unix 套接字名称 (而不是TCP)。                                         |
|                  **dev**                  |     `False`     | 等于`debug=True`和`auto_reload=True`。                                                     |
|                 **debug**                 |     `False`     | 启用调试输出 (慢速服务器)。                                                     |
|                  **ssl**                  |       `无`       | SSLContext for SSL 加密 (s)。                                          |
|                  **sock**                 |       `无`       | Socket 让服务器接受连接。                                                                       |
|                **Workers**                |       `1`       | 要生成的工序数量。 无法快速使用。                                                                      |
|                   **循环**                  |       `无`       | 一个异步兼容的事件循环。 如果没有具体说明，Sanic将创建自己的事件循环。                                                 |
|                **protocol**               |  `HttpProtocol` | asyncio.protocol的子类。                                                   |
|                   **版本**                  | `HTTPVERSION_1` | 要使用的 HTTP 版本 (`HTTP.VERSION_1` 或 `HTTP.VERSION_3`). |
|    **access_log**    |      `True`     | 启用处理请求的日志 (大大减慢服务器)。                                                |
|    **auto_reload**   |       `无`       | 启用源目录自动重新加载。                                                                           |
|    **reload_dir**    |       `无`       | 自动读取加载器应该监视的目录路径或路径列表。                                                                 |
| **noisy_exceptions** |       `无`       | 是否设置全局噪音异常。 没有表示离开为默认值。                                                                |
|                  **motd**                 |      `True`     | 是否显示启动消息。                                                                              |
|   **motd_display**   |       `无`       | 在启动消息中显示额外的密钥/值信息                                                                      |
|                  **fast**                 |     `False`     | 是否最大化工人工序。  无法与工人一起使用。                                                                 |
|                  **详细化**                  |       `0`       | 日志的详细级别。 最大值为 2。                                                                       |
|      **自动_tls**      |     `False`     | 是否为本地开发自动创建TLS证书。 不是生产的。                                                               |
|                  **单独处理**                 |     `False`     | 是否在一个过程中运行 Sanic。                                                                      |

.. 列:

```
例如，我们可以关闭访问日志以提高性能并绑定到自定义主机和端口。
```

.. 列:

````
```python
# server.py
app = Sanic("MyApp")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1337, access_log=False)
```
````

.. 列:

```
现在，只需执行 'app.run(...)' 的 python 脚本
```

.. 列:

````
```sh
python server.py
```
````

对于稍微高级的实现来说，我们很高兴知道`app.run`会调用`app.preparre`和`Sanic.serve`。

.. 列:

```
因此，这些标准等同于：
```

.. 列:

````
```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1337, access_log=False)
```
```python
if __name__ == "__main__":
    app.prepare(host='0.0.0.0', port=1337, access_log=False)
    Sanic.serve()
```
````

.. 列:

```
如果您需要将应用程序绑定到多个端口，这将是有用的。
```

.. 列:

````
```python
if __name__ == "__main__":
    app1.prepare(host='0.0.0.0', port=9990)
    app1.prepare(host='0.0.0.0', port=9991)
    app2.prepare(host='0.0.0.0', port=5555)
    Sanic.serve()
```
````

### Sanic 简单服务器

.. 列:

```
有时，你只是一个需要服务的静态文件目录。 这尤其可以方便快速站立本地主机服务器。 一个简单的服务器的神秘船，你只需要在一个目录上指明。
```

.. 列:

````
```sh
sanic ./path/to/dir --imple
```
````

.. 列:

```
这也可以与自动重新加载配对。
```

.. 列:

````
```sh
sanic ./path/to/dir --simple --reload --reload-dir=./path/to/dir
```
````

\*添加于 v21.6 \*

### 守护进程模式

.. 新：v25.12

```
此功能已添加到版本25.12
```

.. 列:

```
Sanic 可以作为后台守护进程运行。使用 "-D" 或 "--daemon" 标志在后台启动服务器。
```

.. 列:

````
```sh
sanic path.to.server:app --daemon
sanic path.to.server:app -D
```
````

.. 列:

```
您可以通过额外命令管理守护进程：
```

.. 列:

````
```sh
sanic path.to.server:app 状态 # 检查是否运行
sanic path.to.server:app stop # 停止守护程序
```
````

.. 列:

```
守护进程配置有其他选项：
```

.. 列:

````
```sh
sanic path.to.server:app -D --pidfile=/var/run/sanic.pid
sanic path.to.server:app -D --logfile=/var/log/sanic.log
sanic path.to.server:app -D --user=www-data
sanic path.to.server:app -D --group=www-data
```
````

低级别命令也可用来管理由 PID 进行的过程：

```sh
sanic kill --pid=<PID>
sanic kill --pidfile=/var/run/sanic.pid
sanic status --pid=<PID>
sanic status --pidfile=/var/run/sanic.pid
```

_添加于 v25.12_

### HTTP/3

Sanic 服务器使用 [aioquic](https://github.com/aiortc/aioquic) 提供 HTTP/3 支持。 此 \*\*must \*\* 安装后才能使用 HTTP/3：

```sh
pip install sanic aioquic
```

```sh
pip install sanic[http3]
```

要启动 HTTP/3，您必须在运行应用程序时明确请求它。

.. 列:

````
```sh
sanic path.to.server:app --http=3
```

```sh
sanic path.to.server:app -3
```
````

.. 列:

````
```python
app.run(version=3)
```
````

要同时运行 HTTP/3 和 HTTP/1.1 服务器，您可以使用 v22.3 中引入的 [应用程序多服务器](../../release-notes/2022/v22.3.md#application-multi-serve)。 这将自动添加一个 [Alt-Svc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ Alt-Svc) 头到您的 HTTP/1.1 请求让客户端知道它也是可用的 HTTP/3。

.. 列:

````
```sh
sanic path.to.server:app --http=3 --http=1
```

```sh
sanic path.to.server:app -3 -1
```
````

.. 列:

````
```python
app.preparre(version=3)
app.preparre(version=1)
Sanic.serve()
```
````

因为HTTP 3 需要 TLS，您不能在没有TLS 证书的情况下启动 HTTP/3 服务器。 您应该[自己设置它](../how-to/tls.md) 或者在 `DEBUG` 模式下使用 `mkcert` 。 目前，HTTP/3 的自动TLS设置与 `trustme` 不兼容。 更多详细信息请访问 [development](./development.md)。

_添加于 v22.6_

## ASGI

Sanic也是ASGI合规者。 这意味着您可以使用您喜欢的 ASGI web服务器来运行 Sanic。 ASGI的三个主要实施方式是： [Daphne](http://github.com/django/daphne)、 [Uvicorn](https://www.uvicorn.org/)和 [Hypercorn](https://pgjones.gitlab.io/hypercorn/index.html)。

.. 警告：:

```
Daphne不支持ASGI `lifespan` 协议，因此不能用于运行 Sanic。详情请参阅[Issue #264](https://github.com/django/daphne/issues/264)。
```

按照他们的文档来运行他们，但它应该看起来像这样：

```sh
uvicorn myapp:app
```

```sh
超彩应用:app
```

使用ASGI时要注意的几件事：

1. 当使用 Sanic 网络服务器时，websockets 将使用 `websockets` 软件包运行。 在 ASGI 模式下，没有必要使用这个软件包，因为websockets 是在 ASGI 服务器上管理的。
2. ASGI 生命周期协议 <https://asgi.readthedocs.io/en/latest/specs/lifespan.html>，只支持两个服务器事件：启动和关机。 萨里语有四个：启动前、启动后、关闭前和关机。 因此，以ASGI模式， 启动和关闭事件将连续运行，而不是围绕服务器进程开始和结束(因为现在是由 ASGI 服务器控制的)。 因此，最好使用 `after _server_start` 和 `previ_server_stop` 。

### 特里奥文

Sanic在Trio上运行时有实验支持：

```sh
超精彩-k 三次应用：应用
```

## 古尼科恩州

[Gunicorn](http://gunicorn.org/) ("Green Unicorn") 是一个基于UNIX的操作系统的 WSGI HTTP 服务器。 这是一个基于 Ruby Unicorn项目的前叉工人模型。

若要与 Gunicorn一起运行 Sanic 应用程序，您需要使用 [uvicorn]的适配器(https://www.uvicorn.org/)。 确保uvicorn已经安装并运行它与 `uvicorn.workers.UvicornWorker` for Gunicorn worker-class参数：

```sh
gunicorn myapp:app --binding 0.0.0:1337 --worker-classuvicorn.workers.UvicornWorker
```

详见[Gunicorn Docs](http://docs.gunicorn.org/enarage/settings.html#max-requests)。

.. 警告：:

```
通常建议不要使用“gunicorn”，除非你需要它。 Sanic 服务器已经准备好在生产中运行 Sanic。在作出这一选择之前仔细加大您的考虑。 Gunicorn确实提供了许多配置选项，但它不是让Sanic以最快的速度运行的最佳选择。
```

## 业绩考虑

.. 列:

```
在生产中运行时，请确保您关闭“debug”。
```

.. 列:

````
```sh
sanic path.to.server:app
```
````

.. 列:

```
如果您关闭了 "access_log" ，Sanic 也会执行最快的操作。

如果您仍然需要访问日志，但想要享受此性能提升， 考虑使用 [Nginx 作为代理](./../deployment/nginx.md)，并让它处理您的访问记录。 它将比Python可以处理的任何东西快得多。
```

.. 列:

````
```sh
sanic path.to.server:app --no-access-log
```
````

