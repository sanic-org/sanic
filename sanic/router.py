from functools import lru_cache
from typing import FrozenSet, Iterable, List, Optional, Union

from sanic_routing import BaseRouter
from sanic_routing.exceptions import NoMethod
from sanic_routing.exceptions import NotFound as RoutingNotFound
from sanic_routing.route import Route

from sanic.constants import HTTP_METHODS
from sanic.exceptions import MethodNotSupported, NotFound
from sanic.request import Request


ROUTER_CACHE_SIZE = 1024


class Router(BaseRouter):
    """
    The router implementation responsible for routing a :class:`Request` object
    to the appropriate handler.
    """

    DEFAULT_METHOD = "GET"
    ALLOWED_METHODS = HTTP_METHODS

    # Putting the lru_cache on Router.get() performs better for the benchmarsk
    # at tests/benchmark/test_route_resolution_benchmark.py
    # However, overall application performance is significantly improved
    # with the lru_cache on this method.
    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def _get(self, path, method, host):
        try:
            route, handler, params = self.resolve(
                path=path,
                method=method,
                extra={"host": host},
            )
        except RoutingNotFound as e:
            raise NotFound("Requested URL {} not found".format(e.path))
        except NoMethod as e:
            raise MethodNotSupported(
                "Method {} not allowed for URL {}".format(method, path),
                method=method,
                allowed_methods=e.allowed_methods,
            )

        # TODO: Implement response
        # - args,
        # - endpoint,

        return (
            handler,
            (),
            params,
            route.path,
            route.name,
            None,
            route.ctx.ignore_body,
        )

    def get(self, request: Request):
        """
        Retrieve a `Route` object containg the details about how to handle
        a response for a given request

        :param request: the incoming request object
        :type request: Request
        :return: details needed for handling the request and returning the
            correct response
        :rtype: Tuple[ RouteHandler, Tuple[Any, ...], Dict[str, Any], str, str,
            Optional[str], bool, ]
        """
        return self._get(
            request.path, request.method, request.headers.get("host")
        )

    def add(
        self,
        uri: str,
        methods: Iterable[str],
        handler,
        host: Optional[Union[str, FrozenSet[str]]] = None,
        strict_slashes: bool = False,
        stream: bool = False,
        ignore_body: bool = False,
        version: Union[str, float, int] = None,
        name: Optional[str] = None,
        unquote: bool = False,
        static: bool = False,
    ) -> Union[Route, List[Route]]:
        """
        Add a handler to the router

        :param uri: the path of the route
        :type uri: str
        :param methods: the types of HTTP methods that should be attached,
            example: ``["GET", "POST", "OPTIONS"]``
        :type methods: Iterable[str]
        :param handler: the sync or async function to be executed
        :type handler: RouteHandler
        :param host: host that the route should be on, defaults to None
        :type host: Optional[str], optional
        :param strict_slashes: whether to apply strict slashes, defaults
            to False
        :type strict_slashes: bool, optional
        :param stream: whether to stream the response, defaults to False
        :type stream: bool, optional
        :param ignore_body: whether the incoming request body should be read,
            defaults to False
        :type ignore_body: bool, optional
        :param version: a version modifier for the uri, defaults to None
        :type version: Union[str, float, int], optional
        :param name: an identifying name of the route, defaults to None
        :type name: Optional[str], optional
        :return: the route object
        :rtype: Route
        """
        # TODO: Implement
        # - host
        # - strict_slashes
        # - ignore_body
        # - stream
        if version is not None:
            version = str(version).strip("/").lstrip("v")
            uri = "/".join([f"/v{version}", uri.lstrip("/")])

        params = dict(
            path=uri,
            handler=handler,
            methods=methods,
            name=name,
            strict=strict_slashes,
            unquote=unquote,
        )

        if isinstance(host, str):
            hosts = [host]
        else:
            hosts = host or [None]

        routes = []

        for host in hosts:
            if host:
                params.update({"requirements": {"host": host}})

            route = super().add(**params)
            route.ctx.ignore_body = ignore_body
            route.ctx.stream = stream
            route.ctx.hosts = hosts
            route.ctx.static = static

            routes.append(route)

        if len(routes) == 1:
            return routes[0]
        return routes

    def is_stream_handler(self, request) -> bool:
        """
        Handler for request is stream or not.

        :param request: Request object
        :return: bool
        """
        try:
            handler = self.get(request)[0]
        except (NotFound, MethodNotSupported):
            return False
        if hasattr(handler, "view_class") and hasattr(
            handler.view_class, request.method.lower()
        ):
            handler = getattr(handler.view_class, request.method.lower())
        return hasattr(handler, "is_stream")

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def find_route_by_view_name(self, view_name, name=None):
        """
        Find a route in the router based on the specified view name.

        :param view_name: string of view name to search by
        :param kwargs: additional params, usually for static files
        :return: tuple containing (uri, Route)
        """
        if not view_name:
            return None

        # TODO:
        # - Check blueprint naming, we shouldn't need to double check here
        #   but it seems like blueprints are not receiving full names
        #   probably need tocheck the blueprint registration func
        route = self.name_index.get(view_name)
        if not route:
            full_name = self.ctx.app._generate_name(view_name)
            route = self.name_index.get(full_name)

        if not route:
            return None

        return route

    @property
    def routes_all(self):
        return self.routes

    @property
    def routes_static(self):
        return self.static_routes

    @property
    def routes_dynamic(self):
        return self.dynamic_routes

    @property
    def routes_regex(self):
        return self.regex_routes
