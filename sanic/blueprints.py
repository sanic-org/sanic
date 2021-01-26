from collections import defaultdict, namedtuple

from sanic.blueprint_group import BlueprintGroup
from sanic.constants import HTTP_METHODS
from sanic.mixins.routes import RouteMixin
from sanic.models.futures import (
    FutureException,
    FutureListener,
    FutureMiddleware,
    FutureRoute,
    FutureStatic,
)
from sanic.views import CompositionView


class Blueprint(RouteMixin):
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
        super().__init__()

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

            _route = app._apply_route(apply_route)

        # TODO:
        # for future in self.websocket_routes:
        #     # attach the blueprint name to the handler so that it can be
        #     # prefixed properly in the router
        #     future.handler.__blueprintname__ = self.name
        #     # Prepend the blueprint URI prefix if available
        #     uri = url_prefix + future.uri if url_prefix else future.uri
        #     _routes, _ = app.websocket(
        #         uri=uri,
        #         host=future.host or self.host,
        #         strict_slashes=future.strict_slashes,
        #         name=future.name,
        #     )(future.handler)
        #     if _routes:
        #         routes += _routes

        # # Static Files
        # for future in self.statics:
        #     # Prepend the blueprint URI prefix if available
        #     uri = url_prefix + future.uri if url_prefix else future.uri
        #     _routes = app.static(
        #         uri, future.file_or_directory, *future.args, **future.kwargs
        #     )
        #     if _routes:
        #         routes += _routes

        # route_names = [route.name for route in routes if route]

        # # Middleware
        # for future in self.middlewares:
        #     if future.args or future.kwargs:
        #         app.register_named_middleware(
        #             future.middleware,
        #             route_names,
        #             *future.args,
        #             **future.kwargs,
        #         )
        #     else:
        #         app.register_named_middleware(future.middleware, route_names)

        # # Exceptions
        # for future in self.exceptions:
        #     app.exception(*future.args, **future.kwargs)(future.handler)

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

    def middleware(self, *args, **kwargs):
        """
        Create a blueprint middleware from a decorated function.

        :param args: Positional arguments to be used while invoking the
            middleware
        :param kwargs: optional keyword args that can be used with the
            middleware.
        """

        def register_middleware(_middleware):
            future_middleware = FutureMiddleware(_middleware, args, kwargs)
            self.middlewares.append(future_middleware)
            return _middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            middleware = args[0]
            args = []
            return register_middleware(middleware)
        else:
            if kwargs.get("bp_group") and callable(args[0]):
                middleware = args[0]
                args = args[1:]
                kwargs.pop("bp_group")
                return register_middleware(middleware)
            else:
                return register_middleware

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

    def static(self, uri, file_or_directory, *args, **kwargs):
        """Create a blueprint static route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        :param file_or_directory: Static asset.
        """
        name = kwargs.pop("name", "static")
        if not name.startswith(self.name + "."):
            name = f"{self.name}.{name}"
        kwargs.update(name=name)

        strict_slashes = kwargs.get("strict_slashes")
        if strict_slashes is None and self.strict_slashes is not None:
            kwargs.update(strict_slashes=self.strict_slashes)

        static = FutureStatic(uri, file_or_directory, args, kwargs)
        self.statics.append(static)
