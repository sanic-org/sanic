---
title: Sanic 扩展 - 自定义
---

# 自定义扩展

可以创建您自己的自定义扩展。

22.9版本添加了 `Extend.register` [method](#extension-preregistration)。 这使得向应用程序添加自定义扩展变得非常容易。

## 扩展的解析度

所有扩展必须是子类“扩展”。

### 必填

- `name`: 按惯例, 名称是一个小写字符串
- `启动`: 添加扩展时运行的方法

### 可选的

- `label`：返回MOTD中有关扩展的额外信息的方法
- `included`：返回是否启用扩展名布尔值的方法 (可以用来检查配置状态)

### 示例

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

## 扩展预注册

.. 列:

```
`Extend.register` 简化了自定义扩展的添加。
```

.. 列:

````
```python
from sanic_ext import Extend, extension

class MyCustomExtension(Extension):


Extend.register(MyCustomExtencion())
```
````

_添加于 v22.9_
