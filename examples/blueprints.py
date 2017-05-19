from sanic import Sanic
from sanic import Blueprint
from sanic.response import json, text


app = Sanic(__name__)
blueprint = Blueprint('name', url_prefix='/my_blueprint')
blueprint2 = Blueprint('name2', url_prefix='/my_blueprint2')
blueprint3 = Blueprint('name3', url_prefix='/my_blueprint3')


@blueprint.route('/foo')
async def foo(request):
    return json({'msg': 'hi from blueprint'})


@blueprint2.route('/foo')
async def foo2(request):
    return json({'msg': 'hi from blueprint2'})


@blueprint3.websocket('/foo')
async def foo3(request, ws):
    while True:
        data = 'hello!'
        print('Sending: ' + data)
        await ws.send(data)
        data = await ws.recv()
        print('Received: ' + data)

app.blueprint(blueprint)
app.blueprint(blueprint2)
app.blueprint(blueprint3)

app.run(host="0.0.0.0", port=8000, debug=True)
