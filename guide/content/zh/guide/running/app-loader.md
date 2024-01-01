---
title: 动态应用程序
---

# 动态应用程序

正在运行的Sanic已被优化，以配合CLI。 如果你还没有阅读它，你应该阅读 [Running Sanic](./running.md#sanic-server) 来熟悉这些选项。

.. 列:

```
这包括将其作为全局范围对象运行...
```

.. 列:

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

.. 列:

```
...或者创建一个 `Sanic` 应用程序对象的工厂函数。
```

.. 列:

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

**有时候，这还不够... 🤔**

引入于 [v22.9](../release-notes/v22.9.md)，萨尼克有一个`AppLoader` 对象，负责在各种[工人进程](./manager.md#how-sanic-server-starts-process)中创建一个应用程序。 如果你需要为你的应用程序创建一个更动态的启动体验，你可以利用这个机会。

.. 列:

```
一个 `AppLoader` 可以传递一个传唤函数返回一个 `Sanic` 实例。这个`AppLoader` 可以与运行 API 的低级别应用程序一起使用。
```

.. 列:

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

在上面的例子中，`AppLoader` 是用`factory`创建的，它可以用来在整个过程中创建同一应用程序的副本。 在这样做时，您应该明确使用上面显示的 `Sanic.serve` 模式，以便您创建的 `AppLoader` 不会被替换。
