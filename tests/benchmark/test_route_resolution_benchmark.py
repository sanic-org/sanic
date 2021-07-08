from random import choice, seed

from pytest import mark

import sanic.router

from sanic.request import Request


seed("Pack my box with five dozen liquor jugs.")

# Disable Caching for testing purpose
sanic.router.ROUTER_CACHE_SIZE = 0


class TestSanicRouteResolution:
    @mark.asyncio
    async def test_resolve_route_no_arg_string_path(
        self, sanic_router, route_generator, benchmark
    ):
        simple_routes = route_generator.generate_random_direct_route(
            max_route_depth=4
        )
        router, simple_routes = sanic_router(route_details=simple_routes)
        route_to_call = choice(simple_routes)
        request = Request(
            "/{}".format(route_to_call[-1]).encode(),
            {"host": "localhost"},
            "v1",
            route_to_call[0],
            None,
            None,
        )

        result = benchmark.pedantic(
            router.get,
            (
                request.path,
                request.method,
                request.headers.get("host"),
            ),
            iterations=1000,
            rounds=1000,
        )
        assert await result[1](None) == 1

    @mark.asyncio
    async def test_resolve_route_with_typed_args(
        self, sanic_router, route_generator, benchmark
    ):
        typed_routes = route_generator.add_typed_parameters(
            route_generator.generate_random_direct_route(max_route_depth=4),
            max_route_depth=8,
        )
        router, typed_routes = sanic_router(route_details=typed_routes)
        route_to_call = choice(typed_routes)
        url = route_generator.generate_url_for_template(
            template=route_to_call[-1]
        )

        print("{} -> {}".format(route_to_call[-1], url))
        request = Request(
            "/{}".format(url).encode(),
            {"host": "localhost"},
            "v1",
            route_to_call[0],
            None,
            None,
        )

        result = benchmark.pedantic(
            router.get,
            (
                request.path,
                request.method,
                request.headers.get("host"),
            ),
            iterations=1000,
            rounds=1000,
        )
        assert await result[1](None) == 1
