from sanic import Sanic
from sanic.response import json, text

app = Sanic("test")

@app.route("/")
async def test(request):
    return json({ "test": True })

@app.route("/text")
def test(request):
    return text('hi')

@app.route("/post_json")
def test(request):
    return json({ "received": True, "message": request.json })

@app.route("/query_string")
def test(request):
    return json({ "parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string })

app.run(host="0.0.0.0")