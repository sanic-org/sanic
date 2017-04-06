from sanic import Sanic
from sanic import response

import aiohttp

app = Sanic()

async def fetch(session, url):
    """
    Use session object to perform 'get' request on url
    """
    async with session.get(url) as result:
        return await result.text()


@app.route('/')
async def handle_request(request):
    url = "https://api.github.com/repos/channelcat/sanic"
    
    async with aiohttp.ClientSession() as session:
        result = await fetch(session, url)
        return response.json(result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, workers=2)
