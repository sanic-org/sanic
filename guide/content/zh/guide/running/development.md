# 贸易和发展会议

应该提到的第一件事是，集成到 Sanic 的 web 服务器是 **不是** 开发服务器。

它已准备就绪，除非您在调试模式下启用\*。

## 调试模式

通过设置调试模式，Sanic将会在其输出中更详细，并将禁用几个运行时的优化。

```python
# server.py
from sanic import Sanic
from sanic.response import json

app = Sanic(__name__)

@app.route("/")
async def hello_world(request):
    return json({"hello": "world"})
```

```sh
sanic server:app --host=0.0.0.0 --port=1234 --debug
```

.. 危险：:

```
Sanic's debug mode will slow down the server's performance, and is **NOT** intended for production environments.

**DO NOT** enable debug mode in production.
```

## 自动重新加载

.. 列:

```
Sanic 提供了一种启用或禁用自动重新加载器的方式。 启用它的最简单方式是使用 CLI 的 `--reload` 参数来激活自动重新加载。 每次更改 Python 文件，读取器将自动重启您的应用程序。 正在开发时这非常方便。

... 注意： 

    读取器仅在使用 Sanic's 的[工人经理](.) 时才可用。 manager.md. 如果您已禁用它使用 "--lin-process" ，则读取器将不会对您开放。
```

.. 列:

