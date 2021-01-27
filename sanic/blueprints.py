from collections import defaultdict, namedtuple

from sanic.blueprint_group import BlueprintGroup
from sanic.constants import HTTP_METHODS
from sanic.mixins.base import BaseMixin
from sanic.mixins.middleware import MiddlewareMixin
from sanic.mixins.routes import RouteMixin
from sanic.models.futures import (
    FutureException,
    FutureListener,
    FutureMiddleware,
    FutureRoute,
    FutureStatic,
)
from sanic.views import CompositionView


class Blueprint(BaseMixin, RouteMixin, MiddlewareMixin):
    def __init__(
        self,
        name,
        url_prefix=None,
        host=None,
        version=None,
        strict_slashes=None,
    ):
        """
        In *Sanic* terminology, a **Blueprint** is a logical collection of
        URLs that perform a specific set of tasks which can be identified by
        a unique name.

        :param name: unique name of the blueprint
        :param url_prefix: URL to be prefixed before all route URLs
        :param host: IP Address of FQDN for the sanic server to use.
        :param version: Blueprint Version
        :param strict_slashes: Enforce the API urls are requested with a
            training */*
        """
        self.name = name
        self.url_prefix = url_prefix
        self.host = host

        self.routes = []
        self.websocket_routes = []
        self.exceptions = []
        self.listeners = defaultdict(list)
        self.middlewares = []
        self.statics = []
        self.version = version
        self.strict_slashes = strict_slashes

    def route(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().route(*args, **kwargs)

    def static(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().static(*args, **kwargs)

    def middleware(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().middleware(*args, **kwargs)

    @staticmethod
    def group(*blueprints, url_prefix=""):
        """
        Create a list of blueprints, optionally grouping them under a
        general URL prefix.

        :param blueprints: blueprints to be registered as a group
        :param url_prefix: URL route to be prepended to all sub-prefixes
        """

        def chain(nested):
            """itertools.chain() but leaves strings untouched"""
            for i in nested:
                if isinstance(i, (list, tuple)):
                    yield from chain(i)
                elif isinstance(i, BlueprintGroup):
                    yield from i.blueprints
                else:
                    yield i

        bps = BlueprintGroup(url_prefix=url_prefix)
        for bp in chain(blueprints):
            if bp.url_prefix is None:
                bp.url_prefix = ""
            bp.url_prefix = url_prefix + bp.url_prefix
            bps.append(bp)
        return bps

    def register(self, app, options):
        """
        Register the blueprint to the sanic app.

        :param app: Instance of :class:`sanic.app.Sanic` class
        :param options: Options to be used while registering the
            blueprint into the app.
            *url_prefix* - URL Prefix to override the blueprint prefix
        """

        url_prefix = options.get("url_prefix", self.url_prefix)

        routes = []

        # TODO:
        # - Add BP name to handler name for all routes

        # Routes
        for future in self._future_routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri

            apply_route = FutureRoute(
                future.handler,
                uri[1:] if uri.startswith("//") else uri,
                future.methods,
                future.host or self.host,
                future.strict_slashes,
                future.stream,
                future.version or self.version,
                future.name,
                future.ignore_body,
            )

            route = app._apply_route(apply_route)
            routes.append(route)

        # Static Files
        for future in self._future_statics:
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            apply_route = FutureStatic(uri, *future[1:])
            route = app._apply_static(apply_route)
            routes.append(route)

        route_names = [route.name for route in routes if route]

        # Middleware
        for future in self._future_middleware:
            app._apply_middleware(future, route_names)

        # Exceptions
        for future in self.exceptions:
            app.exception(*future.args, **future.kwargs)(future.handler)

        # Event listeners
        for event, listeners in self.listeners.items():
            for listener in listeners:
                app.listener(event)(listener)

    def listener(self, event):
        """Create a listener from a decorated function.

        :param event: Event to listen to.
        """

        def decorator(listener):
            self.listeners[event].append(listener)
            return listener

        return decorator

    def exception(self, *args, **kwargs):
        """
        This method enables the process of creating a global exception
        handler for the current blueprint under question.

        :param args: List of Python exceptions to be caught by the handler
        :param kwargs: Additional optional arguments to be passed to the
            exception handler

        :return a decorated method to handle global exceptions for any
            route registered under this blueprint.
        """

        def decorator(handler):
            exception = FutureException(handler, args, kwargs)
            self.exceptions.append(exception)
            return handler

        return decorator

    def _generate_name(self, handler, name: str) -> str:
        return f"{self.name}.{name or handler.__name__}"
