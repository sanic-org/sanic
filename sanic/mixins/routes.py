from ast import NodeVisitor, Return, parse
from contextlib import suppress
from functools import partial, wraps
from inspect import getsource, signature
from mimetypes import guess_type
from os import path
from pathlib import Path, PurePath
from textwrap import dedent
from time import gmtime, strftime
from typing import Any, Callable, Iterable, List, Optional, Set, Tuple, Union
from urllib.parse import unquote

from sanic_routing.route import Route  # type: ignore

from sanic.base.meta import SanicMeta
from sanic.compat import stat_async
from sanic.constants import DEFAULT_HTTP_CONTENT_TYPE, HTTP_METHODS
from sanic.errorpages import RESPONSE_MAPPING
from sanic.exceptions import ContentRangeError, FileNotFound, HeaderNotFound
from sanic.handlers import ContentRangeHandler
from sanic.log import deprecation, error_logger
from sanic.models.futures import FutureRoute, FutureStatic
from sanic.models.handler_types import RouteHandler
from sanic.response import HTTPResponse, file, file_stream
from sanic.types import HashableDict


RouteWrapper = Callable[
    [RouteHandler], Union[RouteHandler, Tuple[Route, RouteHandler]]
]
RESTRICTED_ROUTE_CONTEXT = (
    "ignore_body",
    "stream",
    "hosts",
    "static",
    "error_format",
    "websocket",
)


