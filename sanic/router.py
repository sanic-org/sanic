import re
from collections import namedtuple
from functools import lru_cache
from .config import Config
from .exceptions import NotFound, InvalidUsage

Route = namedtuple('Route', ['handler', 'methods', 'pattern', 'parameters'])
Parameter = namedtuple('Parameter', ['name', 'cast'])

REGEX_TYPES = {
    'string': (str, r'[^/]+'),
    'int': (int, r'\d+'),
    'number': (float, r'[0-9\\.]+'),
    'alpha': (str, r'[A-Za-z]+'),
}


class Router:
    """
    Router supports basic routing with parameters and method checks
    Usage:
        @sanic.route('/my/url/<my_parameter>', methods=['GET', 'POST', ...])
        def my_route(request, my_parameter):
            do stuff...

    Parameters will be passed as keyword arguments to the request handling
    function provided Parameters can also have a type by appending :type to
    the <parameter>.  If no type is provided, a string is expected.  A regular
    expression can also be passed in as the type

    TODO:
        This probably needs optimization for larger sets of routes,
        since it checks every route until it finds a match which is bad and
        I should feel bad
    """
    routes = None

    def __init__(self):
        self.routes = []

    def add(self, uri, methods, handler):
        """
        Adds a handler to the route list
        :param uri: Path to match
        :param methods: Array of accepted method names.
        If none are provided, any method is allowed
        :param handler: Request handler function.
        When executed, it should provide a response object.
        :return: Nothing
        """

        # Dict for faster lookups of if method allowed
        if methods:
            methods = frozenset(methods)

        parameters = []

        def add_parameter(match):
            # We could receive NAME or NAME:PATTERN
            parameter_name = match.group(1)
            parameter_pattern = 'string'
            if ':' in parameter_name:
                parameter_name, parameter_pattern = parameter_name.split(':', 1)

            default = (str, parameter_pattern)
            # Pull from pre-configured types
            parameter_type, parameter_pattern = REGEX_TYPES.get(parameter_pattern, default)
            parameters.append(Parameter(name=parameter_name, cast=parameter_type))
            return '({})'.format(parameter_pattern)

        pattern_string = re.sub(r'<(.+?)>', add_parameter, uri)
        pattern = re.compile(r'^{}$'.format(pattern_string))

        route = Route(
            handler=handler, methods=methods, pattern=pattern,
            parameters=parameters)
        self.routes.append(route)

    @lru_cache(maxsize=Config.ROUTER_CACHE_SIZE)
    def get(self, request):
        """
        Gets a request handler based on the URL of the request, or raises an
        error
        :param request: Request object
        :return: handler, arguments, keyword arguments
        """
        route = None
        for route in self.routes:
            match = route.pattern.match(request.url)
            if match:
                break
        else:
            raise NotFound('Requested URL {} not found'.format(request.url))

        if route.methods and request.method not in route.methods:
            raise InvalidUsage(
                'Method {} not allowed for URL {}'.format(
                    request.method, request.url), status_code=405)

        kwargs = {p.name: p.cast(value) for value, p in zip(match.groups(1), route.parameters)}
        return route.handler, [], kwargs
