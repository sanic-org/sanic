import re
from collections import defaultdict, namedtuple
from functools import lru_cache
from .exceptions import NotFound, InvalidUsage
from .views import CompositionView

Route = namedtuple(
    'Route',
    ['handler', 'methods', 'pattern', 'parameters', 'name'])
Parameter = namedtuple('Parameter', ['name', 'cast'])

REGEX_TYPES = {
    'string': (str, r'[^/]+'),
    'int': (int, r'\d+'),
    'number': (float, r'[0-9\\.]+'),
    'alpha': (str, r'[A-Za-z]+'),
}

ROUTER_CACHE_SIZE = 1024


def url_hash(url):
    return url.count('/')


class RouteExists(Exception):
    pass


class RouteDoesNotExist(Exception):
    pass


class Router:
    """Router supports basic routing with parameters and method checks

    Usage:

    .. code-block:: python

        @sanic.route('/my/url/<my_param>', methods=['GET', 'POST', ...])
        def my_route(request, my_param):
            do stuff...

    or

    .. code-block:: python

        @sanic.route('/my/url/<my_param:my_type>', methods['GET', 'POST', ...])
        def my_route_with_type(request, my_param: my_type):
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
    parameter_pattern = re.compile(r'<(.+?)>')

    def __init__(self):
        self.routes_all = {}
        self.routes_static = {}
        self.routes_dynamic = defaultdict(list)
        self.routes_always_check = []
        self.hosts = None

    def parse_parameter_string(self, parameter_string):
        """Parse a parameter string into its constituent name, type, and
        pattern

        For example:
        `parse_parameter_string('<param_one:[A-z]')` ->
            ('param_one', str, '[A-z]')

        :param parameter_string: String to parse
        :return: tuple containing
            (parameter_name, parameter_type, parameter_pattern)
        """
        # We could receive NAME or NAME:PATTERN
        name = parameter_string
        pattern = 'string'
        if ':' in parameter_string:
            name, pattern = parameter_string.split(':', 1)

        default = (str, pattern)
        # Pull from pre-configured types
        _type, pattern = REGEX_TYPES.get(pattern, default)

        return name, _type, pattern

    def add(self, uri, methods, handler, host=None):
        """Add a handler to the route list

        :param uri: path to match
        :param methods: sequence of accepted method names. If none are
            provided, any method is allowed
        :param handler: request handler function.
            When executed, it should provide a response object.
        :return: Nothing
        """

        if host is not None:
            # we want to track if there are any
            # vhosts on the Router instance so that we can
            # default to the behavior without vhosts
            if self.hosts is None:
                self.hosts = set(host)
            else:
                if isinstance(host, list):
                    host = set(host)
                self.hosts.add(host)
            if isinstance(host, str):
                uri = host + uri
            else:
                for h in host:
                    self.add(uri, methods, handler, h)
                return

        # Dict for faster lookups of if method allowed
        if methods:
            methods = frozenset(methods)

        parameters = []
        properties = {"unhashable": None}

        def add_parameter(match):
            name = match.group(1)
            name, _type, pattern = self.parse_parameter_string(name)

            parameter = Parameter(
                name=name, cast=_type)
            parameters.append(parameter)

            # Mark the whole route as unhashable if it has the hash key in it
            if re.search('(^|[^^]){1}/', pattern):
                properties['unhashable'] = True
            # Mark the route as unhashable if it matches the hash key
            elif re.search(pattern, '/'):
                properties['unhashable'] = True

            return '({})'.format(pattern)

        pattern_string = re.sub(self.parameter_pattern, add_parameter, uri)
        pattern = re.compile(r'^{}$'.format(pattern_string))

        def merge_route(route, methods, handler):
            # merge to the existing route when possible.
            if not route.methods or not methods:
                # method-unspecified routes are not mergeable.
                raise RouteExists(
                    "Route already registered: {}".format(uri))
            elif route.methods.intersection(methods):
                # already existing method is not overloadable.
                duplicated = methods.intersection(route.methods)
                raise RouteExists(
                    "Route already registered: {} [{}]".format(
                        uri, ','.join(list(duplicated))))
            if isinstance(route.handler, CompositionView):
                view = route.handler
            else:
                view = CompositionView()
                view.add(route.methods, route.handler)
            view.add(methods, handler)
            route = route._replace(
                handler=view, methods=methods.union(route.methods))
            return route

        if parameters:
            # TODO: This is too complex, we need to reduce the complexity
            if properties['unhashable']:
                routes_to_check = self.routes_always_check
                ndx, route = self.check_dynamic_route_exists(
                    pattern, routes_to_check)
            else:
                routes_to_check = self.routes_dynamic[url_hash(uri)]
                ndx, route = self.check_dynamic_route_exists(
                    pattern, routes_to_check)
            if ndx != -1:
                # Pop the ndx of the route, no dups of the same route
                routes_to_check.pop(ndx)
        else:
            route = self.routes_all.get(uri)

        if route:
            route = merge_route(route, methods, handler)
        else:
            # prefix the handler name with the blueprint name
            # if available
            if hasattr(handler, '__blueprintname__'):
                handler_name = '{}.{}'.format(
                    handler.__blueprintname__, handler.__name__)
            else:
                handler_name = getattr(handler, '__name__', None)

            route = Route(
                handler=handler, methods=methods, pattern=pattern,
                parameters=parameters, name=handler_name)

        self.routes_all[uri] = route
        if properties['unhashable']:
            self.routes_always_check.append(route)
        elif parameters:
            self.routes_dynamic[url_hash(uri)].append(route)
        else:
            self.routes_static[uri] = route

    @staticmethod
    def check_dynamic_route_exists(pattern, routes_to_check):
        for ndx, route in enumerate(routes_to_check):
            if route.pattern == pattern:
                return ndx, route
        else:
            return -1, None

    def remove(self, uri, clean_cache=True, host=None):
        if host is not None:
            uri = host + uri
        try:
            route = self.routes_all.pop(uri)
        except KeyError:
            raise RouteDoesNotExist("Route was not registered: {}".format(uri))

        if route in self.routes_always_check:
            self.routes_always_check.remove(route)
        elif url_hash(uri) in self.routes_dynamic \
                and route in self.routes_dynamic[url_hash(uri)]:
            self.routes_dynamic[url_hash(uri)].remove(route)
        else:
            self.routes_static.pop(uri)

        if clean_cache:
            self._get.cache_clear()

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def find_route_by_view_name(self, view_name):
        """Find a route in the router based on the specified view name.

        :param view_name: string of view name to search by
        :return: tuple containing (uri, Route)
        """
        if not view_name:
            return (None, None)

        for uri, route in self.routes_all.items():
            if route.name == view_name:
                return uri, route

        return (None, None)

    def get(self, request):
        """Get a request handler based on the URL of the request, or raises an
        error

        :param request: Request object
        :return: handler, arguments, keyword arguments
        """
        if self.hosts is None:
            return self._get(request.url, request.method, '')
        else:
            return self._get(request.url, request.method,
                             request.headers.get("Host", ''))

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def _get(self, url, method, host):
        """Get a request handler based on the URL of the request, or raises an
        error.  Internal method for caching.

        :param url: request URL
        :param method: request method
        :return: handler, arguments, keyword arguments
        """
        url = host + url
        # Check against known static routes
        route = self.routes_static.get(url)
        method_not_supported = InvalidUsage(
            'Method {} not allowed for URL {}'.format(
                method, url), status_code=405)
        if route:
            if route.methods and method not in route.methods:
                raise method_not_supported
            match = route.pattern.match(url)
        else:
            route_found = False
            # Move on to testing all regex routes
            for route in self.routes_dynamic[url_hash(url)]:
                match = route.pattern.match(url)
                route_found |= match is not None
                # Do early method checking
                if match and method in route.methods:
                    break
            else:
                # Lastly, check against all regex routes that cannot be hashed
                for route in self.routes_always_check:
                    match = route.pattern.match(url)
                    route_found |= match is not None
                    # Do early method checking
                    if match and method in route.methods:
                        break
                else:
                    # Route was found but the methods didn't match
                    if route_found:
                        raise method_not_supported
                    raise NotFound('Requested URL {} not found'.format(url))

        kwargs = {p.name: p.cast(value)
                  for value, p
                  in zip(match.groups(1), route.parameters)}
        route_handler = route.handler
        if hasattr(route_handler, 'handlers'):
            route_handler = route_handler.handlers[method]
        return route_handler, [], kwargs
