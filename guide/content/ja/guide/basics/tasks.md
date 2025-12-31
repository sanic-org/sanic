---
title: バックグラウンドタスク
---

# バックグラウンドタスク

## タスクの作成

async Pythonで [tasks](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) を利用するのはとても便利です。 Sanicは、現在の**実行中**ループにタスクを追加する便利な方法を提供します。 これは `asyncio.create_task` に似ています。 'App' ループが実行される前にタスクを追加する場合は、次のセクションを参照してください。

```python
async def notify_server_started_after_five_secondss():
    await asyncio.sleep(5)
    print('Server successfully started!')

app.add_task(notify_server_started_after_five_seconds())
```

.. 列::

```
Sanicは自動的にアプリを注入しようとし、タスクに引数として渡します。
```

.. 列::

````
```python
async def auto_inject(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(auto_inject)
```
````

.. 列::

```
もしくは、`app`引数を明示的に渡すこともできます。
```

.. 列::

````
```python
async def explicit_inject(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(explicit_inject(app))
```
````

.. 列::

```
`add_task` メソッドは、生成された `asyncio.Task` オブジェクトを返します。これにより、待ったり、結果を確認することができます。

*v25.12* に追加されました。
```

.. 列::

````
```python
task = app.add_task(some_coroutine())
# Later...
result = await task
```
````

## `app.run`の前にタスクを追加する

`app.run`の前にバックグラウンドタスクを追加することができます。 アプリを実行する前にタスクを追加するには、コルーチンオブジェクトを渡さないことをお勧めします (すなわち。 `async`呼び出し可能を呼び出すことで作成されたものですが、代わりに呼び出し可能ファイルを渡すだけで、Sanicは**各ワーカー**にコルーチンオブジェクトを作成します。 注意: このように追加されたタスクは、 `before_server_start` ジョブとして実行されます。そのため、すべてのワーカーで実行されます (メインプロセスでは実行されません)。 これには一定の影響があります。詳細については、[このissue](https://github.com/sanic-org/sanic/issues/2139#issuecomment-868993668)の[このissue](https://github.com/sanic-org/sanic/issues/2139)をご覧ください。

メインプロセスで作業を追加するには、[`@app.main_process_start`](./listeners.md)に作業を追加することを検討してください。 注意: この作業が完了するまでワーカーは起動しません。

.. 列::

```
`app.run`の前にタスクを追加する例
```

.. 列::

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

## 名前付きタスク

.. 列::

```
タスクを作成するときは、`name`を指定することで、Sanicにそのタスクを追跡させることができます。
```

.. 列::

````
```python
app.add_task(slow_work, name="slow_task")
```
````

.. 列::

```
`get_task` を使用して、アプリケーションのどこからでもタスクインスタンスを取得できるようになりました。
```

.. 列::

````
```python
task = app.get_task("slow_task")
```
````

.. 列::

```
そのタスクをキャンセルする必要がある場合は、`cancel_task` でそれを行うことができます。`await` を確認してください。
```

.. 列::

````
```python
await app.cancel_task("slow_task")
```
````

.. 列::

```
登録されたすべてのタスクは `app.tasks` プロパティにあります。キャンセルされたタスクがいっぱいになるのを防ぐため、`app` を実行します。 完了またはキャンセルされたタスクをクリアする urge_tasks` 。
```

.. 列::

````
```python
app.purge_tasks()
```
````

このパターンは `websockets` で特に役立ちます。

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

_v21.12_ に追加されました
