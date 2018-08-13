from collections import defaultdict, namedtuple
from functools import wraps
from inspect import iscoroutinefunction

from sanic.constants import HTTP_METHODS
from sanic.views import CompositionView

FutureRoute = namedtuple('Route',
                         ['handler', 'uri', 'methods', 'host',
                          'strict_slashes', 'stream', 'version', 'name'])
FutureListener = namedtuple('Listener', ['handler', 'uri', 'methods', 'host'])
FutureMiddleware = namedtuple('Route', ['middleware', 'args', 'kwargs'])
FutureException = namedtuple('Route', ['handler', 'args', 'kwargs'])
FutureStatic = namedtuple('Route',
                          ['uri', 'file_or_directory', 'args', 'kwargs'])


class Blueprint:
    def __init__(self, name,
                 url_prefix=None,
                 host=None, version=None,
                 strict_slashes=False):
        """Create a new blueprint

        :param name: unique name of the blueprint
        :param url_prefix: URL to be prefixed before all route URLs
        :param strict_slashes: strict to trailing slash
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
    def group(*blueprints, url_prefix=''):
        """Create a list of blueprints, optionally
        grouping them under a general URL prefix.

        :param blueprints: blueprints to be registered as a group
        :param url_prefix: URL route to be prepended to all sub-prefixes
        """
        def chain(nested):
            """itertools.chain() but leaves strings untouched"""
            for i in nested:
                if isinstance(i, (list, tuple)):
                    yield from chain(i)
                else:
                    yield i
        bps = []
        for bp in chain(blueprints):
            bp.url_prefix = url_prefix + bp.url_prefix
            bps.append(bp)
        return bps

    def register(self, app, options):
        """Register the blueprint to the sanic app."""

        url_prefix = options.get('url_prefix', self.url_prefix)

        # Routes
        for future in self.routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri

            version = future.version or self.version

            app.route(uri=uri[1:] if uri.startswith('//') else uri,
                      methods=future.methods,
                      host=future.host or self.host,
                      strict_slashes=future.strict_slashes,
                      stream=future.stream,
                      version=version,
                      name=future.name,
                      )(future.handler)

        for future in self.websocket_routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            app.websocket(uri=uri,
                          host=future.host or self.host,
                          strict_slashes=future.strict_slashes,
                          name=future.name,
                          )(future.handler)

        # Middleware
        for future in self.middlewares:
            if future.args or future.kwargs:
                app.register_middleware(future.middleware,
                                        *future.args,
                                        **future.kwargs)
            else:
                app.register_middleware(future.middleware)

        # Exceptions
        for future in self.exceptions:
            app.exception(*future.args, **future.kwargs)(future.handler)

        # Static Files
        for future in self.statics:
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            app.static(uri, future.file_or_directory,
                       *future.args, **future.kwargs)

        # Event listeners
        for event, listeners in self.listeners.items():
            for listener in listeners:
                app.listener(event)(listener)

    def route(self, uri, methods=frozenset({'GET'}), host=None,
              strict_slashes=None, stream=False, version=None, name=None):
        """Create a blueprint route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        :param methods: list of acceptable HTTP methods.
        """
        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def decorator(handler):
            route = FutureRoute(
                handler, uri, methods, host, strict_slashes, stream, version,
                name)
            self.routes.append(route)
            return handler
        return decorator

    def add_route(self, handler, uri, methods=frozenset({'GET'}), host=None,
                  strict_slashes=None, version=None, name=None):
        """Create a blueprint route from a function.

        :param handler: function for handling uri requests. Accepts function,
                        or class instance with a view_class method.
        :param uri: endpoint at which the route will be accessible.
        :param methods: list of acceptable HTTP methods.
        :param host:
        :param strict_slashes:
        :param version:
        :param name: user defined route name for url_for
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, 'view_class'):
            methods = set()

            for method in HTTP_METHODS:
                if getattr(handler.view_class, method.lower(), None):
                    methods.add(method)

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()

        self.route(uri=uri, methods=methods, host=host,
                   strict_slashes=strict_slashes, version=version,
                   name=name)(handler)
        return handler

    def websocket(self, uri, host=None, strict_slashes=None, version=None,
                  name=None):
        """Create a blueprint websocket route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        """
        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def decorator(handler):
            route = FutureRoute(handler, uri, [], host, strict_slashes,
                                False, version, name)
            self.websocket_routes.append(route)
            return handler
        return decorator

    def add_websocket_route(self, handler, uri, host=None, version=None,
                            name=None):
        """Create a blueprint websocket route from a function.

        :param handler: function for handling uri requests. Accepts function,
                        or class instance with a view_class method.
        :param uri: endpoint at which the route will be accessible.
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
        """Create a blueprint middleware from a decorated function."""
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
            return register_middleware

    # Decorator
    def filter(self, old_handler=None, name=None):
        # There should be a function to deduce handler from name.
        # Currently I have no idea how to do it :( .
        if old_handler is None and name is None:
            raise Exception('You should give at lease one of old_handler/name')

        def decorator(handler_filter):
            handler_is_coroutine = iscoroutinefunction(old_handler)
            filter_is_coroutine = iscoroutinefunction(handler_filter)
            # ensure the outside filter must be a coroutine
            # if the handler is already a coroutine
            if handler_is_coroutine and not filter_is_coroutine:
                raise TypeError("Coroutine inside a non-coroutine function")

            if filter_is_coroutine:
                # ensure the handler is given being a coroutine.
                if not handler_is_coroutine:
                    @wraps(old_handler)
                    async def async_handler(*args, **kwargs):
                        return old_handler(*args, **kwargs)
                else:
                    async_handler = old_handler

                @wraps(async_handler)
                async def new_handler(*args, **kwargs):
                    return await handler_filter(async_handler, *args, **kwargs)
            else:
                # handler is just a normal function
                # I force it to be async
                @wraps(old_handler)
                async def new_handler(*args, **kwargs):
                    return handler_filter(old_handler, *args, **kwargs)

            # we have the new handler now
            for i, route in enumerate(self.routes):
                if route.handler is old_handler:
                    self.routes[i] = route._replace(handler=new_handler)
            for i, route in enumerate(self.websocket_routes):
                if route.handler is old_handler:
                    self.websocket_routes[i] = route._replace(
                        handler=new_handler
                    )
            # so one could continuously use handler decorator
            return new_handler
        return decorator

    def exception(self, *args, **kwargs):
        """Create a blueprint exception from a decorated function."""
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
        name = kwargs.pop('name', 'static')
        if not name.startswith(self.name + '.'):
            name = '{}.{}'.format(self.name, name)
        kwargs.update(name=name)

        strict_slashes = kwargs.get('strict_slashes')
        if strict_slashes is None and self.strict_slashes is not None:
            kwargs.update(strict_slashes=self.strict_slashes)

        static = FutureStatic(uri, file_or_directory, args, kwargs)
        self.statics.append(static)

    # Shorthand method decorators
    def get(self, uri, host=None, strict_slashes=None, version=None,
            name=None):
        return self.route(uri, methods=["GET"], host=host,
                          strict_slashes=strict_slashes, version=version,
                          name=name)

    def post(self, uri, host=None, strict_slashes=None, stream=False,
             version=None, name=None):
        return self.route(uri, methods=["POST"], host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version, name=name)

    def put(self, uri, host=None, strict_slashes=None, stream=False,
            version=None, name=None):
        return self.route(uri, methods=["PUT"], host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version, name=name)

    def head(self, uri, host=None, strict_slashes=None, version=None,
             name=None):
        return self.route(uri, methods=["HEAD"], host=host,
                          strict_slashes=strict_slashes, version=version,
                          name=name)

    def options(self, uri, host=None, strict_slashes=None, version=None,
                name=None):
        return self.route(uri, methods=["OPTIONS"], host=host,
                          strict_slashes=strict_slashes, version=version,
                          name=name)

    def patch(self, uri, host=None, strict_slashes=None, stream=False,
              version=None, name=None):
        return self.route(uri, methods=["PATCH"], host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version, name=name)

    def delete(self, uri, host=None, strict_slashes=None, version=None,
               name=None):
        return self.route(uri, methods=["DELETE"], host=host,
                          strict_slashes=strict_slashes, version=version,
                          name=name)
