from random import randint

from sanic import Sanic
from sanic.response import text


app = Sanic(__name__)


@app.middleware("request")
def append_request(request):
    request.ctx.num = randint(0, 100)


@app.get("/pop")
def pop_handler(request):
    return text(request.ctx.num)


@app.get("/key_exist")
def key_exist_handler(request):
    # Check the key is exist or not
    if hasattr(request.ctx, "num"):
        return text("num exist in request")

    return text("num does not exist in reqeust")


app.run(host="0.0.0.0", port=8000, debug=True)