class RouteMixin(metaclass=SanicMeta):
    name: str

    def __init__(self, *args, **kwargs) -> None:
        self._future_routes: Set[FutureRoute] = set()
        self._future_statics: Set[FutureStatic] = set()
        self.strict_slashes: Optional[bool] = False

    def _apply_route(self, route: FutureRoute) -> List[Route]:
        raise NotImplementedError  # noqa

    def _apply_static(self, static: FutureStatic) -> Route:
        raise NotImplementedError  # noqa

    def route(
        self,
        uri: str,
        methods: Optional[Iterable[str]] = None,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = False,
        apply: bool = True,
        subprotocols: Optional[List[str]] = None,
        websocket: bool = False,
        unquote: bool = False,
        static: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteWrapper:
        """
        Decorate a function to be registered as a route


        **Example using context kwargs**

        .. code-block:: python

            @app.route(..., ctx_foo="foobar")
            async def route_handler(request: Request):
                assert request.route.ctx.foo == "foobar"

        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :param host: the host, if required
        :param strict_slashes: whether to apply strict slashes to the route
        :param stream: whether to allow the request to stream its body
        :param version: route specific versioning
        :param name: user defined route name for url_for
        :param ignore_body: whether the handler should ignore request
            body (eg. GET requests)
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
        :return: tuple of routes, decorated function
        """

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith("/") and (uri or hasattr(self, "router")):
            uri = "/" + uri

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        if not methods and not websocket:
            methods = frozenset({"GET"})

        route_context = self._build_route_context(ctx_kwargs)

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
            nonlocal static
            nonlocal version_prefix
            nonlocal error_format

            if isinstance(handler, tuple):
                # if a handler fn is already wrapped in a route, the handler
                # variable will be a tuple of (existing routes, handler fn)
                _, handler = handler

            name = self._generate_name(name, handler)

            if isinstance(host, str):
                host = frozenset([host])
            elif host and not isinstance(host, frozenset):
                try:
                    host = frozenset(host)
                except TypeError:
                    raise ValueError(
                        "Expected either string or Iterable of host strings, "
                        "not %s" % host
                    )
            if isinstance(subprotocols, list):
                # Ordered subprotocols, maintain order
                subprotocols = tuple(subprotocols)
            elif isinstance(subprotocols, set):
                # subprotocol is unordered, keep it unordered
                subprotocols = frozenset(subprotocols)

            if not error_format or error_format == "auto":
                error_format = self._determine_error_format(handler)

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
                unquote,
                static,
                version_prefix,
                error_format,
                route_context,
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

            if static:
                return route, handler
            return handler

        return decorator

    def add_route(
        self,
        handler: RouteHandler,
        uri: str,
        methods: Iterable[str] = frozenset({"GET"}),
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        stream: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteHandler:
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
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, "view_class"):
            methods = set()

            for method in HTTP_METHODS:
                view_class = getattr(handler, "view_class")
                _handler = getattr(view_class, method.lower(), None)
                if _handler:
                    methods.add(method)
                    if hasattr(_handler, "is_stream"):
                        stream = True

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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )(handler)
        return handler

    # Shorthand method decorators
    def get(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **GET** *HTTP* method

        :param uri: URL to be tagged to **GET** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def post(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **POST** *HTTP* method

        :param uri: URL to be tagged to **POST** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def put(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **PUT** *HTTP* method

        :param uri: URL to be tagged to **PUT** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def head(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **HEAD** *HTTP* method

        :param uri: URL to be tagged to **HEAD** method of *HTTP*
        :type uri: str
        :param host: Host IP or FQDN for the service to use
        :type host: Optional[str], optional
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :type strict_slashes: Optional[bool], optional
        :param version: API Version
        :type version: Optional[str], optional
        :param name: Unique name that can be used to identify the Route
        :type name: Optional[str], optional
        :param ignore_body: whether the handler should ignore request
            body (eg. GET requests), defaults to True
        :type ignore_body: bool, optional
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"HEAD"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
            ignore_body=ignore_body,
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def options(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **OPTIONS** *HTTP* method

        :param uri: URL to be tagged to **OPTIONS** method of *HTTP*
        :type uri: str
        :param host: Host IP or FQDN for the service to use
        :type host: Optional[str], optional
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :type strict_slashes: Optional[bool], optional
        :param version: API Version
        :type version: Optional[str], optional
        :param name: Unique name that can be used to identify the Route
        :type name: Optional[str], optional
        :param ignore_body: whether the handler should ignore request
            body (eg. GET requests), defaults to True
        :type ignore_body: bool, optional
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def patch(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream=False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **PATCH** *HTTP* method

        :param uri: URL to be tagged to **PATCH** method of *HTTP*
        :type uri: str
        :param host: Host IP or FQDN for the service to use
        :type host: Optional[str], optional
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :type strict_slashes: Optional[bool], optional
        :param stream: whether to allow the request to stream its body
        :type stream: Optional[bool], optional
        :param version: API Version
        :type version: Optional[str], optional
        :param name: Unique name that can be used to identify the Route
        :type name: Optional[str], optional
        :param ignore_body: whether the handler should ignore request
            body (eg. GET requests), defaults to True
        :type ignore_body: bool, optional
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def delete(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ) -> RouteWrapper:
        """
        Add an API URL under the **DELETE** *HTTP* method

        :param uri: URL to be tagged to **DELETE** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def websocket(
        self,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        subprotocols: Optional[List[str]] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        apply: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
    ):
        """
        Decorate a function to be registered as a websocket route

        :param uri: path of the URL
        :param host: Host IP or FQDN details
        :param strict_slashes: If the API endpoint needs to terminate
                               with a "/" or not
        :param subprotocols: optional list of str with supported subprotocols
        :param name: A unique name assigned to the URL so that it can
                     be used with :func:`url_for`
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
        :return: tuple of routes, decorated function
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
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
        )

    def add_websocket_route(
        self,
        handler,
        uri: str,
        host: Optional[Union[str, List[str]]] = None,
        strict_slashes: Optional[bool] = None,
        subprotocols=None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs,
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
        :param version_prefix: URL path that should be before the version
            value; default: ``/v``
        :param  ctx_kwargs: Keyword arguments that begin with a ctx_* prefix
            will be appended to the route context (``route.ctx``)
        :return: Objected decorated by :func:`websocket`
        """
        return self.websocket(
            uri=uri,
            host=host,
            strict_slashes=strict_slashes,
            subprotocols=subprotocols,
            version=version,
            name=name,
            version_prefix=version_prefix,
            error_format=error_format,
            **ctx_kwargs,
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
        resource_type=None,
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

        name = self._generate_name(name)

        if strict_slashes is None and self.strict_slashes is not None:
            strict_slashes = self.strict_slashes

        if not isinstance(file_or_directory, (str, bytes, PurePath)):
            raise ValueError(
                f"Static route must be a valid path, not {file_or_directory}"
            )

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
            resource_type,
        )
        self._future_statics.add(static)

        if apply:
            self._apply_static(static)

    def _generate_name(self, *objects) -> str:
        name = None

        for obj in objects:
            if obj:
                if isinstance(obj, str):
                    name = obj
                    break

                try:
                    name = obj.name
                except AttributeError:
                    try:
                        name = obj.__name__
                    except AttributeError:
                        continue
                else:
                    break

        if not name:  # noqa
            raise ValueError("Could not generate a name for handler")

        if not name.startswith(f"{self.name}."):
            name = f"{self.name}.{name}"

        return name

    async def _static_request_handler(
        self,
        file_or_directory,
        use_modified_since,
        use_content_range,
        stream_large_files,
        request,
        content_type=None,
        __file_uri__=None,
    ):
        # Merge served directory and requested file if provided
        file_path_raw = Path(unquote(file_or_directory))
        root_path = file_path = file_path_raw.resolve()
        not_found = FileNotFound(
            "File not found",
            path=file_or_directory,
            relative_url=__file_uri__,
        )

        if __file_uri__:
            # Strip all / that in the beginning of the URL to help prevent
            # python from herping a derp and treating the uri as an
            # absolute path
            unquoted_file_uri = unquote(__file_uri__).lstrip("/")
            file_path_raw = Path(file_or_directory, unquoted_file_uri)
            file_path = file_path_raw.resolve()
            if (
                file_path < root_path and not file_path_raw.is_symlink()
            ) or ".." in file_path_raw.parts:
                error_logger.exception(
                    f"File not found: path={file_or_directory}, "
                    f"relative_url={__file_uri__}"
                )
                raise not_found

        try:
            file_path.relative_to(root_path)
        except ValueError:
            if not file_path_raw.is_symlink():
                error_logger.exception(
                    f"File not found: path={file_or_directory}, "
                    f"relative_url={__file_uri__}"
                )
                raise not_found
        try:
            headers = {}
            # Check if the client has been sent this file before
            # and it has not been modified since
            stats = None
            if use_modified_since:
                stats = await stat_async(file_path)
                modified_since = strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", gmtime(stats.st_mtime)
                )
                if (
                    request.headers.getone("if-modified-since", None)
                    == modified_since
                ):
                    return HTTPResponse(status=304)
                headers["Last-Modified"] = modified_since
            _range = None
            if use_content_range:
                _range = None
                if not stats:
                    stats = await stat_async(file_path)
                headers["Accept-Ranges"] = "bytes"
                headers["Content-Length"] = str(stats.st_size)
                if request.method != "HEAD":
                    try:
                        _range = ContentRangeHandler(request, stats)
                    except HeaderNotFound:
                        pass
                    else:
                        del headers["Content-Length"]
                        for key, value in _range.headers.items():
                            headers[key] = value

            if "content-type" not in headers:
                content_type = (
                    content_type
                    or guess_type(file_path)[0]
                    or DEFAULT_HTTP_CONTENT_TYPE
                )

                if "charset=" not in content_type and (
                    content_type.startswith("text/")
                    or content_type == "application/javascript"
                ):
                    content_type += "; charset=utf-8"

                headers["Content-Type"] = content_type

            if request.method == "HEAD":
                return HTTPResponse(headers=headers)
            else:
                if stream_large_files:
                    if type(stream_large_files) == int:
                        threshold = stream_large_files
                    else:
                        threshold = 1024 * 1024

                    if not stats:
                        stats = await stat_async(file_path)
                    if stats.st_size >= threshold:
                        return await file_stream(
                            file_path, headers=headers, _range=_range
                        )
                return await file(file_path, headers=headers, _range=_range)
        except ContentRangeError:
            raise
        except FileNotFoundError:
            raise not_found
        except Exception:
            error_logger.exception(
                f"Exception in static request handler: "
                f"path={file_or_directory}, "
                f"relative_url={__file_uri__}"
            )
            raise

    def _register_static(
        self,
        static: FutureStatic,
    ):
        # TODO: Though sanic is not a file server, I feel like we should
        # at least make a good effort here.  Modified-since is nice, but
        # we could also look into etags, expires, and caching
        """
        Register a static directory handler with Sanic by adding a route to the
        router and registering a handler.

        :param app: Sanic
        :param file_or_directory: File or directory path to serve from
        :type file_or_directory: Union[str,bytes,Path]
        :param uri: URL to serve from
        :type uri: str
        :param pattern: regular expression used to match files in the URL
        :param use_modified_since: If true, send file modified time, and return
                                not modified if the browser's matches the
                                server's
        :param use_content_range: If true, process header for range requests
                                and sends the file part that is requested
        :param stream_large_files: If true, use the file_stream() handler
                                rather than the file() handler to send the file
                                If this is an integer, this represents the
                                threshold size to switch to file_stream()
        :param name: user defined name used for url_for
        :type name: str
        :param content_type: user defined content type for header
        :return: registered static routes
        :rtype: List[sanic.router.Route]
        """

        if isinstance(static.file_or_directory, bytes):
            file_or_directory = static.file_or_directory.decode("utf-8")
        elif isinstance(static.file_or_directory, PurePath):
            file_or_directory = str(static.file_or_directory)
        elif not isinstance(static.file_or_directory, str):
            raise ValueError("Invalid file path string.")
        else:
            file_or_directory = static.file_or_directory

        uri = static.uri
        name = static.name
        # If we're not trying to match a file directly,
        # serve from the folder
        if not static.resource_type:
            if not path.isfile(file_or_directory):
                uri += "/<__file_uri__:path>"
        elif static.resource_type == "dir":
            if path.isfile(file_or_directory):
                raise TypeError(
                    "Resource type improperly identified as directory. "
                    f"'{file_or_directory}'"
                )
            uri += "/<__file_uri__:path>"
        elif static.resource_type == "file" and not path.isfile(
            file_or_directory
        ):
            raise TypeError(
                "Resource type improperly identified as file. "
                f"'{file_or_directory}'"
            )
        elif static.resource_type != "file":
            raise ValueError(
                "The resource_type should be set to 'file' or 'dir'"
            )

        # special prefix for static files
        # if not static.name.startswith("_static_"):
        #     name = f"_static_{static.name}"

        _handler = wraps(self._static_request_handler)(
            partial(
                self._static_request_handler,
                file_or_directory,
                static.use_modified_since,
                static.use_content_range,
                static.stream_large_files,
                content_type=static.content_type,
            )
        )

        route, _ = self.route(  # type: ignore
            uri=uri,
            methods=["GET", "HEAD"],
            name=name,
            host=static.host,
            strict_slashes=static.strict_slashes,
            static=True,
        )(_handler)

        return route

    def _determine_error_format(self, handler) -> str:
        with suppress(OSError, TypeError):
            src = dedent(getsource(handler))
            tree = parse(src)
            http_response_types = self._get_response_types(tree)

            if len(http_response_types) == 1:
                return next(iter(http_response_types))

        return ""

    def _get_response_types(self, node):
        types = set()

        class HttpResponseVisitor(NodeVisitor):
            def visit_Return(self, node: Return) -> Any:
                nonlocal types

                with suppress(AttributeError):
                    if node.value.func.id == "stream":  # type: ignore
                        deprecation(
                            "The sanic.response.stream method has been "
                            "deprecated and will be removed in v22.6. Please "
                            "upgrade your application to use the new style "
                            "streaming pattern. See "
                            "https://sanicframework.org/en/guide/advanced/"
                            "streaming.html#response-streaming for more "
                            "information.",
                            22.6,
                        )
                    checks = [node.value.func.id]  # type: ignore
                    if node.value.keywords:  # type: ignore
                        checks += [
                            k.value
                            for k in node.value.keywords  # type: ignore
                            if k.arg == "content_type"
                        ]

                    for check in checks:
                        if check in RESPONSE_MAPPING:
                            types.add(RESPONSE_MAPPING[check])

        HttpResponseVisitor().visit(node)

        return types

    def _build_route_context(self, raw):
        ctx_kwargs = {
            key.replace("ctx_", ""): raw.pop(key)
            for key in {**raw}.keys()
            if key.startswith("ctx_")
        }
        restricted = [
            key for key in ctx_kwargs.keys() if key in RESTRICTED_ROUTE_CONTEXT
        ]
        if restricted:
            restricted_arguments = ", ".join(restricted)
            raise AttributeError(
                "Cannot use restricted route context: "
                f"{restricted_arguments}. This limitation is only in place "
                "until v22.3 when the restricted names will no longer be in"
                "conflict. See https://github.com/sanic-org/sanic/issues/2303 "
                "for more information."
            )
        if raw:
            unexpected_arguments = ", ".join(raw.keys())
            raise TypeError(
                f"Unexpected keyword arguments: {unexpected_arguments}"
            )
        return HashableDict(ctx_kwargs)
