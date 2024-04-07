from sanic import Request, Sanic
from sanic.config import Config


class CustomConfig(Config):
    pass


class Foo:
    pass


class RequestContext:
    foo: Foo


class CustomRequest(Request[Sanic[CustomConfig, Foo], RequestContext]):
    @staticmethod
    def make_context() -> RequestContext:
        ctx = RequestContext()
        ctx.foo = Foo()
        return ctx


app = Sanic(
    "test", config=CustomConfig(), ctx=Foo(), request_class=CustomRequest
)


@app.get("/")
async def handler(request: CustomRequest):
    reveal_type(request)  # noqa
    reveal_type(request.ctx)  # noqa
    reveal_type(request.app)  # noqa
