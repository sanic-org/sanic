---
title: Worker Manager
---

# Worker Manager

The worker manager and its functionality was introduced in version 22.9.

*The details of this section are intended for more advanced usages and **not** necessary to get started.*

The purpose of the manager is to create consistency and flexibility between development and production environments. Whether you intend to run a single worker, or multiple workers, whether with, or without auto-reload: the experience will be the same.

In general it looks like this:

![](https://user-images.githubusercontent.com/166269/178677618-3b4089c3-6c6a-4ecc-8d7a-7eba2a7f29b0.png)

When you run Sanic, the main process instantiates a `WorkerManager`. That manager is in charge of running one or more `WorkerProcess`. There generally are two kinds of processes:

- server processes, and
- non-server processes.

For the sake of ease, the User Guide generally will use the term "worker" or "worker process" to mean a server process, and "Manager" to mean the single worker manager running in your main process.

## How Sanic Server starts processes

Sanic will start processes using the [spawn](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods) start method. This means that for every process/worker, the global scope of your application will be run on its own thread. The practical impact of this that *if* you do not run Sanic with the CLI, you will need to nest the execution code inside a block to make sure it only runs on `__main__`.

```python
if __name__ == "__main__":
    app.run()
```

If you do not, you are likely to see an error message like this:

```
sanic.exceptions.ServerError: Sanic server could not start: [Errno 98] Address already in use.

This may have happened if you are running Sanic in the global scope and not inside of a `if __name__ == "__main__"` block.

See more information: https://sanic.dev/en/guide/deployment/manager.html#how-sanic-server-starts-processes
```

The likely fix for this problem is nesting your Sanic run call inside of the `__name__ == "__main__"` block. If you continue to receive this message after nesting, or if you see this while using the CLI, then it means the port you are trying to use is not available on your machine and you must select another port.

### Starting a worker

All worker processes *must* send an acknowledgement when starting. This happens under the hood, and you as a developer do not need to do anything. However, the Manager will exit with a status code `1` if one or more workers do not send that `ack` message, or a worker process throws an exception while trying to start. If no exceptions are encountered, the Manager will wait for up to thirty (30) seconds for the acknowledgement.

.. column::

    In the situation when you know that you will need more time to start, you can monkeypatch the Manager. The threshold does not include anything inside of a listener, and is limited to the execution time of everything in the global scope of your application.

    If you run into this issue, it may indicate a need to look deeper into what is causing the slow startup.

.. column::

    ```python
    from sanic.worker.manager import WorkerManager

    WorkerManager.THRESHOLD = 100  # Value is in 0.1s
    ```

See [worker ack](#worker-ack) for more information.

.. column::

    As stated above, Sanic will use [spawn](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods) to start worker processes. If you would like to change this behavior and are aware of the implications of using different start methods, you can modify as shown here.

.. column::

    ```python
    from sanic import Sanic

    Sanic.start_method = "fork"
    ```


### Worker ack

When all of your workers are running in a subprocess a potential problem is created: deadlock. This can occur when the child processes cease to function, but the main process is unaware that this happened. Therefore, Sanic servers will automatically send an `ack` message (short for acknowledge) to the main process after startup.

In version 22.9, the `ack` timeout was short and limited to `5s`. In version 22.12, the timeout was lengthened to `30s`. If your application is shutting down after thirty seconds then it might be necessary to manually increase this threshhold.

.. column::

    The value of `WorkerManager.THRESHOLD` is in `0.1s` increments. Therefore, to set it to one minute, you should set the value to `600`.

    This value should be set as early as possible in your application, and should ideally happen in the global scope.  Setting it after the main process has started will not work.

.. column::

    ```python
    from sanic.worker.manager import WorkerManager

    WorkerManager.THRESHOLD = 600
    ```

### Zero downtime restarts

By default, when restarting workers, Sanic will teardown the existing process first before starting a new one. 

If you are intending to use the restart functionality in production then you may be interested in having zero-downtime reloading. This can be accomplished by forcing the reloader to change the order to start a new process, wait for it to [ack](#worker-ack), and then teardown the old process.

.. column::

    From the multiplexer, use the `zero_downtime` argument

.. column::

    ```python
    app.m.restart(zero_downtime=True)
    ```

*Added in v22.12*

## Using shared context between worker processes

Python provides a few methods for [exchanging objects](https://docs.python.org/3/library/multiprocessing.html#exchanging-objects-between-processes), [synchronizing](https://docs.python.org/3/library/multiprocessing.html#synchronization-between-processes), and [sharing state](https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes) between processes. This usually involves objects from the `multiprocessing` and `ctypes` modules.

If you are familiar with these objects and how to work with them, you will be happy to know that Sanic provides an API for sharing these objects between your worker processes. If you are not familiar, you are encouraged to read through the Python documentation linked above and try some of the examples before proceeding with implementing shared context.

Similar to how [application context](../basics/app.md#application-context) allows an applicaiton to share state across the lifetime of the application with `app.ctx`, shared context provides the same for the special objects mentioned above. This context is available as `app.shared_ctx` and should **ONLY** be used to share objects intended for this purpose.

The `shared_ctx` will:

- *NOT* share regular objects like `int`, `dict`, or `list`
- *NOT* share state between Sanic instances running on different machines
- *NOT* share state to non-worker processes
- **only** share state between server workers managed by the same Manager

Attaching an inappropriate object to `shared_ctx` will likely result in a warning, and not an error. You should be careful to not accidentally add an unsafe object to `shared_ctx` as it may not work as expected. If you are directed here because of one of those warnings, you might have accidentally used an unsafe object in `shared_ctx`.

.. column::

    In order to create a shared object you **must** create it in the main process and attach it inside of the `main_process_start` listener.

.. column::

    ```python
    from multiprocessing import Queue

    @app.main_process_start
    async def main_process_start(app):
        app.shared_ctx.queue = Queue()
    ```

Trying to attach to the `shared_ctx` object outside of this listener may result in a `RuntimeError`.

.. column::

    After creating the objects in the `main_process_start` listener and attaching to the `shared_ctx`, they will be available in your workers wherever the application instance is available (example: listeners, middleware, request handlers).

.. column::

    ```python
    from multiprocessing import Queue

    @app.get("")
    async def handler(request):
        request.app.shared_ctx.queue.put(1)
        ...
    ```

## Access to the multiplexer

The application instance has access to an object that provides access to interacting with the Manager and other worker processes. The object is attached as the `app.multiplexer` property, but it is more easily accessed by its alias: `app.m`.

.. column::

    For example, you can get access to the current worker state.

.. column::

    ```python
    @app.on_request
    async def print_state(request: Request):
        print(request.app.m.name)
        print(request.app.m.pid)
        print(request.app.m.state)
    ```
    ```
    Sanic-Server-0-0
    99999
    {'server': True, 'state': 'ACKED', 'pid': 99999, 'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), 'starts': 2, 'restart_at': datetime.datetime(2022, 10, 1, 0, 0, 12, 861332, tzinfo=datetime.timezone.utc)}
    ```


.. column::

    The `multiplexer` also has access to terminate the Manager, or restart worker processes

.. column::

    ```python
    # shutdown the entire application and all processes
    app.m.name.terminate()

    # restart the current worker only
    app.m.name.restart()

    # restart specific workers only (comma delimited)
    app.m.name.restart("Sanic-Server-4-0,Sanic-Server-7-0")

    # restart ALL workers
    app.m.name.restart(all_workers=True)  # Available v22.12+
    ```

## Worker state

.. column::

    As shown above, the `multiplexer` has access to report upon the state of the current running worker. However, it also contains the state for ALL processes running.

.. column::

    ```python
    @app.on_request
    async def print_state(request: Request):
        print(request.app.m.workers)
    ```
    ```
    {
        'Sanic-Main': {'pid': 99997},
        'Sanic-Server-0-0': {
            'server': True,
            'state': 'ACKED',
            'pid': 9999,
            'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
            'starts': 2,
            'restart_at': datetime.datetime(2022, 10, 1, 0, 0, 12, 861332, tzinfo=datetime.timezone.utc)
        },
        'Sanic-Reloader-0': {
            'server': False,
            'state': 'STARTED',
            'pid': 99998,
            'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
            'starts': 1
        }
    }
    ```

The possible states are:

- `NONE` - The worker has been created, but there is no process yet
- `IDLE` - The process has been created, but is not running yet
- `STARTING` - The process is starting
- `STARTED` - The process has started
- `ACKED` - The process has started and sent an acknowledgement (usually only for server processes)
- `JOINED` - The process has exited and joined the main process
- `TERMINATED` - The process has exited and terminated
- `RESTARTING` - The process is restarting
- `FAILED` - The process encountered an exception and is no longer running
- `COMPLETED` - The process has completed its work and exited successfully

## Built-in non-server processes

As mentioned, the Manager also has the ability to run non-server processes. Sanic comes with two built-in types of non-server processes, and allows for [creating custom processes](#running-custom-processes).

The two built-in processes are

- the [auto-reloader](./development.md#automatic-reloader), optionally enabled to watch the file system for changes and trigger a restart
- [inspector](#inspector), optionally enabled to provide external access to the state of the running instance

## Inspector

Sanic has the ability to expose the state and the functionality of the `multiplexer` to the CLI. Currently, this requires the CLI command to be run on the same machine as the running Sanic instance. By default the inspector is disabled.

.. column::

    To enable it, set the config value to `True`.

.. column::

    ```python
    app.config.INSPECTOR = True
    ```

You will now have access to execute any of these CLI commands:

```
sanic inspect reload                      Trigger a reload of the server workers
sanic inspect shutdown                    Shutdown the application and all processes
sanic inspect scale N                     Scale the number of workers to N
sanic inspect <custom>                    Run a custom command
```

![](https://user-images.githubusercontent.com/166269/190099384-2f2f3fae-22d5-4529-b279-8446f6b5f9bd.png)

.. column::

    This works by exposing a small HTTP service on your machine. You can control the location using configuration values:

.. column::

    ```python
    app.config.INSPECTOR_HOST =  "localhost"
    app.config.INSPECTOR_PORT =  6457
    ```

[Learn more](./inspector.md) to find out what is possible with the Inspector.

## Running custom processes

To run a managed custom process on Sanic, you must create a callable. If that process is meant to be long-running, then it should handle a shutdown call by a `SIGINT` or `SIGTERM` signal.

.. column::

    The simplest method for doing that in Python will be to just wrap your loop in `KeyboardInterrupt`.

    If you intend to run another application, like a bot, then it is likely that it already has capability to handle this signal and you likely do not need to do anything.

.. column::

    ```python
    from time import sleep

    def my_process(foo):
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            print("done")
    ```


.. column::

    That callable must be registered in the `main_process_ready` listener. It is important to note that is is **NOT** the same location that you should register [shared context](#using-shared-context-between-worker-processes) objects.

.. column::

    ```python
    @app.main_process_ready
    async def ready(app: Sanic, _):
    #   app.manager.manage(<name>, <callable>, <kwargs>)
        app.manager.manage("MyProcess", my_process, {"foo": "bar"})
    ```

### Transient v. durable processes

.. column::

    When you manage a process with the `manage` method, you have the option to make it transient or durable. A transient process will be restarted by the auto-reloader, and a durable process will not.
    
    By default, all processes are durable.
    
.. column::

    ```python
    @app.main_process_ready
    async def ready(app: Sanic, _):
        app.manager.manage(
            "MyProcess",
            my_process,
            {"foo": "bar"},
            transient=True,
        )
    ```


### Tracked v. untracked processes

Out of the box, Sanic will track the state of all processes. This means that you can access the state of the process from the [multiplexer](./manager#access-to-the-multiplexer) object, or from the [Inspector](./manager#inspector).

See [worker state](./manager#worker-state) for more information.
    
Sometimes it is helpful to run background processes that are not long-running. You run them once until completion and then they exit. Upon completion, they will either be in `FAILED` or `COMPLETED` state.
    
.. column::

    When you are running a non-long-running process, you can opt out of tracking it by setting `tracked=False` in the `manage` method. This means that upon completion of the process it will be removed from the list of tracked processes. You will only be able to check the state of the process while it is running.
    
.. column::

    ```python
    @app.main_process_ready
    async def ready(app: Sanic, _):
        app.manager.manage(
            "OneAndDone",
            do_once,
            {},
            tracked=False,
        )
    ```

*Added in v23.12*

### Restartable custom processes

A custom process that is transient will **always** be restartable. That means the auto-restart will work as expected. However, what if you want to be able to *manually* restart a process, but not have it be restarted by the auto-reloader?
    
.. column::

    In this scenario, you can set `restartable=True` in the `manage` method. This will allow you to manually restart the process, but it will not be restarted by the auto-reloader.
    
.. column::

    ```python
    @app.main_process_ready
    async def ready(app: Sanic, _):
        app.manager.manage(
            "MyProcess",
            my_process,
            {"foo": "bar"},
            restartable=True,
        )
    ```
    
.. column::

    You could now manually restart that process from the multiplexer.
    
.. column::

    ```python
    @app.get("/restart")
    async def restart_handler(request: Request):
        request.app.m.restart("Sanic-MyProcess-0")
        return json({"foo": request.app.m.name})
    ```
    
*Added in v23.12*

### On the fly process management

Custom processes are usually added in the `main_process_ready` listener. However, there may be times when you want to add a process after the application has started. For example, you may want to add a process from a request handler. The multiplexer provides a method for doing this.
    
.. column::

    Once you have a reference to the multiplexer, you can call `manage` to add a process. It works the same as the `manage` method on the Manager.
    
.. column::

    ```python
    @app.post("/start")
    async def start_handler(request: Request):
        request.app.m.manage(
            "MyProcess",
            my_process,
            {"foo": "bar"},
            workers=2,
        )
        return json({"foo": request.app.m.name})
    ```
    
*Added in v23.12*

## Single process mode

.. column::

    If you would like to opt out of running multiple processes, you can run Sanic in a single process only. In this case, the Manager will not run. You will also not have access to any features that require processes (auto-reload, the inspector, etc).

.. column::

    ```sh
    sanic path.to.server:app --single-process
    ```
    ```python
    if __name__ == "__main__":
        app.run(single_process=True)
    ```
    ```python
    if __name__ == "__main__":
        app.prepare(single_process=True)
        Sanic.serve_single()
    ```

## Sanic and multiprocessing

Sanic makes heavy use of the [`multiprocessing` module](https://docs.python.org/3/library/multiprocessing.html) to manage the worker processes. You should generally avoid lower level usage of this module (like setting the start method) as it may interfere with the functionality of Sanic.

### Start methods in Python

Before explaining what Sanic tries to do, it is important to understand what the `start_method` is and why it is important. Python generally allows for three different methods of starting a process:

- `fork`
- `spawn`
- `forkserver`

The `fork` and `forkserver` methods are only available on Unix systems, and `spawn` is the only method available on Windows. On Unix systems where you have a choice, `fork` is generally the default system method.

You are encouraged to read the [Python documentation](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods) to learn more about the differences between these methods. However, the important thing to know is that `fork` basically copies the entire memory of the parent process into the child process, whereas `spawn` will create a new process and then load the application into that process. This is the reason why you need to nest your Sanic `run` call inside of the `__name__ == "__main__"` block if you are not using the CLI.

### Sanic and start methods

By default, Sanic will try and use `spawn` as the start method. This is because it is the only method available on Windows, and it is the safest method on Unix systems. 

.. column::

    However, if you are running Sanic on a Unix system and you would like to use `fork` instead, you can do so by setting the `start_method` on the `Sanic` class. You will want to do this as early as possible in your application, and ideally in the global scope before you import any other modules.

.. column::

    ```python
    from sanic import Sanic
    
    Sanic.start_method = "fork"
    ```

### Overcoming a `RuntimeError`

You might have received a `RuntimeError` that looks like this:

```
RuntimeError: Start method 'spawn' was requested, but 'fork' was already set.
```

If so, that means somewhere in your application you are trying to set the start method that conflicts with what Sanic is trying to do. You have a few options to resolve this:

.. column::

    **OPTION 1:** You can tell Sanic that the start method has been set and to not try and set it again.

.. column::

    ```python
    from sanic import Sanic

    Sanic.START_METHOD_SET = True
    ```

.. column::

    **OPTION 2:** You could tell Sanic that you intend to use `fork` and to not try and set it to `spawn`.

.. column::

    ```python
    from sanic import Sanic

    Sanic.start_method = "fork"
    ```

.. column::

    **OPTION 3:** You can tell Python to use `spawn` instead of `fork` by setting the `multiprocessing` start method.

.. column::

    ```python
    import multiprocessing

    multiprocessing.set_start_method("spawn")
    ```

In any of these options, you should run this code as early as possible in your application. Depending upon exactly what your specific scenario is, you may need to combine some of the options.

.. note::

    The potential issues that arise from this problem are usually easily solved by just allowing Sanic to be in charge of multiprocessing. This usually means making use of the `main_process_start` and `main_process_ready` listeners to deal with multiprocessing issues. For example, you should move instantiating multiprocessing primitives that do a lot of work under the hood from the global scope and into a listener.
    
    ```python
    # This is BAD; avoid the global scope
    from multiprocessing import Queue
    
    q = Queue()
    ```
    
    ```python
    # This is GOOD; the queue is made in a listener and shared to all the processes on the shared_ctx
    from multiprocessing import Queue

    @app.main_process_start
    async def main_process_start(app):
        app.shared_ctx.q = Queue()
    ```
