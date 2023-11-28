# Background tasks

## Creating Tasks
It is often desirable and very convenient to make usage of [tasks](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) in async Python. Sanic provides a convenient method to add tasks to the currently **running** loop. It is somewhat similar to `asyncio.create_task`. For adding tasks before the 'App' loop is running, see next section.

```python
async def notify_server_started_after_five_seconds():
    await asyncio.sleep(5)
    print('Server successfully started!')

app.add_task(notify_server_started_after_five_seconds())
```

.. column::

    Sanic will attempt to automatically inject the app, passing it as an argument to the task.

.. column::

    ```python
    async def auto_inject(app):
        await asyncio.sleep(5)
        print(app.name)

    app.add_task(auto_inject)
    ```


.. column::

    Or you can pass the `app` argument explicitly.

.. column::

    ```python
    async def explicit_inject(app):
        await asyncio.sleep(5)
        print(app.name)

    app.add_task(explicit_inject(app))
    ```

## Adding tasks before `app.run`

It is possible to add background tasks before the App is run ie. before `app.run`. To add a task before the App is run, it is recommended to not pass the coroutine object (ie. one created by calling the `async` callable), but instead just pass the callable and Sanic will create the coroutine object on **each worker**. Note: the tasks that are added such are run as `before_server_start` jobs and thus run on every worker (and not in the main process). This has certain consequences, please read [this comment](https://github.com/sanic-org/sanic/issues/2139#issuecomment-868993668) on [this issue](https://github.com/sanic-org/sanic/issues/2139) for further details.

To add work on the main process, consider adding work to [`@app.main_process_start`](./listeners.md). Note: the workers won't start until this work is completed.

.. column::

    Example to add a task before `app.run`

.. column::

    ```python
    async def slow_work():
       ...
   
    async def even_slower(num):
       ...

    app = Sanic(...)
    app.add_task(slow_work) # Note: we are passing the callable and not coroutine object ...
    app.add_task(even_slower(10)) # ... or we can call the function and pass the coroutine.
    app.run(...)
    ```

## Named tasks

.. column::

    When creating a task, you can ask Sanic to keep track of it for you by providing a `name`.

.. column::

    ```python
    app.add_task(slow_work, name="slow_task")
    ```


.. column::

    You can now retrieve that task instance from anywhere in your application using `get_task`.

.. column::

    ```python
    task = app.get_task("slow_task")
    ```

.. column::

    If that task needs to be cancelled, you can do that with `cancel_task`. Make sure that you `await` it.

.. column::

    ```python
    await app.cancel_task("slow_task")
    ```

.. column::

    All registered tasks can be found in the `app.tasks` property. To prevent cancelled tasks from filling up, you may want to run `app.purge_tasks` that will clear out any completed or cancelled tasks.

.. column::

    ```python
    app.purge_tasks()
    ```

This pattern can be particularly useful with `websockets`:

```python
async def receiver(ws):
    while True:
        message = await ws.recv()
        if not message:
            break
        print(f"Received: {message}")

@app.websocket("/feed")
async def feed(request, ws):
    task_name = f"receiver:{request.id}"
    request.app.add_task(receiver(ws), name=task_name)
    try:
        while True:
            await request.app.event("my.custom.event")
            await ws.send("A message")
    finally:
        # When the websocket closes, let's cleanup the task
        await request.app.cancel_task(task_name)
        request.app.purge_tasks()
```

*Added in v21.12*
