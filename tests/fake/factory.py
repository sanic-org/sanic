from sanic import Sanic


def run():
    app = Sanic("FactoryTest")
    return app
