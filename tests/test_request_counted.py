from unittest.mock import Mock

import pytest

from sanic_testing.reusable import ReusableClient

from sanic import Sanic
from sanic.compat import Header
from sanic.request import CountedRequest
from sanic.response import json


@pytest.fixture(autouse=True)
def reset_counter():
    yield
    CountedRequest.reset_count()


def test_counter_increments(app: Sanic):
    app.request_class = CountedRequest

    @app.get("/")
    async def handler(request: CountedRequest):
        return json({"count": request.count})

    @app.get("/info")
    async def info(request: CountedRequest):
        return json({"state": request.app.m.state})

    with ReusableClient(app) as client:
        for i in range(1, 10):
            _, response = client.get("/")
            assert response.json["count"] == i


def test_counter_increment_on_state(app: Sanic):
    mock = Mock()
    mock.state = {}
    app.multiplexer = mock

    for i in range(1, 10):
        CountedRequest(b"/", Header({}), "", "", Mock(), app)
        assert CountedRequest.count == i
