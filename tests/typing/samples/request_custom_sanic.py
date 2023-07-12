from types import SimpleNamespace

from sanic import Request, Sanic
from sanic.config import Config


class CustomConfig(Config):
    pass


app = Sanic("test", config=CustomConfig())


@app.get("/")
async def handler(
    request: Request[Sanic[CustomConfig, SimpleNamespace], SimpleNamespace]
):
    reveal_type(request.ctx)
    reveal_type(request.app)
