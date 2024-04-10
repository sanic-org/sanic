# 监听器(Listeners)

Sanic 提供了八个（8）机会让您在应用程序服务器生命周期的不同阶段注入操作。 这还不包括[信号](../advanced/signals.md)，后者允许进一步自定义注入。

有两个（2）**仅**在主 Sanic 进程中运行（即每次调用 `sanic server.app` 时运行一次）。

- `main_process_start`
- `main_process_stop`

另外有两个（2）是在启用自动重载功能时**仅**在重载进程中运行的。

- `reload_process_start`
- `reload_process_stop`

\*在 v22.3中添加 `reload_process_start` 和 `reload_process_stop` \*

还有四个（4）允许您在服务器启动(startup)或关闭(teardown )时执行启动/清理代码。

- `before_server_start`
- `after_server_start`
- `before_server_stop`
- `after_server_stop`

工作者进程的生命周期如下所示：

.. mermaid::

```
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
```

重新加载进程位于负责启动和停止 Sanic 进程的外部进程内，独立于上述工作者进程之外运行。 请看下面的例子：

```python
@app.reload_process_start
async def reload_start(*_):
    print(">>>>>> reload_start <<<<<<")

@app.main_process_start
async def main_start(*_):
    print(">>>>>> main_start <<<<<<")
	
@app.before_server_start
async def before_start(*_):
	print(">>>>>> before_start <<<<<<")
```

如果该应用程序在开启自动重载的情况下运行，当重新加载进程启动时，会调用一次 `reload_start` 函数。 当主进程启动时，`main_start` 函数也会被调用一次。 **然而**，`before_start` 函数会在每个启动的工作者进程中被调用一次，并且每当文件保存导致工作者进程重启时，也会再次调用。

## 注册监听器(Attaching a listener)

.. column::

```
将函数设置为监听器的过程类似于声明路由。

当前正在运行的 `Sanic()` 实例会被注入到监听器中。
```

.. column::

````
```python
async def setup_db(app):
    app.ctx.db = await db_setup()

app.register_listener(setup_db, "before_server_start")
```
````

.. column::

```
`Sanic` 应用实例还提供了一个便利的装饰器。
```

.. column::

````
```python
@app.listener("before_server_start")
async def setup_db(app):
    app.ctx.db = await db_setup()
```
````

.. column::

```
在 v22.3 版本之前，应用程序实例和当前事件循环都会被注入到函数中。然而，默认情况下只会注入应用程序实例。如果您的函数签名同时接受这两个参数，那么应用程序实例和循环将会像下面所示那样都被注入。
```

.. column::

````
```python
@app.listener("before_server_start")
async def setup_db(app, loop):
    app.ctx.db = await db_setup()
```
````

.. column::

```
您甚至可以进一步缩短装饰器。这对于具有自动补全功能的 IDE 尤其有用。
```

.. column::

````
```python
@app.before_server_start
async def setup_db(app):
    app.ctx.db = await db_setup()
```
````

## 执行顺序(Order of execution)

在启动期间，监听器按照声明的顺序执行，在关闭期间则按照声明的反向顺序执行。

|                       | 执行阶段            | 执行顺序          |
| --------------------- | --------------- | ------------- |
| `main_process_start`  | main startup    | regular 🙂 ⬇️ |
| `before_server_start` | worker startup  | regular 🙂 ⬇️ |
| `after_server_start`  | worker startup  | regular 🙂 ⬇️ |
| `before_server_stop`  | worker shutdown | 🙃 ⬆️ reverse |
| `after_server_stop`   | worker shutdown | 🙃 ⬆️ reverse |
| `main_process_stop`   | main shutdown   | 🙃 ⬆️ reverse |

鉴于以下设置，如果我们运行两个工作者进程，我们预期会在控制台看到以下输出：

.. column::

````
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
````

.. column::

````
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
在上面的例子中，请注意存在三个运行中的进程：

- `pid: 1000000` - The *main* process
- `pid: 1111111` - Worker 1
- `pid: 1222222` - Worker 2

*尽管我们的示例先展示了所有属于一个工作者（worker）的输出，然后展示了另一个工作者（worker）的所有输出，但在实际情况中，由于这些进程是在不同的进程中运行的，不同进程之间的执行顺序并不保证一致。但是，您完全可以确定的是，单一工作者（worker）进程 **总是** 会保持其内部执行顺序不变。*
````

.. tip:: 提示一下

```
这种情况的实际结果是，如果在 `before_server_start` 处理器中的第一个监听器设置了数据库连接，那么在此之后注册的监听器可以依赖于在它们启动和停止时该连接都处于活跃状态。
```

### 优先级（Priority）

.. new:: v23.12

```
自 v23.12 版本起，向监听器添加了 `priority` 关键字参数。这允许精细调整监听器执行顺序。默认优先级为 `0`。优先级较高的监听器将首先执行。相同优先级的监听器将按照注册的顺序执行。此外，附加到 `app` 实例的监听器将优先于附加到 `Blueprint` 实例的监听器执行。
```

决定执行顺序的整体规则如下：

1. 先级降序排列
2. 应用程序级别的监听器优先于蓝图级别的监听器执行
3. 按照注册顺序执行

.. column::

````
作为示例，考虑以下内容，它将打印：

```bash
third
bp_third
second
bp_second
first
fourth
bp_first
```
````

.. column::

````
```python
@app.before_server_start
async def first(app):
    print("first")

@app.listener("before_server_start", priority=2)
async def second(app):
    print("second")

@app.before_server_start(priority=3)
async def third(app):
    print("third")

@bp.before_server_start
async def bp_first(app):
    print("bp_first")

@bp.listener("before_server_start", priority=2)
async def bp_second(app):
    print("bp_second")

@bp.before_server_start(priority=3)
async def bp_third(app):
    print("bp_third")

@app.before_server_start
async def fourth(app):
    print("fourth")

app.blueprint(bp)
```
````

## ASGI 模式 (ASGI Mode)

如果你使用ASGI服务器运行应用程序，请注意以下变化：

- `reload_process_start` 和 `reload_process_stop` 将被**忽略**
- `main_process_start` 和 `main_process_stop` 将被**忽略**
- `before_server_start` 尽可能早地运行，并且将在 `after_server_start ` 之前执行，但从技术上讲，在此时服务器已经启动了
- `after_server_stop` 尽可能晚地运行，并且将在 `before_server_stop` 之后执行，但从技术上讲，在此时服务器仍在运行中
