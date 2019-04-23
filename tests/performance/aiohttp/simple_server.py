# Run with python3 simple_server.py PORT

import asyncio
import sys

import ujson as json
import uvloop

from aiohttp import web


loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)


async def handle(request):
    return web.Response(
        body=json.dumps({"test": True}).encode("utf-8"),
        content_type="application/json",
    )


app = web.Application(loop=loop)
app.router.add_route("GET", "/", handle)

web.run_app(app, port=sys.argv[1], access_log=None)
