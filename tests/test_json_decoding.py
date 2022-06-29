from json import loads as sloads

import pytest


try:
    from ujson import loads as uloads

    NO_UJSON = False
    DEFAULT_LOADS = uloads
except ModuleNotFoundError:
    NO_UJSON = True
    DEFAULT_LOADS = sloads

from sanic import Request, Sanic, json


@pytest.fixture(autouse=True)
def default_back_to_ujson():
    yield
    Request._loads = DEFAULT_LOADS


def test_change_decoder():
    Sanic("Test", loads=sloads)
    assert Request._loads == sloads


def test_change_decoder_to_some_custom():
    def my_custom_decoder(some_str: str):
        dict = sloads(some_str)
        dict["some_key"] = "new_value"
        return dict

    app = Sanic("Test", loads=my_custom_decoder)
    assert Request._loads == my_custom_decoder

    req_body = {"some_key": "some_value"}

    @app.post("/test")
    def handler(request):
        new_json = request.json
        return json(new_json)

    req, res = app.test_client.post("/test", json=req_body)
    assert sloads(res.body) == {"some_key": "new_value"}


@pytest.mark.skipif(NO_UJSON is True, reason="ujson not installed")
def test_default_decoder():
    Sanic("Test")
    assert Request._loads == uloads
