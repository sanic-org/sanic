# Websockets

Sanic 提供了一个易于使用的 [websockets]顶部的摘要(https://websockets.readthedocs.io/en/stable/)。

## 路由

.. 列:

```
Websocket 处理程序可以绑定到路由器，类似于常规处理程序。
```

.. 列:

````
```python
from sanic import Request, Websocket

async def Feed(request: Request, ws: Websocket):
    pask

appp dd_websocket_route(feed, "/feed")
```
```python
from sanic import Request, Websocket

@app. ebsocket("/feed")
async def Feed(request, ws: Websocket):
    passe
```
````

## Handler

.. 列:

```
通常情况下，一个 websocket 处理程序将会保持打开一个循环。

然后它可以在注入处理器的第二个对象上使用 `send()` 和 `recv()` 方法。

这个示例是一个简单的端点，回溯到它收到的客户端消息。
```

.. 列:

````
```python
来自sanic import Request, Websocket

@app. ebsocket("/feed")
async def Feed(请求: 请求, ws: Websocket:
    while True:
        data = "hello!
        打印("发送：" + 数据)
        等待ws。 end(data)
        data = 等待ws。 ecv()
        打印("接收：" + 数据)
```
````

.. 列:

```
You can simplify your loop by just iterating over the `Websocket` object in a for loop.

*Added in v22.9*
```

.. 列:

````
```python
来自sanic import Request, Websocket

@app. ebsocket("/feed")
async def Feed(请求: 请求, ws: Websocket:
    async for msg in w:
        等待w. end(msg)
```
````

## 配置

详见[配置部分](/guide/deplement/configuration.md)，但默认值显示在下面。

```python
app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
app.config.WEBSOCKET_PING_INTERVAL = 20
app.config.WEBSOCKET_PING_TIMEOUT = 20
```
