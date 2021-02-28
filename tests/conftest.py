import random
import re
import string
import sys
import uuid

from typing import Tuple

import pytest

from sanic_routing.exceptions import RouteExists
from sanic_testing import TestManager

from sanic import Sanic
from sanic.constants import HTTP_METHODS
from sanic.router import Router
from sanic.signals import SignalRegistry, SignalContext


random.seed("Pack my box with five dozen liquor jugs.")
Sanic.test_mode = True

if sys.platform in ["win32", "cygwin"]:
    collect_ignore = ["test_worker.py"]


@pytest.fixture
def caplog(caplog):
    yield caplog


async def _handler(request):
    """
    Dummy placeholder method used for route resolver when creating a new
    route into the sanic router. This router is not actually called by the
    sanic app. So do not worry about the arguments to this method.

    If you change the return value of this method, make sure to propagate the
    change to any test case that leverages RouteStringGenerator.
    """
    return 1


TYPE_TO_GENERATOR_MAP = {
    "string": lambda: "".join(
        [random.choice(string.ascii_lowercase) for _ in range(4)]
    ),
    "int": lambda: random.choice(range(1000000)),
    "number": lambda: random.random(),
    "alpha": lambda: "".join(
        [random.choice(string.ascii_lowercase) for _ in range(4)]
    ),
    "uuid": lambda: str(uuid.uuid1()),
}


class RouteStringGenerator:

    ROUTE_COUNT_PER_DEPTH = 100
    HTTP_METHODS = HTTP_METHODS
    ROUTE_PARAM_TYPES = ["string", "int", "number", "alpha", "uuid"]

    def generate_random_direct_route(self, max_route_depth=4):
        routes = []
        for depth in range(1, max_route_depth + 1):
            for _ in range(self.ROUTE_COUNT_PER_DEPTH):
                route = "/".join(
                    [
                        TYPE_TO_GENERATOR_MAP.get("string")()
                        for _ in range(depth)
                    ]
                )
                route = route.replace(".", "", -1)
                route_detail = (random.choice(self.HTTP_METHODS), route)

                if route_detail not in routes:
                    routes.append(route_detail)
        return routes

    def add_typed_parameters(self, current_routes, max_route_depth=8):
        routes = []
        for method, route in current_routes:
            current_length = len(route.split("/"))
            new_route_part = "/".join(
                [
                    "<{}:{}>".format(
                        TYPE_TO_GENERATOR_MAP.get("string")(),
                        random.choice(self.ROUTE_PARAM_TYPES),
                    )
                    for _ in range(max_route_depth - current_length)
                ]
            )
            route = "/".join([route, new_route_part])
            route = route.replace(".", "", -1)
            routes.append((method, route))
        return routes

    @staticmethod
    def generate_url_for_template(template):
        url = template
        for pattern, param_type in re.findall(
            re.compile(r"((?:<\w+:(string|int|number|alpha|uuid)>)+)"),
            template,
        ):
            value = TYPE_TO_GENERATOR_MAP.get(param_type)()
            url = url.replace(pattern, str(value), -1)
        return url


@pytest.fixture(scope="function")
def sanic_router(app):
    # noinspection PyProtectedMember
    def _setup(route_details: tuple) -> Tuple[Router, tuple]:
        router = Router()
        added_router = []
        for method, route in route_details:
            try:
                router.add(
                    uri=f"/{route}",
                    methods=frozenset({method}),
                    host="localhost",
                    handler=_handler,
                )
                added_router.append((method, route))
            except RouteExists:
                pass
        router.finalize()
        return router, added_router

    return _setup


@pytest.fixture(scope="function")
def route_generator() -> RouteStringGenerator:
    return RouteStringGenerator()


@pytest.fixture(scope="function")
def url_param_generator():
    return TYPE_TO_GENERATOR_MAP


@pytest.fixture(scope="function")
def app(request):
    app = Sanic(request.node.name)
    return app


@pytest.fixture(scope="function")
def callback_tracker():
    class Tracker:
        def __init__(self):
            self.called = 0

        def inc(self):
            self.called += 1

        @property
        def call_count(self):
            return self.called

    return Tracker


@pytest.fixture(scope="function")
def signal_registry():
    return SignalRegistry()


@pytest.fixture(scope="function")
def test_signal_context():
    return SignalContext(namespace="test", context="unit-test", action="run")


@pytest.fixture(scope="function")
def dummy_signal_callback():
    def _callback_generator(call_tracker=None):
        async def _callback(app, loop, signal, data):
            call_tracker.inc()
            import logging

            logger = logging.getLogger()
            logger.info(f"{data} {signal}")

        return _callback

    return _callback_generator


@pytest.fixture(scope="function")
def dummy_signal_callback_sync():
    def _callback_generator(call_tracker=None):
        def _callback(app, loop, signal, data):
            call_tracker.inc()
            import logging

            logger = logging.getLogger()
            logger.info(f"{data} {signal}")

        return _callback

    return _callback_generator
