from .exceptions import InvalidUsage


class HTTPMethodView:
    """ Simple class based implementation of view for the sanic.
    You should implement methods (get, post, put, patch, delete) for the class
    to every HTTP method you want to support.

    For example:
        class DummyView(HTTPMethodView):

            def get(self, request, *args, **kwargs):
                return text('I am get method')

            def put(self, request, *args, **kwargs):
                return text('I am put method')
    etc.

    If someone tries to use a non-implemented method, there will be a
    405 response.

    If you need any url params just mention them in method definition:
        class DummyView(HTTPMethodView):

            def get(self, request, my_param_here, *args, **kwargs):
                return text('I am get method with %s' % my_param_here)

    To add the view into the routing you could use
        1) app.add_route(DummyView.as_view(), '/')
        2) app.route('/')(DummyView.as_view())

    To add any decorator you could set it into decorators variable
    """

    decorators = []

    def dispatch_request(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower(), None)
        if handler:
            return handler(request, *args, **kwargs)
        raise InvalidUsage(
            'Method {} not allowed for URL {}'.format(
                request.method, request.url), status_code=405)

    @classmethod
    def as_view(cls, *class_args, **class_kwargs):
        """ Converts the class into an actual view function that can be used
        with the routing system.

        """
        def view(*args, **kwargs):
            self = view.view_class(*class_args, **class_kwargs)
            return self.dispatch_request(*args, **kwargs)

        if cls.decorators:
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)

        view.view_class = cls
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        return view


class CompositionView:
    """ Simple method-function mapped view for the sanic.
    You can add handler functions to methods (get, post, put, patch, delete)
    for every HTTP method you want to support.

    For example:
        view = CompositionView()
        view.add(['GET'], lambda request: text('I am get method'))
        view.add(['POST', 'PUT'], lambda request: text('I am post/put method'))

    etc.

    If someone tries to use a non-implemented method, there will be a
    405 response.
    """

    def __init__(self):
        self.handlers = {}

    def add(self, methods, handler):
        for method in methods:
            if method in self.handlers:
                raise KeyError(
                    'Method {} already is registered.'.format(method))
            self.handlers[method] = handler

    def __call__(self, request, *args, **kwargs):
        handler = self.handlers.get(request.method.upper(), None)
        if handler is None:
            raise InvalidUsage(
                'Method {} not allowed for URL {}'.format(
                    request.method, request.url), status_code=405)
        return handler(request, *args, **kwargs)
