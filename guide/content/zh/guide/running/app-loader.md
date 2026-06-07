---
title: 动态应用
---

# 动态应用（Dynamic Applications）

我们优化了通过命令行来运行 Sanic 应用的过程。 如果您还不了解的话，最好在读这篇文章前去看一下 [运行 Sanic](./running.md#sanic-server) 以获取一些详细的信息。

.. column::

```
既可以指定全局变量来启动应用：
```

.. column::

````
```sh
sanic path.to.server:app
```
```python
# server.py
app = Sanic("TestApp")

@app.get("/")
async def handler(request: Request):
    return json({"foo": "bar"})
```
````

.. column::

```
也可以指定某创建 Sanic 对象的工厂函数来启动：
```

.. column::

````
```sh
sanic path.to.server:create_app --factory
```
```python
# server.py
def create_app():
    app = Sanic("TestApp")

    @app.get("/")
    async def handler(request: Request):
        return json({"foo": "bar"})

    return app
```
````

**但有些时候，这还不够... 🤔**

在 [v22.9](../../release-notes/2022/v22.9.md中引入， Sanic 有一个 `AppLoader` 对象，负责在各种[工人进程](./manager.md#how-sanic-server-starts-processes)中创建一个应用程序。 如果你需要更加「动态」的运行体验，那可以用一下它。

.. column::

```
我们可以将一个能够返回 `Sanic` 实例的工厂函数给 `AppLoader` 。`AppLoader` 可以和更底层的运行应用的 API 一起使用。
```

.. column::

````
```python
import sys
from functools import partial

from sanic import Request, Sanic, json
from sanic.worker.loader import AppLoader

def attach_endpoints(app: Sanic):
    @app.get("/")
    async def handler(request: Request):
        return json({"app_name": request.app.name})

def create_app(app_name: str) -> Sanic:
    app = Sanic(app_name)
    attach_endpoints(app)
    return app

if __name__ == "__main__":
    app_name = sys.argv[-1]
    loader = AppLoader(factory=partial(create_app, app_name))
    app = loader.load()
    app.prepare(port=9999, dev=True)
    Sanic.serve(primary=app, app_loader=loader)
```
```sh
python path/to/server.py MyTestAppName
```
````

在这个例子中，`AppLoader` 与 `factory` 传入的可用于在不同进程中创建同一应用的拷贝的函数一起被创建。 然后您需要显式地使用 `Sanic.serve` ，这样您的 `AppLoader` 就不会被自动生成的应用替换。
