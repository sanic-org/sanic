import re
from collections import defaultdict, namedtuple
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


def url_hash(url):
    return url.count('/')


class RouteExists(Exception):
    pass


class Router:
    """
    Router supports basic routing with parameters and method checks
    Usage:
        @sanic.route('/my/url/<my_parameter>', methods=['GET', 'POST', ...])
        def my_route(request, my_parameter):
            do stuff...
    or
        @sanic.route('/my/url/<my_paramter>:type', methods['GET', 'POST', ...])
        def my_route_with_type(request, my_parameter):
            do stuff...

    Parameters will be passed as keyword arguments to the request handling
    function. Provided parameters can also have a type by appending :type to
    the <parameter>. Given parameter must be able to be type-casted to this.
    If no type is provided, a string is expected.  A regular expression can
    also be passed in as the type. The argument given to the function will
    always be a string, independent of the type.
    """
    routes_static = None
    routes_dynamic = None
    routes_always_check = None

    def __init__(self):
        self.routes_all = {}
        self.routes_static = {}
        self.routes_dynamic = defaultdict(list)
        self.routes_always_check = []

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
        if uri in self.routes_all:
            raise RouteExists("Route already registered: {}".format(uri))

        # Dict for faster lookups of if method allowed
        if methods:
            methods = frozenset(methods)

        parameters = []
        properties = {"unhashable": None}

        def add_parameter(match):
            # We could receive NAME or NAME:PATTERN
            name = match.group(1)
            pattern = 'string'
            if ':' in name:
                name, pattern = name.split(':', 1)

            default = (str, pattern)
            # Pull from pre-configured types
            _type, pattern = REGEX_TYPES.get(pattern, default)
            parameter = Parameter(name=name, cast=_type)
            parameters.append(parameter)

            # Mark the whole route as unhashable if it has the hash key in it
            if re.search('(^|[^^]){1}/', pattern):
                properties['unhashable'] = True
            # Mark the route as unhashable if it matches the hash key
            elif re.search(pattern, '/'):
                properties['unhashable'] = True

            return '({})'.format(pattern)

        pattern_string = re.sub(r'<(.+?)>', add_parameter, uri)
        pattern = re.compile(r'^{}$'.format(pattern_string))

        route = Route(
            handler=handler, methods=methods, pattern=pattern,
            parameters=parameters)

        self.routes_all[uri] = route
        if properties['unhashable']:
            self.routes_always_check.append(route)
        elif parameters:
            self.routes_dynamic[url_hash(uri)].append(route)
        else:
            self.routes_static[uri] = route

    def get(self, request):
        """
        Gets a request handler based on the URL of the request, or raises an
        error
        :param request: Request object
        :return: handler, arguments, keyword arguments
        """
        return self._get(request.url, request.method)

    @lru_cache(maxsize=Config.ROUTER_CACHE_SIZE)
    def _get(self, url, method):
        """
        Gets a request handler based on the URL of the request, or raises an
        error.  Internal method for caching.
        :param url: Request URL
        :param method: Request method
        :return: handler, arguments, keyword arguments
        """
        # Check against known static routes
        route = self.routes_static.get(url)
        if route:
            match = route.pattern.match(url)
        else:
            # Move on to testing all regex routes
            for route in self.routes_dynamic[url_hash(url)]:
                match = route.pattern.match(url)
                if match:
                    break
            else:
                # Lastly, check against all regex routes that cannot be hashed
                for route in self.routes_always_check:
                    match = route.pattern.match(url)
                    if match:
                        break
                else:
                    raise NotFound('Requested URL {} not found'.format(url))

        if route.methods and method not in route.methods:
            raise InvalidUsage(
                'Method {} not allowed for URL {}'.format(
                    method, url), status_code=405)

        kwargs = {p.name: p.cast(value)
                  for value, p
                  in zip(match.groups(1), route.parameters)}
        return route.handler, [], kwargs
