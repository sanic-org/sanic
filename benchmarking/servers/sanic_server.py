from sanic import Sanic
from sanic.response import json, text

app = Sanic(__name__)


@app.route("/")
async def default(request):
    return json({"msg": "msg"})


@app.route("/text")
async def txt(request):
    return text("msg")


@app.route("/json")
async def json_data(request):
    return json({
        "some": "other"
    })
app.run(host="0.0.0.0", port=9898)
