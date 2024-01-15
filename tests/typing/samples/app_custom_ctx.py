from sanic import Sanic


class Foo:
    pass


app = Sanic("test", ctx=Foo())
reveal_type(app)  # noqa
