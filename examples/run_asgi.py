"""
1. Create a simple Sanic app
2. Run with an ASGI server:
    $ uvicorn run_asgi:app
    or
    $ hypercorn run_asgi:app
"""

from sanic import Sanic
from sanic.response import text


app = Sanic(__name__)

@app.route("/")
def handler(request):
    return text("Hello")

@app.route("/foo")
def handler_foo(request):
    return text("bar")


@app.websocket('/feed')
async def feed(request, ws):
    name = "<someone>"
    while True:
        data = f"Hello {name}"
        await ws.send(data)
        name = await ws.recv()

        if not name:
            break


if __name__ == '__main__':
    app.run(debug=True)
