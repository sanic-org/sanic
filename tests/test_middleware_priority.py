from functools import partial

import pytest

from sanic import Sanic
from sanic.middleware import Middleware
from sanic.response import json


PRIORITY_TEST_CASES = (
    ([0, 1, 2], [1, 1, 1]),
    ([0, 1, 2], [1, 1, None]),
    ([0, 1, 2], [1, None, None]),
    ([0, 1, 2], [2, 1, None]),
    ([0, 1, 2], [2, 2, None]),
    ([0, 1, 2], [3, 2, 1]),
    ([0, 1, 2], [None, None, None]),
    ([0, 2, 1], [1, None, 1]),
    ([0, 2, 1], [2, None, 1]),
    ([0, 2, 1], [2, None, 2]),
    ([0, 2, 1], [3, 1, 2]),
    ([1, 0, 2], [1, 2, None]),
    ([1, 0, 2], [2, 3, 1]),
    ([1, 0, 2], [None, 1, None]),
    ([1, 2, 0], [1, 3, 2]),
    ([1, 2, 0], [None, 1, 1]),
    ([1, 2, 0], [None, 2, 1]),
    ([1, 2, 0], [None, 2, 2]),
    ([2, 0, 1], [1, None, 2]),
    ([2, 0, 1], [2, 1, 3]),
    ([2, 0, 1], [None, None, 1]),
    ([2, 1, 0], [1, 2, 3]),
    ([2, 1, 0], [None, 1, 2]),
)


@pytest.fixture(autouse=True)
def reset_middleware():
    yield
    Middleware.reset_count()


@pytest.mark.parametrize(
    "expected,priorities",
    PRIORITY_TEST_CASES,
)
def test_request_middleware_order_priority(app: Sanic, expected, priorities):
    order = []

    def add_ident(request, ident):
        order.append(ident)

    @app.get("/")
    def handler(request):
        return json(None)

    for ident, priority in enumerate(priorities):
        kwargs = {}
        if priority is not None:
            kwargs["priority"] = priority
        app.on_request(partial(add_ident, ident=ident), **kwargs)

    app.test_client.get("/")

    assert order == expected


@pytest.mark.parametrize(
    "expected,priorities",
    PRIORITY_TEST_CASES,
)
def test_response_middleware_order_priority(app: Sanic, expected, priorities):
    order = []

    def add_ident(request, response, ident):
        order.append(ident)

    @app.get("/")
    def handler(request):
        return json(None)

    for ident, priority in enumerate(priorities):
        kwargs = {}
        if priority is not None:
            kwargs["priority"] = priority
        app.on_response(partial(add_ident, ident=ident), **kwargs)

    app.test_client.get("/")

    assert order[::-1] == expected
