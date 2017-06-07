from sanic import Sanic
import pytest


class MongoDB:

    def __init__(self, name):
        self.name = name


class ClientSession:

    def __init__(self, name):
        self.name = name


def test_app_extensions():
    app = Sanic("test_app")
    app["session"] = ClientSession("session")
    app["db"] = MongoDB("mongo")
    assert len(app) == 2
    assert app["session"].name == "session"
    assert app["db"].name == "mongo"


def test_app_extensions_delete():
    app = Sanic("test_app")
    app["session"] = ClientSession("session")
    assert len(app) == 1
    del app["session"]
    assert len(app) == 0


def test_app_extensions_iteration():
    app = Sanic("test_app")
    app["session"] = ClientSession("session")
    app["db"] = MongoDB("mongo")
    count = 0
    for extension in app:
        count = count + 1
    assert count == 2


def test_app_equal():
    app_1 = Sanic("test_app_1")
    app_2 = Sanic("test_app_2")
    assert (app_1 == app_2) == False
    assert (app_1 == app_1) == True
