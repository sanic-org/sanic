---
title: 背景任务
---

# 后台任务(Background tasks)

## 创建任务(Creating Tasks)

在异步 Python 中，常常希望能够方便地使用任务[tasks](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task)。 Sanic 提供了一种便捷的方法，可以将任务添加到当前**正在运行**的循环中， 类似于 `asyncio.create_task`。 若要在“App”循环启动前添加任务，请参阅下一节内容。

```python
async def notify_server_started_after_five_seconds():
    await asyncio.sleep(5)
    print('Server successfully started!')

app.add_task(notify_server_started_after_five_seconds())
```

.. column::

```
Sanic 会尝试自动注入应用实例，并将其作为参数传递给任务。
```

.. column::

````
```python
async def auto_inject(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(auto_inject)
```
````

.. column::

```
或者，您可以显式地传递 `app` 参数。
```

.. column::

````
```python
async def explicit_inject(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(explicit_inject(app))
```
````

.. column::

```
The `add_task` method returns the created `asyncio.Task` object, allowing you to await or check its result later.

*Added in v25.12*
```

.. column::

````
```python
任务 = app.add_task(some_coroutine())
# 稍后...
结果 = 等待任务
```
````

## 在 `app.run` 之前添加任务

在应用运行之前（即在调用 app.run 之前），可以添加后台任务。 建议在这种情况下不要传递协程对象（即通过调用异步可调用函数创建的对象），而是仅传递可调用函数，Sanic 会在**每个工作进程**中自行创建协程对象。 请注意，这样添加的任务会在每个工作进程内以 `before_server_start `任务的形式运行，而不是在主进程中运行。 这一点具有特定的影响，请参阅该问题下的[这条评论](https://github.com/sanic-org/sanic/issues/2139#issuecomment-868993668) 在 [issue](https://github.com/sanic-org/sanic/issues/2139) 以获取更多细节。

若要在主进程中添加任务，请考虑使用装饰器  [`@app.main_process_start`](./listeners.md) 来添加任务。 请注意，直到这些任务完成，工作进程才开始启动。

.. column::

```
在 `app.run` 之前添加任务的示例代码
```

.. column::

````
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
````

## 命名任务(Named tasks)

.. column::

```
创建任务时，通过提供一个`name`，你可以让Sanic帮你跟踪这个任务。
```

.. column::

````
```python
app.add_task(troub_work, name="low_task")
```
````

.. column::

```
现在，你可以在应用程序的任何地方使用`get_task`来检索该任务实例。
```

.. column::

````
```python
task = app.get_task("slow_task")
```
````

.. column::

```
如果需要取消该任务，你可以使用`cancel_task`来完成。确保对它进行`await`调用。
```

.. column::

````
```python
await app.cancel_task("slow_task")
```
````

.. 列:

```
所有已注册的任务都可以在`app.tasks`属性中找到。为了避免被取消的任务占用空间，你可能想要运行`app.purge_tasks`，它会清除所有已完成或被取消的任务。
```

.. 列:

````
```python
app.purge_tasks()
```
````

这种模式在处理`websockets`时尤其有用：

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

\*添加于 v21.12 \*
