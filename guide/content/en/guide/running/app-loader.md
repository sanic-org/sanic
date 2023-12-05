---
title: Dynamic Applications
---

# Dynamic Applications

Running Sanic has been optimized to work with the CLI. If you have not read it yet, you should read [Running Sanic](./running.md#sanic-server) to become familiar with the options. 

.. column::

    This includes running it as a global scope object...

.. column::

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



.. column::

    ...or, a factory function that creates the `Sanic` application object.

.. column::

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


**Sometimes, this is not enough ... 🤔**

Introduced in [v22.9](../release-notes/v22.9.md), Sanic has an `AppLoader` object that is responsible for creating an application in the various [worker processes](./manager.md#how-sanic-server-starts-processes). You can take advantage of this if you need to create a more dynamic startup experience for your application.

.. column::

    An `AppLoader` can be passed a callable that returns a `Sanic` instance. That `AppLoader` could be used with the low-level application running API.

.. column::

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

In the above example, the `AppLoader` is created with a `factory` that can be used to create copies of the same application across processes. When doing this, you should explicitly use the `Sanic.serve` pattern shown above so that the `AppLoader` that you create is not replaced.
