import aiohttp
import uvloop

from sanic import Sanic
from sanic.response import json

# Create an event loop manually so that we can use it for both sanic & aiohttp
loop = uvloop.new_event_loop()

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

    async with aiohttp.ClientSession(loop=loop) as session:
        response = await fetch(session, url)
        return json(response)


app.run(host="0.0.0.0", port=8000, loop=loop)
