"""
1. Create a simple Sanic app
2. Run with an ASGI server:
    $ uvicorn run_asgi:app
    or
    $ hypercorn run_asgi:app
"""

import os
from sanic import Sanic, response


app = Sanic(__name__)


@app.route("/text")
def handler(request):
    return response.text("Hello")


@app.route("/json")
def handler_foo(request):
    return response.text("bar")


@app.websocket("/ws")
async def feed(request, ws):
    name = "<someone>"
    while True:
        data = f"Hello {name}"
        await ws.send(data)
        name = await ws.recv()

        if not name:
            break


@app.route("/file")
async def test_file(request):
    return await response.file(os.path.abspath("setup.py"))


@app.route("/file_stream")
async def test_file_stream(request):
    return await response.file_stream(
        os.path.abspath("setup.py"), chunk_size=1024
    )
