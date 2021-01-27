from functools import lru_cache

from sanic_routing import BaseRouter
from sanic_routing.route import Route

from sanic.constants import HTTP_METHODS
from sanic.request import Request


class Router(BaseRouter):
    DEFAULT_METHOD = "GET"
    ALLOWED_METHODS = HTTP_METHODS

    @lru_cache
    def get(self, request: Request):
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
        uri,
        methods,
        handler,
        host=None,
        strict_slashes=False,
        stream=False,
        ignore_body=False,
        version=None,
        name=None,
    ) -> Route:
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
