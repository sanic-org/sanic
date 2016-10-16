# Run with: python3 -O simple_server.py
import asyncio
from kyoukai import Kyoukai, HTTPRequestContext
import logging
import ujson
import uvloop

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

kyk = Kyoukai("example_app")

logger = logging.getLogger("Kyoukai")
logger.setLevel(logging.ERROR)

@kyk.route("/")
async def index(ctx: HTTPRequestContext):
    return ujson.dumps({"test":True}), 200, {"Content-Type": "application/json"}

kyk.run()