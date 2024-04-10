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

## 正在附加侦听器

.. 列:

```
作为侦听器设置函数的过程类似于声明路由。

正在运行的 `Sanic()` 实例被注入到侦听器中。
```

.. 列:

````
```python
async def setup_db(app):
    app.ctx.db = 等待db_setup()

app.register_listener(setup_db, "previ_server_start")
```
````

.. 列:

```
“Sanic”应用实例也有一个方便装饰器。
```

.. 列:

````
```python
@app.listener("prev_server_start")
async def setup_db(app):
    app.ctx.db = 等待db_setup()
```
````

.. 列:

```
在 v22.3 之前，应用程序实例和当前事件循环都被注入到函数中。 然而，默认情况下只注入应用程序实例。 如果您的函数签名同时接受，那么应用程序和循环都会像这里显示的那样被注入。
```

.. 列:

````
```python
@app.listener("prev_server_start")
async def setup_db(app, loop):
    app.ctx.db = 等待db_setup()
```
````

.. 列:

```
您可以进一步缩短装饰。如果您拥有一个自动完成的 IDE，这将是很有帮助的。
```

.. 列:

````
```python
@app.before_server_start
async def setup_db(app):
    app.ctx.db = 等待db_setup()
```
````

## 执行顺序

侦听器按启动时的申报顺序执行，并在拆解时反向排序。

|                       | 阶段     | 订单                                                                                                 |
| --------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| `main_process_start`  | 主要启动   | 普通:稍微ly_smiling_face: ⬇️ |
| `befor_server_start`  | 工作人员启动 | 普通:稍微ly_smiling_face: ⬇️ |
| `After _server_start` | 工作人员启动 | 普通:稍微ly_smiling_face: ⬇️ |
| `before_server_stop`  | 工人关机   | 🙃 ⬆️ reverse                                                                                      |
| `After _server_stop`  | 工人关机   | 🙃 ⬆️ reverse                                                                                      |
| `main_process_stop`   | 主要关机   | 🙃 ⬆️ reverse                                                                                      |

鉴于以下情况，如果我们运行两名工人，我们应该在控制台中看到这一点。

.. 列:

````
```python
@app.listener("before_server_start")
async def listener_1(app, loop):
    print("listener_1")

@appp efor_server_start
async def listener_2(app, loor):
    print("listener_2")

@app. istener("after_server_start")
async def listener_3(app, rol):
    print("listener_3")

@app. fter_server_start
async def listener_4(app, loor):
    print("listener_4")

@app. istener("before_server_stop")
async def listener_5(app, rol):
    print("listener_5")

@app. efor_server_stop
async def listener_6(app, loor):
    print("listener_6")

@app. istener("after_server_stop")
async def listener_7(app, rol):
    print("listener_7")

@app. fter_server_stop
async def listener_8(app, loor):
    print("listener_8")
```
````

.. 列:

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
In the above example, notice how there are three processes running:

- `pid: 1000000` - The *main* process
- `pid: 1111111` - Worker 1
- `pid: 1222222` - Worker 2

*Just because our example groups all of one worker and then all of another, in reality since these are running on separate processes, the ordering between processes is not guaranteed. But, you can be sure that a single worker will **always** maintain its order.*
````

.. tip:: FYI

```
这个结果的实际结果是，如果`pre_server_start`中的第一个监听器设置了数据库连接。 注册后的侦听器可以在启动和停止时依靠该连接存活。
```

### 优先权

.. 新：v23.12

```
在 v23.12，监听器中添加了 `priority` 关键字参数。这允许调整监听器的执行顺序。 默认优先级是 `0`。优先级较高的侦听器将先执行。 具有相同优先级的侦听器将按照他们注册的顺序执行。 此外，连接到 `app` 实例的侦听器将在连接到 `Blueprint` 实例的侦听器之前执行。
```

总体上，决定执行顺序的规则如下：

1. 按降序排序
2. 蓝图监听器之前的应用程序监听器
3. 注册订单

.. 列:

````
As an example, consider the following, which will print:

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

.. 列:

````
```python
@app.before_server_start
async def first(app):
    print("first")

@app。 istener("before_server_start", priority=2)
async def second(app):
    print("second")

@app. efor_server_start(priority=3)
async def third(app):
    print("third")

@bp.befor_server_start
async def bp_first(app):
    print("bp_first")

@bp. istener("before_server_start", priority=2)
async def bp_second(app):
    print("bp_second")

@bp. efor_server_start(priority=3)
async def bp_third(app):
    print("bp_third")

@app。 efore_server_start
async def fourth(app):
    print("fourth")

app.blueprint(bp)
```
````

## ASGI 模式

如果您正在使用 ASGI 服务器运行您的应用程序，请注意以下变化：

- `reload_process_start` 和 `reload_process_stop` 将被**忽略**
- `main_process_start` 和 `main_process_stop` 将被**忽略**
- `befor_server_start` 将尽早运行，并且将在 `After _server_start` 之前运行，但是从技术上讲，服务器已经在那个地点运行。
- `after _server_stop`将会尽早运行，并且会在 `before_server_stop` 之后运行，但从技术上讲，服务器仍然在那个地点运行
