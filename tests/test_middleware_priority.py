from functools import partial

import pytest

from sanic import Sanic
from sanic.middleware import Middleware, MiddlewareLocation
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


def test_add_register_priority(app: Sanic):
    def foo(*_):
        ...

    app.register_middleware(foo, priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 0
    assert app.request_middleware[0].priority == 999  # type: ignore
    app.register_middleware(foo, attach_to="response", priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 1
    assert app.response_middleware[0].priority == 999  # type: ignore


def test_add_register_named_priority(app: Sanic):
    def foo(*_):
        ...

    app.register_named_middleware(foo, route_names=["foo"], priority=999)
    assert len(app.named_request_middleware) == 1
    assert len(app.named_response_middleware) == 0
    assert app.named_request_middleware["foo"][0].priority == 999  # type: ignore
    app.register_named_middleware(
        foo, attach_to="response", route_names=["foo"], priority=999
    )
    assert len(app.named_request_middleware) == 1
    assert len(app.named_response_middleware) == 1
    assert app.named_response_middleware["foo"][0].priority == 999  # type: ignore


def test_add_decorator_priority(app: Sanic):
    def foo(*_):
        ...

    app.middleware(foo, priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 0
    assert app.request_middleware[0].priority == 999  # type: ignore
    app.middleware(foo, attach_to="response", priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 1
    assert app.response_middleware[0].priority == 999  # type: ignore


def test_add_convenience_priority(app: Sanic):
    def foo(*_):
        ...

    app.on_request(foo, priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 0
    assert app.request_middleware[0].priority == 999  # type: ignore
    app.on_response(foo, priority=999)
    assert len(app.request_middleware) == 1
    assert len(app.response_middleware) == 1
    assert app.response_middleware[0].priority == 999  # type: ignore


def test_add_conflicting_priority(app: Sanic):
    def foo(*_):
        ...

    middleware = Middleware(foo, MiddlewareLocation.REQUEST, priority=998)
    app.register_middleware(middleware=middleware, priority=999)
    assert app.request_middleware[0].priority == 999  # type: ignore
    middleware.priority == 998


def test_add_conflicting_priority_named(app: Sanic):
    def foo(*_):
        ...

    middleware = Middleware(foo, MiddlewareLocation.REQUEST, priority=998)
    app.register_named_middleware(
        middleware=middleware, route_names=["foo"], priority=999
    )
    assert app.named_request_middleware["foo"][0].priority == 999  # type: ignore
    middleware.priority == 998


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
