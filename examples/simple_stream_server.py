import asyncio
from sanic import Sanic

app = Sanic(__name__)


@app.stream("/")
async def index(request, response):
    await response.write_headers()
    await asyncio.sleep(1)
    await response.write("Hello\n")
    await asyncio.sleep(1)
    await response.write("World\n")
    await asyncio.sleep(1)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
