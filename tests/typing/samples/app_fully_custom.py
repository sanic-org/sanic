from sanic import Sanic
from sanic.config import Config


class CustomConfig(Config):
    pass


class Foo:
    pass


app = Sanic("test", config=CustomConfig(), ctx=Foo())
reveal_type(app)  # noqa