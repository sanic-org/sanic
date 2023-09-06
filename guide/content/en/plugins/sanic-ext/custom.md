# Custom extensions

It is possible to create your own custom extensions.

Version 22.9 added the `Extend.register` [method](#extension-preregistration). This makes it extremely easy to add custom expensions to an application.

## Anatomy of an extension

All extensions must subclass `Extension`.

### Required

- `name`: By convention, the name is an all-lowercase string
- `startup`: A method that runs when the extension is added

### Optional

- `label`: A method that returns additional information about the extension in the MOTD
- `included`: A method that returns a boolean whether the extension should be enabled or not (could be used for example to check config state)

### Example

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

## Extension preregistration

.. column::

    `Extend.register` simplifies the addition of custom extensions.

.. column::

    ```python
    from sanic_ext import Extend, Extension

    class MyCustomExtension(Extension):
        ...

    Extend.register(MyCustomExtension())
    ```

*Added in v22.9*
