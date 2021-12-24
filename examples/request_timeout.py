import asyncio

from sanic import Sanic, response
from sanic.config import Config
from sanic.exceptions import RequestTimeout


Config.REQUEST_TIMEOUT = 1
app = Sanic("Example")


@app.route("/")
async def test(request):
    await asyncio.sleep(3)
    return response.text("Hello, world!")


@app.exception(RequestTimeout)
def timeout(request, exception):
    return response.text("RequestTimeout from error_handler.", 408)


app.run(host="0.0.0.0", port=8000)
