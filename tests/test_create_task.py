import sanic
from sanic.utils import sanic_endpoint_test
from sanic.response import text
from threading import Event
import asyncio

def test_create_task():
    e = Event()
    async def coro():
        await asyncio.sleep(0.05)
        e.set()

    app = sanic.Sanic()
    app.add_task(coro)

    @app.route('/early')
    def not_set(request):
        return text(e.is_set())

    @app.route('/late')
    async def set(request):
        await asyncio.sleep(0.1)
        return text(e.is_set())


    request, response = sanic_endpoint_test(app, uri='/early')
    assert response.body == b'False'

    request, response = sanic_endpoint_test(app, uri='/late')
    assert response.body == b'True'
