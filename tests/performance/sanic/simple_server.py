import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir + '/../../../')

from sanic import Sanic
from sanic.response import json

app = Sanic("test")


@app.route("/")
async def test(request):
    return json({"test": True})


app.run(host="0.0.0.0", port=sys.argv[1])
