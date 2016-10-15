import re
from collections import namedtuple
from .exceptions import NotFound, InvalidUsage

Route = namedtuple("Route", ['handler', 'methods', 'pattern', 'parameters'])
Parameter = namedtuple("Parameter", ['name', 'cast'])


class Router:
    """
    Router supports basic routing with parameters and method checks
    Usage:
        @sanic.route('/my/url/<my_parameter>', methods=['GET', 'POST', ...])
        def my_route(request, my_parameter):
            do stuff...

    Parameters will be passed as keyword arguments to the request handling function provided
    Parameters can also have a type by appending :type to the <parameter>.  If no type is provided,
        a string is expected.  A regular expression can also be passed in as the type

    TODO:
        This probably needs optimization for larger sets of routes,
        since it checks every route until it finds a match which is bad and I should feel bad
    """
    routes = None
    regex_types = {
        "string": (None, "\w+"),
        "int": (int, "\d+"),
        "number": (float, "[0-9\\.]+"),
        "alpha": (None, "[A-Za-z]+"),
    }

    def __init__(self):
        self.routes = []

    def add(self, uri, methods, handler):
        """
        Adds a handler to the route list
        :param uri: Path to match
        :param methods: Array of accepted method names.  If none are provided, any method is allowed
        :param handler: Request handler function.  When executed, it should provide a response object.
        :return: Nothing
        """

        # Dict for faster lookups of if method allowed
        methods_dict = {method: True for method in methods} if methods else None

        parameters = []

        def add_parameter(match):
            # We could receive NAME or NAME:PATTERN
            parts = match.group(1).split(':')
            if len(parts) == 2:
                parameter_name, parameter_pattern = parts
            else:
                parameter_name = parts[0]
                parameter_pattern = 'string'

            # Pull from pre-configured types
            parameter_regex = self.regex_types.get(parameter_pattern)
            if parameter_regex:
                parameter_type, parameter_pattern = parameter_regex
            else:
                parameter_type = None

            parameter = Parameter(name=parameter_name, cast=parameter_type)
            parameters.append(parameter)

            return "({})".format(parameter_pattern)

        pattern_string = re.sub("<(.+?)>", add_parameter, uri)
        pattern = re.compile("^{}$".format(pattern_string))

        route = Route(handler=handler, methods=methods_dict, pattern=pattern, parameters=parameters)
        self.routes.append(route)

    def get(self, request):
        """
        Gets a request handler based on the URL of the request, or raises an error
        :param request: Request object
        :return: handler, arguments, keyword arguments
        """

        route = None
        args = []
        kwargs = {}
        for _route in self.routes:
            match = _route.pattern.match(request.url)
            if match:
                for index, parameter in enumerate(_route.parameters, start=1):
                    value = match.group(index)
                    kwargs[parameter.name] = parameter.cast(value) if parameter.cast is not None else value
                route = _route
                break

        if route:
            if route.methods and not request.method in route.methods:
                raise InvalidUsage("Method {} not allowed for URL {}".format(request.method, request.url),
                                   status_code=405)
            return route.handler, args, kwargs
        else:
            raise NotFound("Requested URL {} not found".format(request.url))


class SimpleRouter:
    """
    Simple router records and reads all routes from a dictionary
    It does not support parameters in routes, but is very fast
    """
    routes = None

    def __init__(self):
        self.routes = {}

    def add(self, uri, methods, handler):
        # Dict for faster lookups of method allowed
        methods_dict = {method: True for method in methods} if methods else None
        self.routes[uri] = Route(handler=handler, methods=methods_dict, pattern=uri, parameters=None)

    def get(self, request):
        route = self.routes.get(request.url)
        if route:
            if route.methods and not request.method in route.methods:
                raise InvalidUsage("Method {} not allowed for URL {}".format(request.method, request.url),
                                   status_code=405)
            return route.handler, [], {}
        else:
            raise NotFound("Requested URL {} not found".format(request.url))
