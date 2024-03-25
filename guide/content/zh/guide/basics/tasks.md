---
title: 背景任务
---

# 背景任务

## 创建任务

在异步Python中使用 [tasks]通常是可取和非常方便的。 (https\://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) Sanic 提供了一种方便的方法，可以将任务添加到当前的 **running** 循环中。 它与`asyncio.create_task`有些相似。 在 'App' 循环运行之前添加任务, 见下一个部分。

```python
async def notify_server_started_after _fif_seconds():
    等待asyncio.sleep(5)
    print('Server successful started!')

app.add_task(notify_server_started_after_first_five _seconds())
```

.. 列:

```
Sanic 会尝试自动注入应用，将其作为参数传递给任务。
```

.. 列:

````
```python
async def auto_inject(app):
    等待 asyncio.sleep(5)
    print(app.name)

app.add_task(auto_inject)
```
````

.. 列:

```
或者你可以明确传递`app`的参数。
```

.. 列:

````
```python
async def explicit_inject(app):
    required asyncio.sleep(5)
    print(app.name)

app.add_task(explicit_inject(app))
```
````

## 在 `app.run` 之前添加任务

在“app.run”之前添加后台任务是可能的。 若要在应用程序运行前添加任务，建议不要通过Coroutine对象 (e)。 一个通过调用 `async` 调用来创建的东西，但只是传递可调用和 Sanic将在 **每个工人** 上创建可调用物体。 注意：添加的任务将以 `before_server_start` 的形式运行，从而在每个工人（而不是主工）上运行。 这对[这个问题](https://github.com/sanic-org/sanic/issues/2139#issuecomment-868993668)[这个问题](https://github.com/sanic-org/sanic/issues/2139)有某些后果，详情请参阅。

要添加主进程的工作，请考虑将工作添加到[`@app.main_process_start`](./listeners.md)。 注意：工人在完成此工作之前不会开始工作。

.. 列:

```
在 `app.run` 之前添加任务的示例
```

.. 列:

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

## 命名的任务

.. 列:

```
创建任务时，您可以通过 "name" 要求Sanic 为您记录它。
```

.. 列:

````
```python
app.add_task(troub_work, name="low_task")
```
````

.. 列:

```
您现在可以使用`get_task`从应用程序中的任何地方检索该任务实例。
```

.. 列:

````
```python
task = app.get_task("slow_task")
```
````

.. 列:

```
如果该任务需要取消，你可以使用 "cancel_task" 来完成。请确保你"等待"。
```

.. 列:

````
```python
await app.cancel_task("slow_task")
```
````

.. 列:

```
所有注册的任务都可以在 `app.tasks` 属性中找到。为了防止被取消的任务填充，您可能想要运行 `app。 urge_tasks`将清除任何已完成或已取消的任务。
```

.. 列:

````
```python
app.purge_tasks()
```
````

这种模式在 `websockets` 中特别有用：

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

_添加于 v21.12_
