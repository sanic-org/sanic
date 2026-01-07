---
title: サニックエクステンション - Custom
---

# カスタムの拡張機能

独自の拡張機能を作成することは可能です。

バージョン 22.9 は `Extend.register` [method](#extension-preregistration) を追加しました。 これにより、アプリケーションにカスタムの拡張機能を追加することが非常に簡単になります。

## 拡張機能の解剖学

すべてのエクステンションは `Extension` のサブクラスでなければなりません。

### 必須

- `name`: 規約により、名前は全て小文字の文字列です
- `startup`: 拡張機能が追加されたときに実行されるメソッド

### 省略可能

- `label`: MOTD の拡張機能に関する追加情報を返すメソッド
- `included`: 拡張機能を有効にするかどうかを真偽値を返すメソッド (設定状態を確認するために例えば使用できます)

### 例

```python
from sanic import Request, Sanic, json
from sanic_ext import Extend, Extension

app = Sanic(__name__)
app.config.MONITOR = True

class AutoMonitor(Extension):
    name = "automonitor"

    def startup(self, bootstrap) -> None:
        if self.included():
            self.app.before_server_start(self.ensure_monitor_set)
            self.app.on_request(self.monitor)

    @staticmethod
    async def monitor(request: Request):
        if request.route and request.route.ctx.monitor:
            print("....")

    @staticmethod
    async def ensure_monitor_set(app: Sanic):
        for route in app.router.routes:
            if not hasattr(route.ctx, "monitor"):
                route.ctx.monitor = False

    def label(self):
        has_monitor = [
            route
            for route in self.app.router.routes
            if getattr(route.ctx, "monitor", None)
        ]
        return f"{len(has_monitor)} endpoint(s)"

    def included(self):
        return self.app.config.MONITOR

Extend.register(AutoMonitor)

@app.get("/", ctx_monitor=True)
async def handler(request: Request):
    return json({"foo": "bar"})
```

## エクステンションの事前登録

.. 列::

```
`Extend.register` はカスタムエクステンションの追加を簡単にします。
```

.. 列::

````
```python
from sanic_ext import Extend, Extension

class MyCustomExtension(Extension):
    ...

Extend.register(MyCustomExtension())
```
````

_v22.9_に追加されました
