"""
Example of caching using aiocache package. To run it you will need a Redis
instance running in localhost:6379.

Running this example you will see that the first call lasts 3 seconds and
the rest are instant because the value is retrieved from the Redis.

If you want more info about the package check
https://github.com/argaen/aiocache
"""

import asyncio

import aiocache
from aiocache import RedisCache, cached
from aiocache.serializers import JsonSerializer

from sanic import Sanic
from sanic.log import log
from sanic.response import json

app = Sanic(__name__)
aiocache.set_defaults(cache=RedisCache)


@cached(key="my_custom_key", serializer=JsonSerializer())
async def expensive_call():
    log.info("Expensive has been called")
    await asyncio.sleep(3)
    return {"test": True}


@app.route("/")
async def test(request):
    log.info("Received GET /")
    return json(await expensive_call())


app.run(host="0.0.0.0", port=8000, loop=asyncio.get_event_loop())
