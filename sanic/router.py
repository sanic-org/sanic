from functools import lru_cache

from sanic_routing import BaseRouter

from sanic.constants import HTTP_METHODS
from sanic.log import logger
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
        # - ignore_body,

        return handler, (), params, route.path, route.name, None, False

    def add(
        self,
        uri,
        methods,
        handler,
        host=None,
        strict_slashes=False,
        ignore_body=False,
        version=None,
        name=None,
    ):
        # TODO: Implement
        # - host
        # - strict_slashes
        # - version
        # - ignore_body
        super().add(path=uri, handler=handler, methods=methods, name=name)
