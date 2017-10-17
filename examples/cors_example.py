from sanic import Sanic
from sanic import response

app = Sanic(__name__)


@app.route("/")
@response.cors()
async def test(request):
    return response.json({"test": True})


@app.route("/t2")
@response.cors()
def test2(request):
    return response.json({"test": True})


@app.websocket('/feed')
@response.cors()
async def feed(request, ws):
    while True:
        data = 'hello!'
        print('Sending: ' + data)
        await ws.send(data)
        data = await ws.recv()
        print('Received: ' + data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
