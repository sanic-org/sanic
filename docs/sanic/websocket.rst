WebSocket
=========

Sanic supports websockets, to setup a WebSocket:

.. code:: python

    from sanic import Sanic
    from sanic.response import json
    from sanic.websocket import WebSocketProtocol

    app = Sanic()

    @app.websocket('/feed')
    async def feed(request, ws):
        while True:
            data = 'hello!'
            print('Sending: ' + data)
            await ws.send(data)
            data = await ws.recv()
            print('Received: ' + data)

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, protocol=WebSocketProtocol)


Alternatively, the ``app.add_websocket_route`` method can be used instead of the
decorator:

.. code:: python
    async def feed(request, ws):
        pass

    app.add_websocket_route(feed, '/feed')


Handlers for a WebSocket route are passed the request as first argument, and a
WebSocket protocol object as second argument. The protocol object has ``send``
and ``recv`` methods to send and receive data respectively.


You could setup your own WebSocket configuration through ``app.config``, like

.. code:: python
    app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
    app.config.WEBSOCKET_MAX_QUEUE = 32
    app.config.WEBSOCKET_READ_LIMIT = 2 ** 16
    app.config.WEBSOCKET_WRITE_LIMIT = 2 ** 16

Find more in ``Configuration`` section.
