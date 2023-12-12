from types import SimpleNamespace

from sanic import Request, Sanic
from sanic.config import Config


class Foo:
    pass


app = Sanic("test")


@app.get("/")
async def handler(request: Request[Sanic[Config, SimpleNamespace], Foo]):
    reveal_type(request.ctx)
    reveal_type(request.app)
