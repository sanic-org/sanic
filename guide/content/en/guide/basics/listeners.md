# Listeners

Sanic provides you with eight (8) opportunities to inject an operation into the life cycle of your application server. This does not include the [signals](../advanced/signals.md), which allow further injection customization.

There are two (2) that run **only** on your main Sanic process (ie, once per call to `sanic server.app`.)

- `main_process_start`
- `main_process_stop`

There are also two (2) that run **only** in a reloader process if auto-reload has been turned on.

- `reload_process_start`
- `reload_process_stop`

*Added `reload_process_start` and `reload_process_stop` in v22.3*

There are four (4) that enable you to execute startup/teardown code as your server starts or closes.

- `before_server_start`
- `after_server_start`
- `before_server_stop`
- `after_server_stop`

The life cycle of a worker process looks like this:

.. mermaid::

    sequenceDiagram
    autonumber
    participant Process
    participant Worker
    participant Listener
    participant Handler
    Note over Process: sanic server.app
    loop
        Process->>Listener: @app.main_process_start
        Listener->>Handler: Invoke event handler
    end
    Process->>Worker: Run workers
    loop Start each worker
        loop
            Worker->>Listener: @app.before_server_start
            Listener->>Handler: Invoke event handler
        end
        Note over Worker: Server status: started
        loop
            Worker->>Listener: @app.after_server_start
            Listener->>Handler: Invoke event handler
        end
        Note over Worker: Server status: ready
    end
    Process->>Worker: Graceful shutdown
    loop Stop each worker
        loop
            Worker->>Listener: @app.before_server_stop
            Listener->>Handler: Invoke event handler
        end
        Note over Worker: Server status: stopped
        loop
            Worker->>Listener: @app.after_server_stop
            Listener->>Handler: Invoke event handler
        end
        Note over Worker: Server status: closed
    end
    loop
        Process->>Listener: @app.main_process_stop
        Listener->>Handler: Invoke event handler
    end
    Note over Process: exit


The reloader process live outside of this worker process inside of a process that is responsible for starting and stopping the Sanic processes. Consider the following example:

```python
@app.reload_process_start
async def reload_start(*_):
    print(">>>>>> reload_start <<<<<<")

@app.main_process_start
async def main_start(*_):
    print(">>>>>> main_start <<<<<<")
```

If this application were run with auto-reload turned on, the `reload_start` function would be called once. This is contrasted with `main_start`, which would be run every time a file is save and the reloader restarts the applicaition process.

## Attaching a listener

.. column::

    The process to setup a function as a listener is similar to declaring a route.

    The currently running `Sanic()` instance is injected into the listener.

.. column::

    ```python
    async def setup_db(app):
        app.ctx.db = await db_setup()

    app.register_listener(setup_db, "before_server_start")
    ```


.. column::

    The `Sanic` app instance also has a convenience decorator.

.. column::

    ```python
    @app.listener("before_server_start")
    async def setup_db(app):
        app.ctx.db = await db_setup()
    ```


.. column::

    Prior to v22.3, both the application instance and the current event loop were injected into the function. However, only the application instance is injected by default. If your function signature will accept both, then both the application and the loop will be injected as shown here.

.. column::

    ```python
    @app.listener("before_server_start")
    async def setup_db(app, loop):
        app.ctx.db = await db_setup()
    ```


.. column::

    You can shorten the decorator even further. This is helpful if you have an IDE with autocomplete.

.. column::

    ```python
    @app.before_server_start
    async def setup_db(app):
        app.ctx.db = await db_setup()
    ```

## Order of execution

Listeners are executed in the order they are declared during startup, and reverse order of declaration during teardown

|                       | Phase           | Order   |
|-----------------------|-----------------|---------|
| `main_process_start`  | main startup    | regular 🙂 ⬇️ |
| `before_server_start` | worker startup  | regular 🙂 ⬇️ |
| `after_server_start`  | worker startup  | regular 🙂 ⬇️ |
| `before_server_stop`  | worker shutdown | 🙃 ⬆️ reverse |
| `after_server_stop`   | worker shutdown | 🙃 ⬆️ reverse |
| `main_process_stop`   | main shutdown   | 🙃 ⬆️ reverse |

Given the following setup, we should expect to see this in the console if we run two workers.

.. column::

    ```python
    @app.listener("before_server_start")
    async def listener_1(app, loop):
        print("listener_1")

    @app.before_server_start
    async def listener_2(app, loop):
        print("listener_2")

    @app.listener("after_server_start")
    async def listener_3(app, loop):
        print("listener_3")

    @app.after_server_start
    async def listener_4(app, loop):
        print("listener_4")

    @app.listener("before_server_stop")
    async def listener_5(app, loop):
        print("listener_5")

    @app.before_server_stop
    async def listener_6(app, loop):
        print("listener_6")

    @app.listener("after_server_stop")
    async def listener_7(app, loop):
        print("listener_7")

    @app.after_server_stop
    async def listener_8(app, loop):
        print("listener_8")
    ```

.. column::

    ```bash
    [pid: 1000000] [INFO] Goin' Fast @ http://127.0.0.1:9999
    [pid: 1000000] [INFO] listener_0
    [pid: 1111111] [INFO] listener_1
    [pid: 1111111] [INFO] listener_2
    [pid: 1111111] [INFO] listener_3
    [pid: 1111111] [INFO] listener_4
    [pid: 1111111] [INFO] Starting worker [1111111]
    [pid: 1222222] [INFO] listener_1
    [pid: 1222222] [INFO] listener_2
    [pid: 1222222] [INFO] listener_3
    [pid: 1222222] [INFO] listener_4
    [pid: 1222222] [INFO] Starting worker [1222222]
    [pid: 1111111] [INFO] Stopping worker [1111111]
    [pid: 1222222] [INFO] Stopping worker [1222222]
    [pid: 1222222] [INFO] listener_6
    [pid: 1222222] [INFO] listener_5
    [pid: 1222222] [INFO] listener_8
    [pid: 1222222] [INFO] listener_7
    [pid: 1111111] [INFO] listener_6
    [pid: 1111111] [INFO] listener_5
    [pid: 1111111] [INFO] listener_8
    [pid: 1111111] [INFO] listener_7
    [pid: 1000000] [INFO] listener_9
    [pid: 1000000] [INFO] Server Stopped
    ```
    In the above example, notice how there are three processes running:

    - `pid: 1000000` - The *main* process
    - `pid: 1111111` - Worker 1
    - `pid: 1222222` - Worker 2

    *Just because our example groups all of one worker and then all of another, in reality since these are running on separate processes, the ordering between processes is not guaranteed. But, you can be sure that a single worker will **always** maintain its order.*



.. tip:: FYI

    The practical result of this is that if the first listener in `before_server_start` handler setups a database connection, listeners that are registered after it can rely upon that connection being alive both when they are started and stopped.


## ASGI Mode

If you are running your application with an ASGI server, then make note of the following changes:

- `reload_process_start` and `reload_process_stop` will be **ignored**
- `main_process_start` and `main_process_stop` will be **ignored**
- `before_server_start` will run as early as it can, and will be before `after_server_start`, but technically, the server is already running at that point
- `after_server_stop` will run as late as it can, and will be after `before_server_stop`, but technically, the server is still running at that point
