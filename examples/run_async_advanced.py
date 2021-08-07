import asyncio

from signal import SIGINT, signal

import uvloop

from sanic import Sanic, response
from sanic.server import AsyncioServer


app = Sanic(__name__)


@app.listener("after_server_start")
async def after_start_test(app, loop):
    print("Async Server Started!")


@app.route("/")
async def test(request):
    return response.json({"answer": "42"})


asyncio.set_event_loop(uvloop.new_event_loop())
serv_coro = app.create_server(
    host="0.0.0.0", port=8000, return_asyncio_server=True
)
loop = asyncio.get_event_loop()
serv_task = asyncio.ensure_future(serv_coro, loop=loop)
signal(SIGINT, lambda s, f: loop.stop())
server: AsyncioServer = loop.run_until_complete(serv_task)  # type: ignore
server.startup()

# When using app.run(), this actually triggers before the serv_coro.
# But, in this example, we are using the convenience method, even if it is
# out of order.
server.before_start()
server.after_start()
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.stop()
finally:
    server.before_stop()

    # Wait for server to close
    close_task = server.close()
    loop.run_until_complete(close_task)

    # Complete all tasks on the loop
    for connection in server.connections:
        connection.close_if_idle()
    server.after_stop()
