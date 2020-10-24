from collections import defaultdict, namedtuple

from sanic.blueprint_group import BlueprintGroup
from sanic.constants import HTTP_METHODS
from sanic.views import CompositionView


FutureRoute = namedtuple(
    "FutureRoute",
    [
        "handler",
        "uri",
        "methods",
        "host",
        "strict_slashes",
        "stream",
        "version",
        "name",
    ],
)
FutureListener = namedtuple(
    "FutureListener", ["handler", "uri", "methods", "host"]
)
FutureMiddleware = namedtuple(
    "FutureMiddleware", ["middleware", "args", "kwargs"]
)
FutureException = namedtuple("FutureException", ["handler", "args", "kwargs"])
FutureStatic = namedtuple(
    "FutureStatic", ["uri", "file_or_directory", "args", "kwargs"]
)


class Blueprint:
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

        # Routes
        for future in self.routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri

            version = future.version or self.version

            _routes, _ = app.route(
                uri=uri[1:] if uri.startswith("//") else uri,
                methods=future.methods,
                host=future.host or self.host,
                strict_slashes=future.strict_slashes,
                stream=future.stream,
                version=version,
                name=future.name,
            )(future.handler)
            if _routes:
                routes += _routes

        for future in self.websocket_routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            _routes, _ = app.websocket(
                uri=uri,
                host=future.host or self.host,
                strict_slashes=future.strict_slashes,
                name=future.name,
            )(future.handler)
            if _routes:
                routes += _routes

        # Static Files
        for future in self.statics:
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            _routes = app.static(
                uri, future.file_or_directory, *future.args, **future.kwargs
            )
            if _routes:
                routes += _routes

        route_names = [route.name for route in routes if route]

        # Middleware
        for future in self.middlewares:
            if future.args or future.kwargs:
                app.register_named_middleware(
                    future.middleware,
                    route_names,
                    *future.args,
                    **future.kwargs,
                )
            else:
                app.register_named_middleware(future.middleware, route_names)

        # Exceptions
        for future in self.exceptions:
            app.exception(*future.args, **future.kwargs)(future.handler)

        # Event listeners
        for event, listeners in self.listeners.items():
            for listener in listeners:
                app.listener(event)(listener)

    def route(
        self,
        uri,
        methods=frozenset({"GET"}),
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """Create a blueprint route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        :param methods: list of acceptable HTTP methods.
        :param host: IP Address of FQDN for the sanic server to use.
        :param strict_slashes: Enforce the API urls are requested with a
            training */*
        :param stream: If the route should provide a streaming support
        :param version: Blueprint Version
        :param name: Unique name to identify the Route

        :return a decorated method that when invoked will return an object
            of type :class:`FutureRoute`
        """
        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def decorator(handler):
            route = FutureRoute(
                handler,
                uri,
                methods,
                host,
                strict_slashes,
                stream,
                version,
                name,
            )
            self.routes.append(route)
            return handler

        return decorator

    def add_route(
        self,
        handler,
        uri,
        methods=frozenset({"GET"}),
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        stream=False,
    ):
        """Create a blueprint route from a function.

        :param handler: function for handling uri requests. Accepts function,
                        or class instance with a view_class method.
        :param uri: endpoint at which the route will be accessible.
        :param methods: list of acceptable HTTP methods.
        :param host: IP Address of FQDN for the sanic server to use.
        :param strict_slashes: Enforce the API urls are requested with a
            training */*
        :param version: Blueprint Version
        :param name: user defined route name for url_for
        :param stream: boolean specifying if the handler is a stream handler
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, "view_class"):
            methods = set()

            for method in HTTP_METHODS:
                if getattr(handler.view_class, method.lower(), None):
                    methods.add(method)

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()

        self.route(
            uri=uri,
            methods=methods,
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )(handler)
        return handler

    def websocket(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """Create a blueprint websocket route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        :param host: IP Address of FQDN for the sanic server to use.
        :param strict_slashes: Enforce the API urls are requested with a
            training */*
        :param version: Blueprint Version
        :param name: Unique name to identify the Websocket Route
        """
        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def decorator(handler):
            nonlocal uri
            nonlocal host
            nonlocal strict_slashes
            nonlocal version
            nonlocal name

            name = f"{self.name}.{name or handler.__name__}"
            route = FutureRoute(
                handler, uri, [], host, strict_slashes, False, version, name
            )
            self.websocket_routes.append(route)
            return handler

        return decorator

    def add_websocket_route(
        self, handler, uri, host=None, version=None, name=None
    ):
        """Create a blueprint websocket route from a function.

        :param handler: function for handling uri requests. Accepts function,
                        or class instance with a view_class method.
        :param uri: endpoint at which the route will be accessible.
        :param host: IP Address of FQDN for the sanic server to use.
        :param version: Blueprint Version
        :param name: Unique name to identify the Websocket Route
        :return: function or class instance
        """
        self.websocket(uri=uri, host=host, version=version, name=name)(handler)
        return handler

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

    # Shorthand method decorators
    def get(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **GET** *HTTP* method

        :param uri: URL to be tagged to **GET** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"GET"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def post(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **POST** *HTTP* method

        :param uri: URL to be tagged to **POST** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"POST"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def put(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **PUT** *HTTP* method

        :param uri: URL to be tagged to **PUT** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"PUT"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def head(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **HEAD** *HTTP* method

        :param uri: URL to be tagged to **HEAD** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"HEAD"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def options(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **OPTIONS** *HTTP* method

        :param uri: URL to be tagged to **OPTIONS** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"OPTIONS"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def patch(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **PATCH** *HTTP* method

        :param uri: URL to be tagged to **PATCH** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"PATCH"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def delete(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **DELETE** *HTTP* method

        :param uri: URL to be tagged to **DELETE** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`sanic.app.Sanic` to check
            if the request URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"DELETE"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )
