---
title: 工人管理器
---

# 工人管理器

22.9版引入了工人经理及其功能。

_本节的详细信息是为了更高级的用法，**无需** 开始。_

管理人员的目的是在开发和生产环境之间建立连贯性和灵活性。 您是否打算运行单个工人或多个工人，无论是否使用自动重新加载： 体验是一样的。

一般而言，它看起来像这样：

![](https://user-images.githubusercontent.com/1662669/178677618-3b4089c3-6c6a-4ecc-8d7a-7eba2a7f29b0.png)

当你运行 Sanic 时，主要进程会实例化一个 `WorkerManager` 。 该经理负责运行一个或多个`WorkerProcess`。 通常有两种程序：

- 服务器进程和
- 非服务器流程。

为了方便起见，用户指南通常使用“工人”或“工人处理”这个术语来表示服务器过程。 和“经理”指在您的主要进程中运行的单个工人管理员。

## Sanic 服务器如何启动进程

Sanic 将使用 [spawn](https://docs.python.org/3/library/multiprocessing.html#contextsand-start-methods) 启动进程。 这意味着对于每个进程/工作者，您的应用程序的全局范围将在自己的线程上运行。 The practical impact of this that _if_ you do not run Sanic with the CLI, you will need to nest the execution code inside a block to make sure it only runs on `__main__`.

```python
if __name__ == "__main__":
    app.run()
```

如果您没有，您可能会看到像这样的错误消息：

```
sanic.exceptions.ServerError: Sanic server could not start: [Errno 98] Address already in use.

This may have happened if you are running Sanic in the global scope and not inside of a `if __name__ == "__main__"` block.

See more information: https://sanic.dev/en/guide/deployment/manager.html#how-sanic-server-starts-processes
```

The likely fix for this problem is nesting your Sanic run call inside of the `__name__ == "__main__"` block. 如果您在嵌套后继续收到此消息，或者如果您在使用CLI时看到此消息， 然后，这意味着您正在尝试使用的端口在您的机器上不可用，您必须选择另一个端口。

### 开始工作者

所有工序_必须_在启动时发送确认信息。 这种情况发生在最严重的情况下，你作为开发者不需要做任何事情。 然而，如果一个或多个工人不发送`ack`消息，管理员将用状态码`1`退出， 或者工人进程在试图启动时抛出异常。 如果没有遇到例外情况，管理员将等待至多三十(30)秒的确认时间。

.. 列:

```
在你知道你需要更多时间来开始的情况下，你可以把管理员混为一谈。 阈值不包括侦听器内的任何内容， 并且限制在您的应用程序的全局范围内的执行时间。

如果你遇到这个问题，它可能会表明需要更深入地了解导致启动速度缓慢的原因。
```

.. 列:

````
```python
from sanic.worker.many import WorkerManager

WorkerManager.THRESHOLD = 100 # 值在 0.1s
```
````

欲了解更多信息，请查看[工人的链接](#worker-ack)。

.. 列:

```
如上所述，Sanic将使用 [spawn](https://docs.python.org/3/library/multiprocessing.html#contextsand-start-methods) 启动工人进程。 如果你想改变这种行为并且知道使用不同的起始方法会产生什么影响，你可以在这里进行修改。
```

.. 列:

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

### 工人套装

当您所有的工人在子进程中运行时，可能出现的问题会被创建：僵局。 当儿童进程停止运作时，就可能出现这种情况，但主要进程并不知道发生了这种情况。 因此，Sanic 服务器将在启动后自动向主进程发送一个 'ack' 消息 (以便确认)。

在22.9版本中，`ack`超时短暂，仅限`5s`。 在第22.12版中，超时时间延长到\`30秒'。 如果您的应用程序在30秒后关闭，可能需要手动增加此阈值。

.. 列:

```
`WorkerManager.THRESHOLD`的值是 `0.1s`。因此，要将它设置为 1分钟，您应该将值设置为 `600'。

此值应尽早在您的应用程序中设置，并且最好在全局范围内出现。 在主要进程开始后设置它将是行不通的。
```

.. 列:

````
```python
from sanic.worker.manager import WorkerManager

WorkerManager.THRESHOLD = 600
```
````

### 零下限重启时间

默认情况下，当重启工人时，萨尼克会先拆除现有的进程，然后再开始一个新进程。

如果您打算在生产中使用重启功能，那么您可能会有兴趣进行零下机刷新。 可以通过强迫读取器改变订单来实现这一点。 等待它到 [ack](#worker-ack), 然后拆除旧的进程。

.. 列:

```
从多路程序中，使用 `zero_downtime` 参数
```

.. 列:

````
```python
app.m.restt(zero_downtime=True)
```
````

_在 v22.12中添加_

## 使用工人流程之间的共享环境

Python 提供了几种方法用于[交换对象](https\://docs.python.org/3/library/multiprocessing.html#exchanging-objects-between en-processes)、 [synchronizing](https\://docs.python.org/3/library/multiprocessing.html#synization-between process)和[sharing state](https://docs.python.org/3/library/multiprocessing.html#sharing-state-honen-processes) 之间的流程。 这通常涉及来自`multiprocessing` 和 `ctypes` 模块的对象。

如果你熟悉这些对象以及如何与它们合作， 你会很乐意知道， Sanic 提供了一个 API 用于在你的工序之间分享这些物体。 如果你不熟悉， 鼓励您阅读以上链接的 Python 文档，然后尝试一些示例，然后执行共享环境。

类似于[应用程序上下文](../basics/app.md#application-context)允许应用程序在应用程序整个生命周期内与 `app 共享状态。 tx`, 共享上下文为上述特殊对象提供了相同的内容。 此上下文可用于 `app.shared_ctx` 并且应该**ONLY** 用于共享用于此目的的物体。

`shared_ctx`将：

- _NOT_ 共享常规对象，如`int`、`dict`或`list`
- _NOT_ 在不同机器上运行的 Sanic 实例之间共享状态
- _NOT_ 共享状态到非工序中
- **仅** 服务器工人之间由同一管理器管理的共享状态

将不恰当对象附加到 "shared_ctx" 可能会导致警告，而不是错误。 您应该小心不要意外添加一个不安全的对象到 "shared_ctx" ，因为它可能无法正常工作。 如果你因为其中一个警告而在这里被指向，你可能会意外地在 "shared_ctx" 中使用不安全的物体。

.. 列:

```
为了创建一个共享对象，你**必须** 在主流程中创建它，并将它附加在`main_process_start`监听器中。
```

.. 列:

````
```python
来自多处理导入队列

@app.main_process_start
async def main_process_start(app):
    app.shared_ctx.queue = Queue()
```
````

尝试附加到监听器外面的`shared_ctx`对象可能会导致一个 `RuntimeError` 。

.. 列:

```
在 `main_process_start` 监听器中创建对象并附加到 `shared_ctx` 之后， 只要有应用程序实例就可以在您的工作人员中使用(例如：监听器、中间器、请求处理器)。
```

.. 列:

````
```python
来自多处理导入队列

@app.get("")
async def 处理器(请求):
    request.app.shared_ctx.queue.put(1)
    ...
```
````

## 访问多声道器

应用程序实例可以访问一个对象，它能够提供与经理和其他工人进程互动的权限。 此对象被附加为 `app.multiplexer` 属性，但它更容易被其别名访问：`app.m`。

.. 列:

```
例如，您可以访问当前的工人状态。
```

.. 列:

````
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
````

.. 列:

```
`multiplexer` 也可以终止管理器或重启工作人员进程
```

.. 列:

````
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
````

## 工人状态

.. 列:

```
如上文所示，`multiplexer`可以报告当前运行的工人的状态。 然而，它也包含所有正在运行的进程的状态。
```

.. 列:

````
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
````

可能的州有：

- `NONE` - 工人已被创建，但还没有进程
- `IDLE` - 进程已创建，但尚未运行
- `STARTING` - 进程正在开始
- `STARTED` - 进程已经开始
- `ACKED` - 进程已经启动并发送了一条确认信息(通常只适用于服务器进程)
- `JOINED` - 该进程已经退出并加入了主要进程
- `TERNATED` - 该进程已经退出并终止
- `RESTARTING` - 进程正在重启
- `FAILED` - 进程遇到异常，已不再运行
- `COMPLETED` - 该进程已经完成并成功退出

## 内置非服务器进程

如上所述，管理员也有能力运行非服务器程序。 Sanic 带有两种内置类型的非服务器进程，并允许[创建自定义进程](#running-custom-processes)。

两个内置进程是

- [auto-reloader](./development.md#automatic-reloader) 可选地启用监视文件系统进行更改并触发重启
- [inspector](#spector), 可选地启用提供外部访问的运行实例状态

## 检查员

Sanic 有能力在 CLI 中暴露`multiplexer` 的状态和功能。 目前，这需要在 CLI 命令上运行与运行中的 Sanic 实例相同的机器。 默认情况下，检查员被禁用。

.. 列:

```
要启用它，请将配置值设置为“True”。
```

.. 列:

````
```python
app.config.INSPECTOR = True
```
````

您现在可以访问这些CLI命令：

```
净化检查重新加载服务器工作人员的一次重新加载
净化检查关闭应用程序和所有进程
净化检查员将工人人数缩放到N
净化检查 <custom>                    运行一个自定义命令
```

![](https://user-images.githubusercontent.com/166269/190099384-2f2f3fae-22d5-4529-b279-8446f6b5f9bd.png)

.. 列:

```
通过在您的机器上显示一个小的 HTTP 服务来实现这一点。您可以使用配置值控制位置：
```

.. 列:

````
```python
app.config.INSPECTOR_HOST = "localhost"
app.config.INSPECTOR_PORT = 6457
```
````

[了解更多](./检查员.md)来了解与检查员可能做些什么。

## 运行自定义进程

若要在 Sanic 上运行一个管理下的自定义进程，您必须创建一个可调用。 如果这个进程是打算长期运行的，那么它就应该用一个`SIGINT`或`SIGTERM`的信号来处理一个关机呼叫。

.. 列:

```
Python最简单的方法是把你的循环换成`KeyboardInterrupt'。

如果您打算运行另一个应用程序，像机器人那样， 然后，它很可能已经有能力处理这个信号，而且你可能不需要做任何事情。
```

.. 列:

````
```python
from time import sleep

def my_process(foo):
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("done")
```
````

.. 列:

```
此可调用必须在 `main_process_ready` 监听器中注册。 必须注意的是，**不** 是你应该注册[共享上下文](#使用共享上下文-工人之间的过程)对象的同一地点。
```

.. 列:

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
# app.manager.manager.manag(<name>, <callable>, <kwargs>)
    app.manager.manager.management("MyProcess", my_proces", {"foo": "bar"})
```
````

### B. 过渡时期与持久进程

.. 列:

```
When you manage a process with the `manage` method, you have the option to make it transient or durable. A transient process will be restarted by the auto-reloader, and a durable process will not.

By default, all processes are durable.
```

.. 列:

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manager.management(
        "MyProcess",
        my_process,
        {"foo": "bar"},
        transitent=True,
    )
```
````

### 跟踪或未跟踪的进程

.. 新：v23.12

```
Out of the box, Sanic will track the state of all processes. This means that you can access the state of the process from the [multiplexer](./manager#access-to-the-multiplexer) object, or from the [Inspector](./manager#inspector).

See [worker state](./manager#worker-state) for more information.

Sometimes it is helpful to run background processes that are not long-running. You run them once until completion and then they exit. Upon completion, they will either be in `FAILED` or `COMPLETED` state.
```

.. 列:

```
当你正在运行一个非长期运行的过程时，你可以在"管理"方法中设置 "tracked=False" 来选择不跟踪它。 这意味着一旦完成这一进程，它将从跟踪的进程清单中删除。 您只能在进程运行时检查进程状态。
```

.. 列:

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manager.manage(
        "One AndDone",
        do_once,
        {},
        tracked=False,
    )
```
````

_添加于 v23.12_

### 可重新启动自定义进程

.. 新：v23.12

```
临时性的自定义进程将**总是可以重启。这意味着自动重启将会如预期的那样正常工作。 然而，如果你想要能够*手动*重新启动一个过程，但它不会被自动重新加载器重新启动？
```

.. 列:

```
在这个场景中，你可以在“管理”方法中设置 `rehartable=True`。 这将允许您手动重启进程，但它不会被自动重新加载器重启。
```

.. 列:

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manager.management(
        "MyProcess",
        my_process,
        {"foo": "bar"},
        restable=True,
    )
```
````

.. 列:

```
您现在可以从多路程序手动重启此进程。
```

.. 列:

````
```python
@app.get("/restart")
async def restest_handler(request: acquest):
    request.app.m.restt("Sanic-MyProcess-0")
    return json({"foo": request.app.m.name})
```
````

_添加于 v23.12_

### 飞行过程管理

.. 新：v23.12

```
自定义进程通常在 `main_process_ready` 监听器中添加。 然而，有时候您想要在应用程序启动后添加一个过程。 例如，您可能想要从请求处理器中添加一个进程。多路程序提供了这样做的方法。
```

.. 列:

```
一旦你有一个多路由器的引用，你可以调用 `manage` 来添加一个过程。 它与经理上的 `manag` 方法相同。
```

.. 列:

````
```python
@app.post("/start")
async def start_handler(request):
    request.app.m. anage(
        "我的过程",
        my_process,
        {"foo": "bar"},
        workers=2,

    return json({"foo": request. pweb name})
```
````

_添加于 v23.12_

## 单进程模式

.. 列:

```
如果你想要退出运行多个进程，你只能在一个进程中运行 Sanic。 在这种情况下，管理员不会运行。 您也无法访问任何需要处理的功能 (自动重新加载、检查员等)。
```

.. 列:

````
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
````

## 声学和多处理器

Sanic大量使用 [`multiprocessing` 模块](https://docs.python.org/3/library/multiprocessing.html) 来管理工人过程。 您通常应该避免低级别使用此模块(例如设置起始方法)，因为它可能会干扰Sanic的功能。

### 在 Python 中启动方法

在解释萨尼克试图做什么之前，必须了解`start_method`是什么以及为什么它是重要的。 Python通常允许三种不同的方法启动进程：

- `fork`
- `spawn`
- `forkserver`

"fork" 和 "forkserver" 方法仅在 Unix 系统上可用，而"spawn" 是Windows上唯一可用的方法。 在您可以选择的 Unix 系统中，`fork` 通常是默认系统方法。

鼓励您阅读[Python文档](https://docs.python.org/3/library/multiprocessing.html#contextsand-start-methods)，了解更多关于这些方法之间差异的信息。 然而，重要的是`fork`基本上将父过程的整个记忆复制到子过程中。 而`spawn`会创建一个新的流程，然后将应用程序加载到该流程中。 This is the reason why you need to nest your Sanic `run` call inside of the `__name__ == "__main__"` block if you are not using the CLI.

### 智能和启动方法

默认情况下，Sanic会尝试使用 `spawn` 作为起始方法。 这是因为它是Windows上唯一可用的方法，它是Unix系统上最安全的方法。

.. 列:

```
然而，如果你在 Unix 系统上运行 Sanic 而你想使用 `fork` 你可以通过设置 `Sanic` 类的 `start_method` 来做到这一点。 您将尽早在您的应用程序中，并且最好是在全局范围内，然后再导入任何其他模块。
```

.. 列:

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

### 覆盖一个 `RuntimeError`

您可能已经收到了一个看起来像这样的 `RuntimeError` ：

```
运行时错误：请求了开始方法“spawn”，但“fork”已经设置。
```

如果是，这意味着你在应用程序中的某个地方试图设置与萨尼克试图做什么相冲突的起始方法。 您有几个选项来解决这个问题：

.. 列:

```
**选项1:** 你可以告诉Sanic, 开始方法已经设置, 不要再尝试.
```

.. 列:

````
```python
from sanic import Sanic

Sanic.START_METHOD_SET = True
```
````

.. 列:

```
**选项2：** 你可以告诉Sanic你打算使用 `fork` 而不尝试设置为 `spawn` 。
```

.. 列:

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

.. 列:

```
**选项3：** 您可以通过设置 `multiprocessing` 开始方法，告诉Python 使用 `spawn` 而不是 `fork` 。
```

.. 列:

````
```python
import multiprocessing

multiprocessing.set_start_method("spawn")
```
````

在这些选项中，您应该尽早在应用程序中运行此代码。 根据具体的场景，您可能需要合并一些选项。

.. 注：

````
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
````
