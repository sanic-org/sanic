# Websockets

Sanic は [websockets](https://websockets.readthedocs.io/en/stable/) の上に簡単に使える抽象化を提供します。

## ルーティング

.. 列::

```
Websocket ハンドラは、通常のハンドラと同様にルータにフックアップできます。
```

.. 列::

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

## Handler

.. 列::

```
Typically, a websocket handler will want to hold open a loop.

It can then use the `send()` and `recv()` methods on the second object injected into the handler.

This example is a simple endpoint that echos back to the client messages that it receives.
```

.. 列::

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

.. 列::

```
forループ内の`Websocket`オブジェクトを繰り返すだけで、ループを簡素化できます。

*v22.9*に追加されました
```

.. 列::

````
```python
from sanic import Request, Websocket

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    async for msg in ws:
        await ws.send(msg)
```
````

## 設定

詳細は [configuration section](/guide/deployment/configuration.md) をご覧ください。

```python
app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
app.config.WEBSOCKET_PING_INTERVAL = 20
app.config.WEBSOCKET_PING_TIMEOUT = 20
```
