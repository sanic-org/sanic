

class BlueprintSetup():
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

    def add_url_rule(self, uri, methods=None, handler=None, **options):
        """A helper method to register a handler to the application url routes.

        """
        if self.url_prefix:
            uri = self.url_prefix + uri

        self.app.router.add(uri, methods, handler)


class Blueprint():
    def __init__(self, name, url_prefix=None):
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions = []

    def record(self, func):
        """Registers a callback function that is invoked when the blueprint is
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
            self.add_url_rule(uri=uri, methods=methods, handler=handler)
            return handler
        return decorator

    def add_url_rule(self, uri, methods=None, handler=None):
        """
        """
        self.record(lambda s:
            s.add_url_rule(uri, methods, handler))
