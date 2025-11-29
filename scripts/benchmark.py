"""Benchmark script for Sanic route resolution.

Replaces the previous pytest-benchmark based tests."""

import asyncio
import statistics
import time
from random import choice, seed

from sanic import Sanic
from sanic.constants import HTTP_METHODS
from sanic.request import Request
from sanic.router import Router


# Set seed for reproducibility
seed("Pack my box with five dozen liquor jugs.")


class RouteGenerator:
    """Generate routes for benchmarking."""
    
    ROUTE_COUNT_PER_DEPTH = 100
    HTTP_METHODS = HTTP_METHODS
    
    @staticmethod
    def generate_random_direct_route(max_route_depth=4):
        """Generate random direct routes without parameters."""
        import random
        import string
        
        routes = []
        for depth in range(1, max_route_depth + 1):
            for _ in range(RouteGenerator.ROUTE_COUNT_PER_DEPTH):
                route = "/".join(
                    ["".join([random.choice(string.ascii_lowercase) for _ in range(4)])
                     for _ in range(depth)]
                )
                route = route.replace(".", "", -1)
                route_detail = (random.choice(RouteGenerator.HTTP_METHODS), route)
                
                if route_detail not in routes:
                    routes.append(route_detail)
        return routes
    
    @staticmethod
    def add_typed_parameters(current_routes, max_route_depth=8):
        """Add typed parameters to routes."""
        import random
        import string
        
        param_types = ["str", "int", "float", "alpha", "uuid"]
        routes = []
        
        for method, route in current_routes:
            current_length = len(route.split("/"))
            new_route_part = "/".join(
                [
                    "<{}:{}>".format(
                        "".join([random.choice(string.ascii_lowercase) for _ in range(4)]),
                        random.choice(param_types),
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
        """Generate a URL from a route template."""
        import random
        import re
        import string
        import uuid
        
        type_generators = {
            "str": lambda: "".join([random.choice(string.ascii_lowercase) for _ in range(4)]),
            "int": lambda: random.choice(range(1000000)),
            "float": lambda: random.random(),
            "alpha": lambda: "".join([random.choice(string.ascii_lowercase) for _ in range(4)]),
            "uuid": lambda: str(uuid.uuid1()),
        }
        
        url = template
        for pattern, param_type in re.findall(
            re.compile(r"((?:<\w+:(str|int|float|alpha|uuid)>)+)"),
            template,
        ):
            value = type_generators.get(param_type)()
            url = url.replace(pattern, str(value), -1)
        return url


async def _handler(request):
    """Dummy handler for route resolution."""
    return 1


def setup_router(route_details, app_name="benchmark"):
    """Set up a router with the given routes."""
    from sanic_routing.exceptions import RouteExists
    
    app = Sanic(app_name)
    router = Router()
    router.ctx.app = app
    added_routes = []
    
    for method, route in route_details:
        try:
            router.add(
                uri=f"/{route}",
                methods=frozenset({method}),
                host="localhost",
                handler=_handler,
            )
            added_routes.append((method, route))
        except RouteExists:
            pass
    
    router.finalize()
    return router, added_routes


def benchmark_function(func, args, iterations=1000, rounds=1000):
    """Benchmark a function with the given arguments."""
    all_times = []
    
    for round_num in range(rounds):
        start = time.perf_counter()
        for _ in range(iterations):
            result = func(*args)
        end = time.perf_counter()
        all_times.append((end - start) / iterations)
    
    return {
        "min": min(all_times),
        "max": max(all_times),
        "mean": statistics.mean(all_times),
        "median": statistics.median(all_times),
        "iterations": iterations,
        "rounds": rounds,
    }


async def test_resolve_route_no_arg_string_path():
    """Benchmark route resolution for simple string paths."""
    print("\n" + "="*80)
    print("Benchmark: Route resolution (no arguments, string paths)")
    print("="*80)
    
    generator = RouteGenerator()
    simple_routes = generator.generate_random_direct_route(max_route_depth=4)
    router, simple_routes = setup_router(route_details=simple_routes, app_name="benchmark_simple")
    route_to_call = choice(simple_routes)
    
    request = Request(
        f"/{route_to_call[-1]}".encode(),
        {"host": "localhost"},
        "v1",
        route_to_call[0],
        None,
        None,
    )
    
    print(f"Testing route: {route_to_call[0]} /{route_to_call[-1]}")
    print(f"Total routes in router: {len(simple_routes)}")
    
    result = benchmark_function(
        router.get,
        (request.path, request.method, request.headers.get("host")),
        iterations=1000,
        rounds=1000,
    )
    
    # Verify the result works
    handler_result = await result.get("_test_result", router.get(
        request.path, request.method, request.headers.get("host")
    ))[1](None)
    assert handler_result == 1, "Route resolution returned unexpected result"
    
    print(f"\nResults (per call):")
    print(f"  Min:    {result['min']*1000000:.2f} µs")
    print(f"  Max:    {result['max']*1000000:.2f} µs")
    print(f"  Mean:   {result['mean']*1000000:.2f} µs")
    print(f"  Median: {result['median']*1000000:.2f} µs")
    print(f"  Iterations: {result['iterations']}, Rounds: {result['rounds']}")
    
    return result


async def test_resolve_route_with_typed_args():
    """Benchmark route resolution with typed parameters."""
    print("\n" + "="*80)
    print("Benchmark: Route resolution (with typed parameters)")
    print("="*80)
    
    generator = RouteGenerator()
    typed_routes = generator.add_typed_parameters(
        generator.generate_random_direct_route(max_route_depth=4),
        max_route_depth=8,
    )
    router, typed_routes = setup_router(route_details=typed_routes, app_name="benchmark_typed")
    route_to_call = choice(typed_routes)
    url = generator.generate_url_for_template(template=route_to_call[-1])
    
    print(f"Testing route template: {route_to_call[0]} /{route_to_call[-1]}")
    print(f"Generated URL: /{url}")
    print(f"Total routes in router: {len(typed_routes)}")
    
    request = Request(
        f"/{url}".encode(),
        {"host": "localhost"},
        "v1",
        route_to_call[0],
        None,
        None,
    )
    
    result = benchmark_function(
        router.get,
        (request.path, request.method, request.headers.get("host")),
        iterations=1000,
        rounds=1000,
    )
    
    # Verify the result works
    handler_result = await result.get("_test_result", router.get(
        request.path, request.method, request.headers.get("host")
    ))[1](None)
    assert handler_result == 1, "Route resolution returned unexpected result"
    
    print(f"\nResults (per call):")
    print(f"  Min:    {result['min']*1000000:.2f} µs")
    print(f"  Max:    {result['max']*1000000:.2f} µs")
    print(f"  Mean:   {result['mean']*1000000:.2f} µs")
    print(f"  Median: {result['median']*1000000:.2f} µs")
    print(f"  Iterations: {result['iterations']}, Rounds: {result['rounds']}")
    
    return result


async def main():
    """Run all benchmarks."""
    import sanic.router
    
    # Clear any existing Sanic app registrations
    Sanic._app_registry.clear()
    
    # Disable caching for benchmarking
    sanic.router.ROUTER_CACHE_SIZE = 0
    
    print("Sanic Route Resolution Benchmarks")
    print("=" * 80)
    print("Note: Router caching is disabled for accurate benchmarking")
    
    try:
        result1 = await test_resolve_route_no_arg_string_path()
        result2 = await test_resolve_route_with_typed_args()
        
        print("\n" + "="*80)
        print("All benchmarks completed successfully!")
        print("="*80)
        
        return 0
    except Exception as e:
        print(f"\n❌ Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
