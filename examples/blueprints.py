from sanic import Blueprint, Sanic
from sanic.response import file, json


app = Sanic("Example")
blueprint = Blueprint("bp_example", url_prefix="/my_blueprint")
blueprint2 = Blueprint("bp_example2", url_prefix="/my_blueprint2")
blueprint3 = Blueprint("bp_example3", url_prefix="/my_blueprint3")


@blueprint.route("/foo")
async def foo(request):
    return json({"msg": "hi from blueprint"})


@blueprint2.route("/foo")
async def foo2(request):
    return json({"msg": "hi from blueprint2"})


@blueprint3.route("/foo")
async def index(request):
    return await file("websocket.html")


@app.websocket("/feed")
async def foo3(request, ws):
    while True:
        data = "hello!"
        print("Sending: " + data)
        await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)


app.blueprint(blueprint)
app.blueprint(blueprint2)
app.blueprint(blueprint3)

app.run(host="0.0.0.0", port=9999, debug=True)
