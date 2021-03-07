from random import choice, seed

from pytest import mark

from httptools import parse_url
from urllib.parse import urlparse

import sanic.router

from sanic.request import Request


seed("Pack my box with five dozen liquor jugs.")

# Disable Caching for testing purpose
sanic.router.ROUTER_CACHE_SIZE = 0


# noinspection PyBroadException
class TestURLParseBenchmark:
    @mark.asyncio
    @mark.parametrize(
        ("callback", "name"),
        [(urlparse, "urlparse"), (parse_url, "parse_url")],
    )
    async def test_benchmark_url_parser(
        self, callback, name, benchmark, urlparse_benchmark_data
    ):
        def _get_parser(cb):
            def _run(*records):
                for record in records:
                    try:
                        cb(record["input"].encode())
                    except:
                        pass

            return _run

        benchmark.pedantic(
            _get_parser(callback),
            urlparse_benchmark_data,
            iterations=100,
            rounds=100,
        )


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

        result = benchmark.pedantic(
            router.get,
            (
                Request(
                    "/{}".format(route_to_call[-1]).encode(),
                    {"host": "localhost"},
                    "v1",
                    route_to_call[0],
                    None,
                    None,
                ),
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

        result = benchmark.pedantic(
            router.get,
            (
                Request(
                    "/{}".format(url).encode(),
                    {"host": "localhost"},
                    "v1",
                    route_to_call[0],
                    None,
                    None,
                ),
            ),
            iterations=1000,
            rounds=1000,
        )
        assert await result[1](None) == 1
