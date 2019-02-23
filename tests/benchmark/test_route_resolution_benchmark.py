import random
import re
import string
import uuid

from pytest import fixture

import sanic.router

from sanic.router import RouteExists, Router


sanic.router.ROUTER_CACHE_SIZE = 0

random.seed("Pack my box with five dozen liquor jugs.")


async def _handler(request):
    return 1


def _alpha_param_generator():
    return "".join([random.choice(string.ascii_letters) for _ in range(4)])


def _string_param_generator():
    return "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(4)]
    )


def _int_param_generator():
    return random.choice(range(1000000))


def _number_param_generator():
    return random.random()


def _uuid_generator():
    return str(uuid.uuid1())


TYPE_TO_GENERATOR_MAP = {
    "string": _string_param_generator,
    "int": _int_param_generator,
    "number": _number_param_generator,
    "alpha": _alpha_param_generator,
    "uuid": _uuid_generator,
}


def _parse_url_template_and_generate_actual_url(template):
    url = template
    for pattern, param_type in re.findall(
        re.compile(r"((?:<\w+:(string|int|number|alpha|uuid)>)+)"), template
    ):
        value = TYPE_TO_GENERATOR_MAP.get(param_type)()
        url = url.replace(pattern, str(value), -1)
    return url


class RouteStringGenerator:

    ROUTE_COUNT_PER_DEPTH = 100
    HTTP_METHODS = ["GET", "PUT", "POST", "PATCH", "DELETE", "OPTION"]
    ROUTE_PARAM_TYPES = ["string", "int", "number", "alpha", "uuid"]

    def generate_random_direct_route(self, max_route_depth=4):
        routes = []
        for depth in range(1, max_route_depth + 1):
            for _ in range(self.ROUTE_COUNT_PER_DEPTH):
                route = "/".join(
                    [_string_param_generator() for _ in range(depth)]
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
                        _string_param_generator(),
                        random.choice(self.ROUTE_PARAM_TYPES),
                    )
                    for _ in range(max_route_depth - current_length)
                ]
            )
            route = "/".join([route, new_route_part])
            route = route.replace(".", "", -1)
            routes.append((method, route))
        return routes


@fixture(scope="function")
def sanic_router():
    # noinspection PyProtectedMember
    def _setup(route_details: tuple) -> (Router, tuple):
        router = Router()
        added_router = []
        for method, route in route_details:
            try:
                router._add(
                    uri="/{}".format(route),
                    methods=frozenset({method}),
                    host="localhost",
                    handler=_handler,
                )
                added_router.append((method, route))
            except RouteExists as e:
                pass
        return router, added_router

    return _setup


@fixture(scope="function")
def route_generator() -> RouteStringGenerator:
    return RouteStringGenerator()


def test_resolve_route_no_arg_string_path(
    sanic_router, route_generator, benchmark
):
    simple_routes = route_generator.generate_random_direct_route(
        max_route_depth=4
    )
    router, simple_routes = sanic_router(route_details=simple_routes)
    route_to_call = random.choice(simple_routes)

    result = benchmark.pedantic(
        router._get,
        ("/{}".format(route_to_call[-1]), route_to_call[0], "localhost"),
        iterations=1000,
        rounds=1000,
    )
    assert result[0] == _handler


def test_resolve_route_with_typed_args(
    sanic_router, route_generator, benchmark
):
    typed_routes = route_generator.add_typed_parameters(
        route_generator.generate_random_direct_route(max_route_depth=4),
        max_route_depth=8,
    )
    router, typed_routes = sanic_router(route_details=typed_routes)
    route_to_call = random.choice(typed_routes)
    url = _parse_url_template_and_generate_actual_url(
        template=route_to_call[-1]
    )

    print("{} -> {}".format(route_to_call[-1], url))

    result = benchmark.pedantic(
        router._get,
        ("/{}".format(url), route_to_call[0], "localhost"),
        iterations=1000,
        rounds=1000,
    )
    assert result[0] == _handler
