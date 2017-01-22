from sanic import Sanic
from sanic.response import json

import aiohttp

app = Sanic(__name__)

async def fetch(session, url):
    """
    Use session object to perform 'get' request on url
    """
    async with session.get(url) as response:
        return await response.json()


@app.route("/")
async def test(request):
    """
    Download and serve example JSON
    """
    url = "https://api.github.com/repos/channelcat/sanic"

    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url)
        return json(response)


app.run(host="0.0.0.0", port=8000, workers=2)
