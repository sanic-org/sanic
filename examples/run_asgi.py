"""
1. Create a simple Sanic app
0. Run with an ASGI server:
    $ uvicorn run_asgi:app
    or
    $ hypercorn run_asgi:app
"""

from pathlib import Path

from sanic import Sanic, response


app = Sanic("Example")


@app.route("/text")
def handler_text(request):
    return response.text("Hello")


@app.route("/json")
def handler_json(request):
    return response.json({"foo": "bar"})


@app.websocket("/ws")
async def handler_ws(request, ws):
    name = "<someone>"
    while True:
        data = f"Hello {name}"
        await ws.send(data)
        name = await ws.recv()

        if not name:
            break


@app.route("/file")
async def handler_file(request):
    return await response.file(Path("../") / "setup.py")


@app.route("/file_stream")
async def handler_file_stream(request):
    return await response.file_stream(
        Path("../") / "setup.py", chunk_size=1024
    )


@app.post("/stream", stream=True)
async def handler_stream(request):
    while True:
        body = await request.stream.read()
        if body is None:
            break
        body = body.decode("utf-8").replace("1", "A")
        await response.write(body)
    return response.stream(body)


@app.before_server_start
async def listener_before_server_start(*args, **kwargs):
    print("before_server_start")


@app.after_server_start
async def listener_after_server_start(*args, **kwargs):
    print("after_server_start")


@app.before_server_stop
async def listener_before_server_stop(*args, **kwargs):
    print("before_server_stop")


@app.after_server_stop
async def listener_after_server_stop(*args, **kwargs):
    print("after_server_stop")


@app.on_request
async def print_on_request(request):
    print("print_on_request")


@app.on_response
async def print_on_response(request, response):
    print("print_on_response")
