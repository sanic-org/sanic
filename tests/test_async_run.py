from sanic import Sanic
from sanic.response import json
import asyncio
import requests
from threading import Thread
import pytest
import sys

@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="fails on python 3.5 with travis")
def test_async_run():
    app = Sanic(__name__)

    @app.route("/")
    async def test(request):
        return json({"answer": "42"})

    server = app.create_server(host="0.0.0.0", port=8001)
    task = asyncio.ensure_future(server)
    loop = asyncio.get_event_loop()
    t = Thread(target=loop.run_forever)
    t.start()
    res = requests.get('http://localhost:8001')
    loop.stop()
    assert res.json()['answer'] == '42'
