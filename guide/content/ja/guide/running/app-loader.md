---
title: 動的アプリケーション
---

# 動的アプリケーション

SanicはCLIで動作するように最適化されています。 まだ読んでいない場合は、format@@0(./running.md#sanic-server)を読んで、オプションに慣れるようにしてください。

.. 列::

```
これにはグローバルスコープオブジェクトとして実行することが含まれます...
```

.. 列::

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

.. 列::

```
...または、`Sanic`アプリケーションオブジェクトを作成するファクトリ関数。
```

.. 列::

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

**時々、これは十分ではありません... 🤔**

[v22.9](../release-notes/v22.9.md) で導入されたSanicは、さまざまな[worker processes](./manager.md#how-sanic-server-starts-processes)でアプリケーションを作成する `AppLoader` オブジェクトを持っています。 アプリケーションでより動的なスタートアップ体験を作成する必要がある場合は、これを利用できます。

.. 列::

```
`AppLoader`は、`Sanic`インスタンスを返す呼び出し可能なものを渡すことができます。その`AppLoader`は、APIを実行する低レベルのアプリケーションで使用できます。
```

.. 列::

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

上記の例では、 `AppLoader` は `factory` で作成され、プロセス間で同じアプリケーションのコピーを作成できます。 これを行う場合は、上記の`Sanic.serve`パターンを使用して、作成した`AppLoader`が置き換えられないようにしてください。