````
```sh
sanic path.to:app --reload
``
你也可以使用短暂属性
```sh
sanic path.to:app -r
```
````

.. 列:

```
如果你有额外的目录，你想要在文件保存时自动重新加载 (例如) 一个 HTML 模板的目录，您可以使用 "--reload-dir" 添加。
```

.. 列:

````
```sh
sanic path.to:app --reload --reload-dir=/path/to/templates
```
Or multiple directories, shown here using the shorthand properties
```sh
sanic path.to:app -r -R /path/to/one -R /path/to/two
```
````

## Development REPL

Sanic CLI 带有一个 REPL (又名“读-写循环”)，可用来与您的应用程序进行交互。 这对调试和测试非常有用。 一个 REPL 是当你在没有任何参数的情况下运行 `python` 时得到的交互式外壳。

.. 列:

```
你可以将 "--repli" 参数传递到 Sanic CLI 来启动 REPL
```

.. 列:

````
```sh
sanic path.to.server:app --repl
```
````

.. 列:

```
也许更方便的是，当你运行`--dev`时，萨尼克会自动为你启动REPL。 然而，在这种情况下，你可能会在实际启动REPL之前被提示按“ENTER”键。
```

.. 列:

````
```sh
sanic path.to.server:app --dev
```
````

![](/assets/images/repli.png)

如上文截图所示，REPL将自动为全局命名空间添加几个变量。 它们是：

- `app` - Sanic 应用程序实例。 这是传递到 `sanic` CLI 的相同实例。
- `sanic` - `sanic` 模块。 这是在您运行 "import sanic" 时导入的同一个模块。
- `do` - 一个将创建模拟`Request`对象并将其传递给您的应用程序的函数。 这对测试你来自REPL的申请非常有用。
- `client` - 一个`httpx.glient`的实例被配置为向您的应用程序提出请求。 这对测试你来自REPL的申请非常有用。 **注意：** 只有在你的环境中安装了 `httpx` 时，这才是可用的。

### Async/Awaw 支持

.. 列:

```
REPL 支持 `async`/`await` 语法。这意味着你可以使用 `await` 来等待异步操作完成。 这有助于测试异步代码。
```

.. 列:

````
```python
>>> > 等待 app.ctx.db.fetchval("SELECT 1")
1 
```
````

### `app`变量

你需要记住，`app`变量是你的应用程序实例，因为它是在REPL启动时存在的。 它是运行CLI 命令时加载的实例。 这意味着对你的源代码的任何更改，然后在工人中重新加载，都不会反映在`app`变量中。 如果你想要与重新加载的应用进行交互，你需要重新启动REPL。

然而，访问REPL中的原始应用程序以进行临时测试和调试也非常有用。

### "客户端" 变量

当 [httpx](https://www.python-httpx.org/) 安装在您的环境中时，"client" 变量将可在REPL中找到。 这是一个 `httpxClient` 的实例，它被配置为向您正在运行的应用程序提出请求。

.. 列:

```
若要使用它，只需调用客户端上的 HTTP 方法之一。请参阅[httpx documentation](https://www.python-httpx.org/api/#client)获取更多信息。
```

.. 列:

````
```python
>>> client.get("/")
<Response [200 OK]>
```
````

### `do`函数

正如上文所讨论的那样，“app”实例就像启动REPL时那样存在，并且在REPL内部进行了修改。 导致服务器重新加载的实例的任何更改都不会反映在`app`变量中。 这是`do`函数的位置。

让我们说你已经修改了你在REPL中的应用程序以添加一条新的路由：

```python
>>> @app.get("/new-route")
... async def new_route(request):
... return sanic.json({"hello": "world"})
...
>>
```

您可以使用 `do` 函数模拟请求，并将其传递到应用程序中，仿佛它是一个真正的 HTTP 请求。 这将允许您测试您的新路线，而不必重新启动REPL。

```python
>>>>正在等待 do("/new-route")
结果(request=<Request: GET /new-route>, response=<JSONResponse: 200 application/json>)
```

`do`函数返回一个包含 `Request` 和 `Response` 对象的 `Result` 对象。 这是一个 `NamedTuple` ，因此您可以按名称访问值：

```python
>>>> 结果 = 等待完成("/new-route")
>>>> result.request
<Request: GET /new-route>
>>> result.reply
<JSONResponse: 200 application/json>
```

或者，通过摧毁管：

```python
>>>>请求, 应答 = 等待完成("/new-route")
>>>>>>>>请求
<Request: GET /new-route>
>>>>>>>> 应答
<JSONResponse: 200 application/json>
```

### 什么时候使用 `do` 和 `client`?

.. 列:

```
**Use `do` when ...**

- You want to test a route that does not exist in the running application
- You want to test a route that has been modified in the REPL
- You make a change to your application inside the REPL
```

.. 列:

```
**Use `client` when ...**

- You want to test a route that already exists in the running application
- You want to test a route that has been modified in your source code
- You want to send an actual HTTP request to your application
```

_添加于 v23.12_

## 完成开发模式

.. 列:

```
如果你想要处于调试模式**和** 运行自动重新加载器，你可以通过 `dev=True`。 这相当于**调试+自动重新加载+重新加载**。

*添加于v22.3*
```

.. 列:

````
```sh
sanic path.to:app --dev
``
你也可以使用短暂属性
```sh
sanic path.to:app -d
```
````

在 v23.12 `--dev` 旗帜上添加了能够启动一个REPL 详见[Development REPL](./development.md#development-reply)部分。

到 v23.12，`--dev` 旗帜大致等于`--debug --reload --reload --repli`。 使用 "--dev" 将需要你明确开头点击 "ENTER"，然后通过 "--repli" 旗帜明确开头。
在 v23.12之前，"--dev" 旗帜更类似于“--debug --reload\`”。

.. 列:

```
如果你想要在使用 --dev' 标志时禁用REPL，你可以通过 "--no-reply "。
```

.. 列:

````
```sh
sanic path.to:app --dev --no-repl
```
````

## 自动TLS证书

当在 `DEBUG` 模式下运行时，您可以要求Sanic 处理本地主机临时TLS 证书的设置。 如果您想要访问 'https://' 本地发展环境，这将是很有帮助的。

此功能由 [mkcert](https://github.com/FiloSottile/mkcert) 或 [trustme](https://github.com/python-trio/trustme) 提供。 两者都是好的选择，但也有一些差异。 `Trustme` 是一个 Python 库，可以安装在 `pip` 里的环境。 这使得可以轻松地处理Envrionment，但在运行 HTTP/3 服务器时是不兼容的。 `mkcert`可能是一个更多的安装过程，但可以安装本地CA并使其更容易使用。

.. 列:

```
您可以通过设置 `config.LOCAL_CERT_CREATOR` 选择哪个平台。当设置为 `auto`时，它将选择任何一个选项，如果可能则选择`mkcert`。
```

.. 列:

````
```python
app.config.LOCAL_CERT_CREATOR= "auto"
app.config.LOCAL_CERT_CREATOR= "mkcert"
app.config.LOCAL_CERT_CREATOR= "trustme"
```
````

.. 列:

```
Sanic 服务器运行时间可以启用自动TLS：
```

.. 列:

````
```sh
sanic path.to.server:app --auto-tls --debug
```
````

.. 警告：:

```
本地的 TLS 证书（就像`mkcert` 和 `trustme` 生成的证书一样）**不适用于生产环境。 如果您不熟悉如何获得*真实*TLS证书，请签出[如何...](../how-to/tls.md)。
```

_添加于 v22.6_
