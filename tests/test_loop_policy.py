from sanic import Sanic
from sanic.response import text
from sanic.utils import sanic_endpoint_test
import asyncio
import uvloop

def test_loop_policy():
    app = Sanic('test_loop_policy')

    @app.route('/')
    def test(request):
        return text("OK")

    server = app.create_server()

    request, response = sanic_endpoint_test(app)
    assert isinstance(asyncio.get_event_loop_policy(),
                      uvloop.EventLoopPolicy)
