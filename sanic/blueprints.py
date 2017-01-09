from collections import defaultdict


class BlueprintSetup:
    """
    """

    def __init__(self, blueprint, app, options):
        self.app = app
        self.blueprint = blueprint
        self.options = options

        url_prefix = self.options.get('url_prefix')
        if url_prefix is None:
            url_prefix = self.blueprint.url_prefix

        #: The prefix that should be used for all URLs defined on the
        #: blueprint.
        self.url_prefix = url_prefix

    def add_route(self, handler, uri, methods):
        """
        A helper method to register a handler to the application url routes.
        """
        if self.url_prefix:
            uri = self.url_prefix + uri

        self.app.route(uri=uri, methods=methods)(handler)

    def add_exception(self, handler, *args, **kwargs):
        """
        Registers exceptions to sanic
        """
        self.app.exception(*args, **kwargs)(handler)

    def add_static(self, uri, file_or_directory, *args, **kwargs):
        """
        Registers static files to sanic
        """
        if self.url_prefix:
            uri = self.url_prefix + uri

        self.app.static(uri, file_or_directory, *args, **kwargs)

    def add_middleware(self, middleware, *args, **kwargs):
        """
        Registers middleware to sanic
        """
        if args or kwargs:
            self.app.middleware(*args, **kwargs)(middleware)
        else:
            self.app.middleware(middleware)


class Blueprint:
    def __init__(self, name, url_prefix=None):
        """
        Creates a new blueprint
        :param name: Unique name of the blueprint
        :param url_prefix: URL to be prefixed before all route URLs
        """
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions = []
        self.listeners = defaultdict(list)

    def record(self, func):
        """
        Registers a callback function that is invoked when the blueprint is
        registered on the application.
        """
        self.deferred_functions.append(func)

    def make_setup_state(self, app, options):
        """
        """
        return BlueprintSetup(self, app, options)

    def register(self, app, options):
        """
        """
        state = self.make_setup_state(app, options)
        for deferred in self.deferred_functions:
            deferred(state)

    def route(self, uri, methods=None):
        """
        """
        def decorator(handler):
            self.record(lambda s: s.add_route(handler, uri, methods))
            return handler
        return decorator

    def add_route(self, handler, uri, methods=None):
        """
        """
        self.record(lambda s: s.add_route(handler, uri, methods))
        return handler

    def listener(self, event):
        """
        """
        def decorator(listener):
            self.listeners[event].append(listener)
            return listener
        return decorator

    def middleware(self, *args, **kwargs):
        """
        """
        def register_middleware(middleware):
            self.record(
                lambda s: s.add_middleware(middleware, *args, **kwargs))
            return middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            middleware = args[0]
            args = []
            return register_middleware(middleware)
        else:
            return register_middleware

    def exception(self, *args, **kwargs):
        """
        """
        def decorator(handler):
            self.record(lambda s: s.add_exception(handler, *args, **kwargs))
            return handler
        return decorator

    def static(self, uri, file_or_directory, *args, **kwargs):
        """
        """
        self.record(
            lambda s: s.add_static(uri, file_or_directory, *args, **kwargs))
