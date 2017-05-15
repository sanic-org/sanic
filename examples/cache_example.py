"""
Example of caching using aiocache package. To run it you will need to install
aiocache with `pip install aiocache` plus a Redis instance running
in localhost:6379

Running this example you will see that the first call lasts 3 seconds and
the rest are instant because the value is retrieved from Redis.

If you want more info about the package check
https://github.com/argaen/aiocache
"""

import asyncio
import uuid

from sanic import Sanic
from sanic.response import json
from sanic.log import log

from aiocache import caches, cached


app = Sanic(__name__)


config = {
    "default": {
        "cache": "aiocache.RedisCache",
        "endpoint": "127.0.0.1",
        "timeout": 2,
        "namespace": "sanic",
        "serializer": {
            "class": "aiocache.serializers.JsonSerializer"
        }
    }
}


@app.listener('before_server_start')
def init_cache(sanic, loop):
    caches.set_config(config)


# You can use alias or pass explicit args instead
@cached(key="my_custom_key", ttl=30, alias="default")
async def expensive_call():
    log.info("Expensive has been called")
    await asyncio.sleep(3)
    # You are storing the whole dict under "my_custom_key"
    return {"test": str(uuid.uuid4())}


async def get_cache_value():
    # This lazy loads a singleton so it will return the same instance every
    # time. If you want to create a new instance, you can use
    # `caches.create("default")`
    cache = caches.get("default")
    return await cache.get("my_custom_key")


@app.route("/")
async def test(request):
    log.info("Received GET /")
    return json(await expensive_call())


@app.route("/retrieve")
async def test(request):
    log.info("Received GET /retrieve")
    return json(await get_cache_value())


app.run(host="0.0.0.0", port=8000)
