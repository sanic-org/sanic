import asyncio

import httpx

from sanic import Sanic
from sanic.response import json


app = Sanic("Example")

sem = None


@app.before_server_start
def init(sanic, _):
    global sem
    concurrency_per_worker = 4
    sem = asyncio.Semaphore(concurrency_per_worker)


async def bounded_fetch(session, url):
    """
    Use session object to perform 'get' request on url
    """
    async with sem:
        response = await session.get(url)
        return response.json()


@app.route("/")
async def test(request):
    """
    Download and serve example JSON
    """
    url = "https://api.github.com/repos/sanic-org/sanic"

    async with httpx.AsyncClient() as session:
        response = await bounded_fetch(session, url)
        return json(response)


app.run(host="0.0.0.0", port=8000, workers=2)
