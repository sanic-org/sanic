import asyncio
from sanic import Sanic
from sanic.response import text
from sanic.config import Config
from sanic.exceptions import RequestTimeout

Config.REQUEST_TIMEOUT = 1
app = Sanic(__name__)


@app.route('/')
async def test(request):
    await asyncio.sleep(3)
    return text('Hello, world!')


@app.exception(RequestTimeout)
def timeout(request, exception):
    return text('RequestTimeout from error_handler.', 408)


app.run(host='127.0.0.1', port=8000)
