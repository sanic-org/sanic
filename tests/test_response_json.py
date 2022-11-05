import json

from functools import partial
from unittest.mock import Mock

import pytest

from sanic import Request, Sanic
from sanic.exceptions import SanicException
from sanic.response import json as json_response
from sanic.response.types import JSONResponse


JSON_BODY = {"ok": True}
json_dumps = partial(json.dumps, separators=(",", ":"))


@pytest.fixture
def json_app(app: Sanic):
    @app.get("/json")
    async def handle(request: Request):
        return json_response(JSON_BODY)

    return app


def test_body_can_be_retrieved(json_app: Sanic):
    _, resp = json_app.test_client.get("/json")
    assert resp.body == json_dumps(JSON_BODY).encode()


def test_body_can_be_set(json_app: Sanic):
    new_body = b'{"hello":"world"}'

    @json_app.on_response
    def set_body(request: Request, response: JSONResponse):
        response.body = new_body

    _, resp = json_app.test_client.get("/json")
    assert resp.body == new_body


def test_raw_body_can_be_retrieved(json_app: Sanic):
    @json_app.on_response
    def check_body(request: Request, response: JSONResponse):
        assert response.raw_body == JSON_BODY

    json_app.test_client.get("/json")


def test_raw_body_can_be_set(json_app: Sanic):
    new_body = {"hello": "world"}

    @json_app.on_response
    def set_body(request: Request, response: JSONResponse):
        response.raw_body = new_body
        assert response.raw_body == new_body
        assert response.body == json_dumps(new_body).encode()

    json_app.test_client.get("/json")


def test_raw_body_cant_be_retrieved_after_body_set(json_app: Sanic):
    new_body = b'{"hello":"world"}'

    @json_app.on_response
    def check_raw_body(request: Request, response: JSONResponse):
        response.body = new_body
        with pytest.raises(SanicException):
            response.raw_body

    json_app.test_client.get("/json")


def test_raw_body_can_be_reset_after_body_set(json_app: Sanic):
    new_body = b'{"hello":"world"}'
    new_new_body = {"lorem": "ipsum"}

    @json_app.on_response
    def set_bodies(request: Request, response: JSONResponse):
        response.body = new_body
        response.raw_body = new_new_body

    _, resp = json_app.test_client.get("/json")
    assert resp.body == json_dumps(new_new_body).encode()


def test_set_body_method(json_app: Sanic):
    new_body = {"lorem": "ipsum"}

    @json_app.on_response
    def set_body(request: Request, response: JSONResponse):
        response.set_body(new_body)

    _, resp = json_app.test_client.get("/json")
    assert resp.body == json_dumps(new_body).encode()


def test_set_body_method_after_body_set(json_app: Sanic):
    new_body = b'{"hello":"world"}'
    new_new_body = {"lorem": "ipsum"}

    @json_app.on_response
    def set_body(request: Request, response: JSONResponse):
        response.body = new_body
        response.set_body(new_new_body)

    _, resp = json_app.test_client.get("/json")
    assert resp.body == json_dumps(new_new_body).encode()


def test_custom_dumps_and_kwargs(json_app: Sanic):
    custom_dumps = Mock(return_value="custom")

    @json_app.get("/json-custom")
    async def handle_custom(request: Request):
        return json_response(JSON_BODY, dumps=custom_dumps, prry="platypus")

    _, resp = json_app.test_client.get("/json-custom")
    assert resp.body == "custom".encode()
    custom_dumps.assert_called_once_with(JSON_BODY, prry="platypus")


def test_override_dumps_and_kwargs(json_app: Sanic):
    custom_dumps_1 = Mock(return_value="custom1")
    custom_dumps_2 = Mock(return_value="custom2")

    @json_app.get("/json-custom")
    async def handle_custom(request: Request):
        return json_response(JSON_BODY, dumps=custom_dumps_1, prry="platypus")

    @json_app.on_response
    def set_body(request: Request, response: JSONResponse):
        response.set_body(JSON_BODY, dumps=custom_dumps_2, platypus="prry")

    _, resp = json_app.test_client.get("/json-custom")

    assert resp.body == "custom2".encode()
    custom_dumps_1.assert_called_once_with(JSON_BODY, prry="platypus")
    custom_dumps_2.assert_called_once_with(JSON_BODY, platypus="prry")
