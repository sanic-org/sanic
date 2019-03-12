Python 3.7 AsyncIO examples
###########################

With Python 3.7 AsyncIO got major update for the following types:

 - asyncio.AbstractEventLoop
 - asyncio.AnstractServer


This example shows how to use sanic with Python 3.7, to be precise: how to retrieve an asyncio server instance:

.. code:: python

    import asyncio
    import socket
    import os

    from sanic import Sanic
    from sanic.response import json

    app = Sanic(__name__)


    @app.route("/")
    async def test(request):
        return json({"hello": "world"})


    server_socket = '/tmp/sanic.sock'

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        os.remove(server_socket)
    finally:
        sock.bind(server_socket)

    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        srv_coro = app.create_server(
            sock=sock,
            return_asyncio_server=True,
            asyncio_server_args=dict(
                start_serving=False
            )
        )
        srv = loop.run_until_complete(srv_coro)
        try:
            assert srv.is_serving() is False
            loop.run_until_complete(srv.start_serving())
            assert srv.is_serving() is True
            loop.run_until_complete(srv.serve_forever())
        except KeyboardInterrupt:
            srv.close()
            loop.close()


Please note that uvloop does not support these features yet.
