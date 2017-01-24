from sanic import Sanic
from sanic.response import json
from multiprocessing import Event
from signal import signal, SIGINT
import asyncio

app = Sanic(__name__)

@app.route("/")
async def test(request):
    return json({"answer": "42"})

server = app.create_server(host="0.0.0.0", port=8001)
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(server)
signal(SIGINT, lambda s, f: loop.close())
try:
    loop.run_forever()
except:
    loop.stop()
