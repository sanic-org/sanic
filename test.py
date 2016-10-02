from sanic import Sanic
from sanic.response import json, text

app = Sanic("test")

@app.route("/")
async def test(request):
    return json({ "test": True })
@app.route("/text")
def test(request):
    return text('hi')

app.run(host="0.0.0.0")