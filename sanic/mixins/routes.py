from functools import partial
from inspect import signature
from pathlib import PurePath
from typing import Set, Union

from sanic_routing.route import Route

from sanic.constants import HTTP_METHODS
from sanic.models.futures import FutureRoute, FutureStatic
from sanic.views import CompositionView


class RouteMixin:
    def __init__(self, *args, **kwargs) -> None:
        self._future_routes: Set[FutureRoute] = set()
        self._future_statics: Set[FutureStatic] = set()
        self.name = ""
        self.strict_slashes = False

    def _apply_route(self, route: FutureRoute) -> Route:
        raise NotImplementedError

    def _apply_static(self, static: FutureStatic) -> Route:
        raise NotImplementedError

    def route(
        self,
        uri,
        methods=None,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
        ignore_body=False,
        apply=True,
        subprotocols=None,
        websocket=False,
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

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith("/"):
            uri = "/" + uri

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        if not methods and not websocket:
            methods = frozenset({"GET"})

        def decorator(handler):
            nonlocal uri
            nonlocal methods
            nonlocal host
            nonlocal strict_slashes
            nonlocal stream
            nonlocal version
            nonlocal name
            nonlocal ignore_body
            nonlocal subprotocols
            nonlocal websocket

            if isinstance(handler, tuple):
                # if a handler fn is already wrapped in a route, the handler
                # variable will be a tuple of (existing routes, handler fn)
                _, handler = handler

            # TODO:
            # - THink this thru.... do we want all routes namespaced?
            # -
            name = self._generate_name(handler, name)

            if isinstance(host, str):
                host = frozenset([host])
            elif host and not isinstance(host, frozenset):
                host = frozenset(host)

            route = FutureRoute(
                handler,
                uri,
                None if websocket else frozenset([x.upper() for x in methods]),
                host,
                strict_slashes,
                stream,
                version,
                name,
                ignore_body,
                websocket,
                subprotocols,
            )

            self._future_routes.add(route)

            args = list(signature(handler).parameters.keys())
            if websocket and len(args) < 2:
                handler_name = handler.__name__

                raise ValueError(
                    f"Required parameter `request` and/or `ws` missing "
                    f"in the {handler_name}() route?"
                )
            elif not args:
                handler_name = handler.__name__

                raise ValueError(
                    f"Required parameter `request` missing "
                    f"in the {handler_name}() route?"
                )

            if not websocket and stream:
                handler.is_stream = stream

            if apply:
                self._apply_route(route)

            return route, handler

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
        """A helper method to register class instance or
        functions as a handler to the application url
        routes.

        :param handler: function or class instance
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed, these are overridden
                        if using a HTTPMethodView
        :param host:
        :param strict_slashes:
        :param version:
        :param name: user defined route name for url_for
        :param stream: boolean specifying if the handler is a stream handler
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, "view_class"):
            methods = set()

            for method in HTTP_METHODS:
                _handler = getattr(handler.view_class, method.lower(), None)
                if _handler:
                    methods.add(method)
                    if hasattr(_handler, "is_stream"):
                        stream = True

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()
            for _handler in handler.handlers.values():
                if hasattr(_handler, "is_stream"):
                    stream = True
                    break

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

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

    # Shorthand method decorators
    def get(
        self,
        uri,
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        ignore_body=True,
    ):
        """
        Add an API URL under the **GET** *HTTP* method

        :param uri: URL to be tagged to **GET** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
            ignore_body=ignore_body,
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
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
        self,
        uri,
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        ignore_body=True,
    ):
        return self.route(
            uri,
            methods=frozenset({"HEAD"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
            ignore_body=ignore_body,
        )

    def options(
        self,
        uri,
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        ignore_body=True,
    ):
        """
        Add an API URL under the **OPTIONS** *HTTP* method

        :param uri: URL to be tagged to **OPTIONS** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
            ignore_body=ignore_body,
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
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
        self,
        uri,
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        ignore_body=True,
    ):
        """
        Add an API URL under the **DELETE** *HTTP* method

        :param uri: URL to be tagged to **DELETE** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
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
            ignore_body=ignore_body,
        )

    def websocket(
        self,
        uri,
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        subprotocols=None,
        apply: bool = True,
    ):
        """Create a blueprint websocket route from a decorated function.

        :param uri: endpoint at which the route will be accessible.
        :param host: IP Address of FQDN for the sanic server to use.
        :param strict_slashes: Enforce the API urls are requested with a
            training */*
        :param version: Blueprint Version
        :param name: Unique name to identify the Websocket Route
        """
        return self.route(
            uri=uri,
            host=host,
            methods=None,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
            apply=apply,
            subprotocols=subprotocols,
            websocket=True,
        )

    def add_websocket_route(
        self,
        handler,
        uri,
        host=None,
        strict_slashes=None,
        subprotocols=None,
        version=None,
        name=None,
    ):
        """
        A helper method to register a function as a websocket route.

        :param handler: a callable function or instance of a class
                        that can handle the websocket request
        :param host: Host IP or FQDN details
        :param uri: URL path that will be mapped to the websocket
                    handler
                    handler
        :param strict_slashes: If the API endpoint needs to terminate
                with a "/" or not
        :param subprotocols: Subprotocols to be used with websocket
                handshake
        :param name: A unique name assigned to the URL so that it can
                be used with :func:`url_for`
        :return: Objected decorated by :func:`websocket`
        """
        return self.websocket(
            uri=uri,
            host=host,
            strict_slashes=strict_slashes,
            subprotocols=subprotocols,
            version=version,
            name=name,
        )(handler)

    def static(
        self,
        uri,
        file_or_directory: Union[str, bytes, PurePath],
        pattern=r"/?.+",
        use_modified_since=True,
        use_content_range=False,
        stream_large_files=False,
        name="static",
        host=None,
        strict_slashes=None,
        content_type=None,
        apply=True,
    ):
        """
        Register a root to serve files from. The input can either be a
        file or a directory. This method will enable an easy and simple way
        to setup the :class:`Route` necessary to serve the static files.

        :param uri: URL path to be used for serving static content
        :param file_or_directory: Path for the Static file/directory with
            static files
        :param pattern: Regex Pattern identifying the valid static files
        :param use_modified_since: If true, send file modified time, and return
            not modified if the browser's matches the server's
        :param use_content_range: If true, process header for range requests
            and sends the file part that is requested
        :param stream_large_files: If true, use the
            :func:`StreamingHTTPResponse.file_stream` handler rather
            than the :func:`HTTPResponse.file` handler to send the file.
            If this is an integer, this represents the threshold size to
            switch to :func:`StreamingHTTPResponse.file_stream`
        :param name: user defined name used for url_for
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param content_type: user defined content type for header
        :return: routes registered on the router
        :rtype: List[sanic.router.Route]
        """

        if not name.startswith(self.name + "."):
            name = f"{self.name}.{name}"

        if strict_slashes is None and self.strict_slashes is not None:
            strict_slashes = self.strict_slashes

        static = FutureStatic(
            uri,
            file_or_directory,
            pattern,
            use_modified_since,
            use_content_range,
            stream_large_files,
            name,
            host,
            strict_slashes,
            content_type,
        )
        self._future_statics.add(static)

        if apply:
            self._apply_static(static)

    def _generate_name(self, handler, name: str) -> str:
        return name or handler.__name__
