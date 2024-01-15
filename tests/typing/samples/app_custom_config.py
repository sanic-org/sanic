from sanic import Sanic
from sanic.config import Config


class CustomConfig(Config):
    pass


app = Sanic("test", config=CustomConfig())
reveal_type(app)  # noqa
