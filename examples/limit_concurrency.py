from sanic import Sanic
from sanic.response import json

import asyncio
import aiohttp

app = Sanic(__name__)

sem = None


@app.listener('before_server_start')
def init(sanic, loop):
    global sem
    concurrency_per_worker = 4
    sem = asyncio.Semaphore(concurrency_per_worker, loop=loop)

async def bounded_fetch(session, url):
    """
    Use session object to perform 'get' request on url
    """
    async with sem, session.get(url) as response:
        return await response.json()


@app.route("/")
async def test(request):
    """
    Download and serve example JSON
    """
    url = "https://api.github.com/repos/channelcat/sanic"

    async with aiohttp.ClientSession() as session:
        response = await bounded_fetch(session, url)
        return json(response)


app.run(host="0.0.0.0", port=8000, workers=2)
