from sanic import Sanic
from sanic.response import redirect


app = Sanic(__name__)


app.static("index.html", "websocket.html")


@app.route("/")
def index(request):
    return redirect("index.html")


@app.websocket("/feed")
async def feed(request, ws):
    while True:
        data = "hello!"
        print("Sending: " + data)
        await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
