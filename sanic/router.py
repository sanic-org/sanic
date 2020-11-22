import re
import uuid

from collections import defaultdict, namedtuple
from collections.abc import Iterable
from functools import lru_cache
from urllib.parse import unquote

from sanic.exceptions import MethodNotSupported, NotFound
from sanic.views import CompositionView


Route = namedtuple(
    "Route",
    [
        "handler",
        "methods",
        "pattern",
        "parameters",
        "name",
        "uri",
        "endpoint",
    ],
)
Parameter = namedtuple("Parameter", ["name", "cast"])

REGEX_TYPES = {
    "string": (str, r"[^/]+"),
    "int": (int, r"-?\d+"),
    "number": (float, r"-?(?:\d+(?:\.\d*)?|\.\d+)"),
    "alpha": (str, r"[A-Za-z]+"),
    "path": (str, r"[^/].*?"),
    "uuid": (
        uuid.UUID,
        r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-"
        r"[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    ),
}

ROUTER_CACHE_SIZE = 1024


def url_hash(url):
    return url.count("/")


class RouteExists(Exception):
    pass


class RouteDoesNotExist(Exception):
    pass


class ParameterNameConflicts(Exception):
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
    parameter_pattern = re.compile(r"<(.+?)>")

    def __init__(self, app):
        self.app = app
        self.routes_all = {}
        self.routes_names = {}
        self.routes_static_files = {}
        self.routes_static = {}
        self.routes_dynamic = defaultdict(list)
        self.routes_always_check = []
        self.hosts = set()

    @classmethod
    def parse_parameter_string(cls, parameter_string):
        """Parse a parameter string into its constituent name, type, and
        pattern

        For example::

            parse_parameter_string('<param_one:[A-z]>')` ->
                ('param_one', str, '[A-z]')

        :param parameter_string: String to parse
        :return: tuple containing
            (parameter_name, parameter_type, parameter_pattern)
        """
        # We could receive NAME or NAME:PATTERN
        name = parameter_string
        pattern = "string"
        if ":" in parameter_string:
            name, pattern = parameter_string.split(":", 1)
            if not name:
                raise ValueError(
                    f"Invalid parameter syntax: {parameter_string}"
                )

        default = (str, pattern)
        # Pull from pre-configured types
        _type, pattern = REGEX_TYPES.get(pattern, default)

        return name, _type, pattern

    def add(
        self,
        uri,
        methods,
        handler,
        host=None,
        strict_slashes=False,
        version=None,
        name=None,
    ):
        """Add a handler to the route list

        :param uri: path to match
        :param methods: sequence of accepted method names. If none are
            provided, any method is allowed
        :param handler: request handler function.
            When executed, it should provide a response object.
        :param strict_slashes: strict to trailing slash
        :param version: current version of the route or blueprint. See
            docs for further details.
        :return: Nothing
        """
        routes = []
        if version is not None:
            version = re.escape(str(version).strip("/").lstrip("v"))
            uri = "/".join([f"/v{version}", uri.lstrip("/")])
        # add regular version
        routes.append(self._add(uri, methods, handler, host, name))

        if strict_slashes:
            return routes

        if not isinstance(host, str) and host is not None:
            # we have gotten back to the top of the recursion tree where the
            # host was originally a list. By now, we've processed the strict
            # slashes logic on the leaf nodes (the individual host strings in
            # the list of host)
            return routes

        # Add versions with and without trailing /
        slashed_methods = self.routes_all.get(uri + "/", frozenset({}))
        unslashed_methods = self.routes_all.get(uri[:-1], frozenset({}))
        if isinstance(methods, Iterable):
            _slash_is_missing = all(
                method in slashed_methods for method in methods
            )
            _without_slash_is_missing = all(
                method in unslashed_methods for method in methods
            )
        else:
            _slash_is_missing = methods in slashed_methods
            _without_slash_is_missing = methods in unslashed_methods

        slash_is_missing = not uri[-1] == "/" and not _slash_is_missing
        without_slash_is_missing = (
            uri[-1] == "/" and not _without_slash_is_missing and not uri == "/"
        )
        # add version with trailing slash
        if slash_is_missing:
            routes.append(self._add(uri + "/", methods, handler, host, name))
        # add version without trailing slash
        elif without_slash_is_missing:
            routes.append(self._add(uri[:-1], methods, handler, host, name))

        return routes

    def _add(self, uri, methods, handler, host=None, name=None):
        """Add a handler to the route list

        :param uri: path to match
        :param methods: sequence of accepted method names. If none are
            provided, any method is allowed
        :param handler: request handler function.
            When executed, it should provide a response object.
        :param name: user defined route name for url_for
        :return: Nothing
        """
        if host is not None:
            if isinstance(host, str):
                uri = host + uri
                self.hosts.add(host)

            else:
                if not isinstance(host, Iterable):
                    raise ValueError(
                        f"Expected either string or Iterable of "
                        f"host strings, not {host!r}"
                    )

                for host_ in host:
                    self.add(uri, methods, handler, host_, name)
                return

        # Dict for faster lookups of if method allowed
        if methods:
            methods = frozenset(methods)

        parameters = []
        parameter_names = set()
        properties = {"unhashable": None}

        def add_parameter(match):
            name = match.group(1)
            name, _type, pattern = self.parse_parameter_string(name)

            if name in parameter_names:
                raise ParameterNameConflicts(
                    f"Multiple parameter named <{name}> " f"in route uri {uri}"
                )
            parameter_names.add(name)

            parameter = Parameter(name=name, cast=_type)
            parameters.append(parameter)

            # Mark the whole route as unhashable if it has the hash key in it
            if re.search(r"(^|[^^]){1}/", pattern):
                properties["unhashable"] = True
            # Mark the route as unhashable if it matches the hash key
            elif re.search(r"/", pattern):
                properties["unhashable"] = True

            return f"({pattern})"

        pattern_string = re.sub(self.parameter_pattern, add_parameter, uri)
        pattern = re.compile(fr"^{pattern_string}$")

        def merge_route(route, methods, handler):
            # merge to the existing route when possible.
            if not route.methods or not methods:
                # method-unspecified routes are not mergeable.
                raise RouteExists(f"Route already registered: {uri}")
            elif route.methods.intersection(methods):
                # already existing method is not overloadable.
                duplicated = methods.intersection(route.methods)
                duplicated_methods = ",".join(list(duplicated))

                raise RouteExists(
                    f"Route already registered: {uri} [{duplicated_methods}]"
                )
            if isinstance(route.handler, CompositionView):
                view = route.handler
            else:
                view = CompositionView()
                view.add(route.methods, route.handler)
            view.add(methods, handler)
            route = route._replace(
                handler=view, methods=methods.union(route.methods)
            )
            return route

        if parameters:
            # TODO: This is too complex, we need to reduce the complexity
            if properties["unhashable"]:
                routes_to_check = self.routes_always_check
                ndx, route = self.check_dynamic_route_exists(
                    pattern, routes_to_check, parameters
                )
            else:
                routes_to_check = self.routes_dynamic[url_hash(uri)]
                ndx, route = self.check_dynamic_route_exists(
                    pattern, routes_to_check, parameters
                )
            if ndx != -1:
                # Pop the ndx of the route, no dups of the same route
                routes_to_check.pop(ndx)
        else:
            route = self.routes_all.get(uri)

        # prefix the handler name with the blueprint name
        # if available
        # special prefix for static files
        is_static = False
        if name and name.startswith("_static_"):
            is_static = True
            name = name.split("_static_", 1)[-1]

        if hasattr(handler, "__blueprintname__"):
            bp_name = handler.__blueprintname__

            handler_name = f"{bp_name}.{name or handler.__name__}"
        else:
            handler_name = name or getattr(
                handler, "__name__", handler.__class__.__name__
            )

        if route:
            route = merge_route(route, methods, handler)
        else:
            endpoint = self.app._build_endpoint_name(handler_name)

            route = Route(
                handler=handler,
                methods=methods,
                pattern=pattern,
                parameters=parameters,
                name=handler_name,
                uri=uri,
                endpoint=endpoint,
            )

        self.routes_all[uri] = route
        if is_static:
            pair = self.routes_static_files.get(handler_name)
            if not (pair and (pair[0] + "/" == uri or uri + "/" == pair[0])):
                self.routes_static_files[handler_name] = (uri, route)

        else:
            pair = self.routes_names.get(handler_name)
            if not (pair and (pair[0] + "/" == uri or uri + "/" == pair[0])):
                self.routes_names[handler_name] = (uri, route)

        if properties["unhashable"]:
            self.routes_always_check.append(route)
        elif parameters:
            self.routes_dynamic[url_hash(uri)].append(route)
        else:
            self.routes_static[uri] = route
        return route

    @staticmethod
    def check_dynamic_route_exists(pattern, routes_to_check, parameters):
        """
        Check if a URL pattern exists in a list of routes provided based on
        the comparison of URL pattern and the parameters.

        :param pattern: URL parameter pattern
        :param routes_to_check: list of dynamic routes either hashable or
            unhashable routes.
        :param parameters: List of :class:`Parameter` items
        :return: Tuple of index and route if matching route exists else
            -1 for index and None for route
        """
        for ndx, route in enumerate(routes_to_check):
            if route.pattern == pattern and route.parameters == parameters:
                return ndx, route
        else:
            return -1, None

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def find_route_by_view_name(self, view_name, name=None):
        """Find a route in the router based on the specified view name.

        :param view_name: string of view name to search by
        :param kwargs: additional params, usually for static files
        :return: tuple containing (uri, Route)
        """
        if not view_name:
            return (None, None)

        if view_name == "static" or view_name.endswith(".static"):
            return self.routes_static_files.get(name, (None, None))

        return self.routes_names.get(view_name, (None, None))

    def get(self, request):
        """Get a request handler based on the URL of the request, or raises an
        error

        :param request: Request object
        :return: handler, arguments, keyword arguments
        """
        # No virtual hosts specified; default behavior
        if not self.hosts:
            return self._get(request.path, request.method, "")
        # virtual hosts specified; try to match route to the host header

        try:
            return self._get(
                request.path, request.method, request.headers.get("Host", "")
            )
        # try default hosts
        except NotFound:
            return self._get(request.path, request.method, "")

    def get_supported_methods(self, url):
        """Get a list of supported methods for a url and optional host.

        :param url: URL string (including host)
        :return: frozenset of supported methods
        """
        route = self.routes_all.get(url)
        # if methods are None then this logic will prevent an error
        return getattr(route, "methods", None) or frozenset()

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def _get(self, url, method, host):
        """Get a request handler based on the URL of the request, or raises an
        error.  Internal method for caching.

        :param url: request URL
        :param method: request method
        :return: handler, arguments, keyword arguments
        """
        url = unquote(host + url)
        # Check against known static routes
        route = self.routes_static.get(url)
        method_not_supported = MethodNotSupported(
            f"Method {method} not allowed for URL {url}",
            method=method,
            allowed_methods=self.get_supported_methods(url),
        )

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
                    raise NotFound(f"Requested URL {url} not found")

        kwargs = {
            p.name: p.cast(value)
            for value, p in zip(match.groups(1), route.parameters)
        }
        route_handler = route.handler
        if hasattr(route_handler, "handlers"):
            route_handler = route_handler.handlers[method]

        return route_handler, [], kwargs, route.uri, route.name, route.endpoint

    def is_stream_handler(self, request):
        """Handler for request is stream or not.
        :param request: Request object
        :return: bool
        """
        try:
            handler = self.get(request)[0]
        except (NotFound, MethodNotSupported):
            return False
        if hasattr(handler, "view_class") and hasattr(
            handler.view_class, request.method.lower()
        ):
            handler = getattr(handler.view_class, request.method.lower())
        return hasattr(handler, "is_stream")
