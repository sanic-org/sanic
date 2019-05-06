import inspect
import os
import sys

from sanic import Sanic
from sanic.response import json


currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe()))
)
sys.path.insert(0, currentdir + "/../../../")


app = Sanic("test")


@app.route("/")
async def test(request):
    return json({"test": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=sys.argv[1])
