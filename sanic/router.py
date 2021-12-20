from __future__ import annotations

from functools import lru_cache
from inspect import signature
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from uuid import UUID

from sanic_routing import BaseRouter  # type: ignore
from sanic_routing.exceptions import NoMethod  # type: ignore
from sanic_routing.exceptions import (
    NotFound as RoutingNotFound,  # type: ignore
)
from sanic_routing.route import Route  # type: ignore

from sanic.constants import HTTP_METHODS
from sanic.errorpages import check_error_format
from sanic.exceptions import MethodNotSupported, NotFound, SanicException
from sanic.models.handler_types import RouteHandler


ROUTER_CACHE_SIZE = 1024
ALLOWED_LABELS = ("__file_uri__",)


class Router(BaseRouter):
    """
    The router implementation responsible for routing a :class:`Request` object
    to the appropriate handler.
    """

    DEFAULT_METHOD = "GET"
    ALLOWED_METHODS = HTTP_METHODS

    def _get(
        self, path: str, method: str, host: Optional[str]
    ) -> Tuple[Route, RouteHandler, Dict[str, Any]]:
        try:
            return self.resolve(
                path=path,
                method=method,
                extra={"host": host} if host else None,
            )
        except RoutingNotFound as e:
            raise NotFound("Requested URL {} not found".format(e.path))
        except NoMethod as e:
            raise MethodNotSupported(
                "Method {} not allowed for URL {}".format(method, path),
                method=method,
                allowed_methods=e.allowed_methods,
            )

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def get(  # type: ignore
        self, path: str, method: str, host: Optional[str]
    ) -> Tuple[Route, RouteHandler, Dict[str, Any]]:
        """
        Retrieve a `Route` object containing the details about how to handle
        a response for a given request

        :param request: the incoming request object
        :type request: Request
        :return: details needed for handling the request and returning the
            correct response
        :rtype: Tuple[ Route, RouteHandler, Dict[str, Any]]
        """
        return self._get(path, method, host)

    def add(  # type: ignore
        self,
        uri: str,
        methods: Iterable[str],
        handler: RouteHandler,
        host: Optional[Union[str, Iterable[str]]] = None,
        strict_slashes: bool = False,
        stream: bool = False,
        ignore_body: bool = False,
        version: Union[str, float, int] = None,
        name: Optional[str] = None,
        unquote: bool = False,
        static: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
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
        if version is not None:
            version = str(version).strip("/").lstrip("v")
            uri = "/".join([f"{version_prefix}{version}", uri.lstrip("/")])

        uri = self._normalize(uri, handler)

        params = dict(
            path=uri,
            handler=handler,
            methods=frozenset(map(str, methods)) if methods else None,
            name=name,
            strict=strict_slashes,
            unquote=unquote,
        )

        if isinstance(host, str):
            hosts = [host]
        else:
            hosts = host or [None]  # type: ignore

        routes = []

        for host in hosts:
            if host:
                params.update({"requirements": {"host": host}})

            route = super().add(**params)  # type: ignore
            route.ctx.ignore_body = ignore_body
            route.ctx.stream = stream
            route.ctx.hosts = hosts
            route.ctx.static = static
            route.ctx.error_format = error_format

            if error_format:
                check_error_format(route.ctx.error_format)

            routes.append(route)

        if len(routes) == 1:
            return routes[0]
        return routes

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

        route = self.name_index.get(view_name)
        if not route:
            full_name = self.ctx.app._generate_name(view_name)
            route = self.name_index.get(full_name)

        if not route:
            return None

        return route

    @property
    def routes_all(self):
        return {route.parts: route for route in self.routes}

    @property
    def routes_static(self):
        return self.static_routes

    @property
    def routes_dynamic(self):
        return self.dynamic_routes

    @property
    def routes_regex(self):
        return self.regex_routes

    def finalize(self, *args, **kwargs):
        super().finalize(*args, **kwargs)

        for route in self.dynamic_routes.values():
            if any(
                label.startswith("__") and label not in ALLOWED_LABELS
                for label in route.labels
            ):
                raise SanicException(
                    f"Invalid route: {route}. Parameter names cannot use '__'."
                )

    def _normalize(self, uri: str, handler: RouteHandler) -> str:
        if "<" not in uri:
            return uri

        sig = signature(handler)
        mapping = {
            param.name: param.annotation.__name__.lower()
            for param in sig.parameters.values()
            if param.annotation in (str, int, float, UUID)
        }

        reconstruction = []
        for part in uri.split("/"):
            if part.startswith("<") and ":" not in part:
                name = part[1:-1]
                annotation = mapping.get(name)
                if annotation:
                    part = f"<{name}:{annotation}>"
            reconstruction.append(part)
        return "/".join(reconstruction)
