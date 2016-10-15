# Run with python3 simple_server.py PORT

from aiohttp import web
import asyncio
import sys
import uvloop

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

async def handle(request):
    return web.json_response({"test":True})

app = web.Application(loop=loop)
app.router.add_route('GET', '/', handle)

web.run_app(app, port=sys.argv[1])
