import asyncio

from signal import SIGINT, signal

import uvloop

from sanic import Sanic, response


app = Sanic(__name__)


@app.route("/")
async def test(request):
    return response.json({"answer": "42"})


asyncio.set_event_loop(uvloop.new_event_loop())
server = app.create_server(
    host="0.0.0.0", port=8000, return_asyncio_server=True
)
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(server)
server = loop.run_until_complete(task)
loop.run_until_complete(server.startup())
signal(SIGINT, lambda s, f: loop.stop())

try:
    loop.run_forever()
finally:
    loop.stop()
