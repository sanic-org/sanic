# Websockets

Sanic 提供了一个基于 [websockets](https://websockets.readthedocs.io/en/stable/) 的易于使用的抽象层

## 路由(Routing)

.. column::

```
Websocket 处理程序可以像常规处理程序那样连接到路由器上。
```

.. column::

````
```python
from sanic import Request, Websocket

async def feed(request: Request, ws: Websocket):
    pass

app.add_websocket_route(feed, "/feed")
```
```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    pass
```
````

## 定义响应函数(Handler)

.. column::

```
通常情况下，websocket 处理程序会维持一个循环保持打开状态。

然后，可以在注入到处理程序的第二个对象上调用 `send()` 和 `recv()` 方法。

下面是一个简单的示例，该端点接收来自客户端的消息并将其回显给客户端。
```

.. column::

````
```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    while True:
        data = "hello!"
        print("Sending: " + data)
        await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)
```
````

.. column::

```
您可以通过在一个for循环中迭代 `Websocket` 对象来简化您的循环。

*该特性在v22.9版本中添加*
```

.. column::

````
```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    async for msg in ws:
        await ws.send(msg)
```
````

## 配置(Configuration)

更多详情请参阅[配置部分](/zh/guide/deployment/configuration.md)，不过下面列出了默认值。

```python
app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
app.config.WEBSOCKET_PING_INTERVAL = 20
app.config.WEBSOCKET_PING_TIMEOUT = 20
```
