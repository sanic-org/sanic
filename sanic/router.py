from functools import lru_cache
from typing import Iterable, Optional, Union

from sanic_routing import BaseRouter
from sanic_routing.route import Route

from sanic.constants import HTTP_METHODS
from sanic.request import Request


class Router(BaseRouter):
    """
    The router implementation responsible for routing a :class:`Request` object
    to the appropriate handler.
    """

    DEFAULT_METHOD = "GET"
    ALLOWED_METHODS = HTTP_METHODS

    @lru_cache
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
        route, handler, params = self.resolve(
            path=request.path,
            method=request.method,
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

    def add(
        self,
        uri: str,
        methods: Iterable[str],
        handler,
        host: Optional[str] = None,
        strict_slashes: bool = False,
        stream: bool = False,
        ignore_body: bool = False,
        version: Union[str, float, int] = None,
        name: Optional[str] = None,
    ) -> Route:
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

        route = super().add(
            path=uri, handler=handler, methods=methods, name=name
        )
        route.ctx.ignore_body = ignore_body
        route.ctx.stream = stream

        return route
