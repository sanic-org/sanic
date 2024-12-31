from ast import NodeVisitor, Return, parse
from collections.abc import Iterable
from contextlib import suppress
from inspect import getsource, signature
from textwrap import dedent
from typing import (
    Any,
    Callable,
    Optional,
    Union,
    cast,
)

from sanic_routing.route import Route

from sanic.base.meta import SanicMeta
from sanic.constants import HTTP_METHODS
from sanic.errorpages import RESPONSE_MAPPING
from sanic.mixins.base import BaseMixin
from sanic.models.futures import FutureRoute, FutureStatic
from sanic.models.handler_types import RouteHandler
from sanic.types import HashableDict


RouteWrapper = Callable[
    [RouteHandler], Union[RouteHandler, tuple[Route, RouteHandler]]
]


class RouteMixin(BaseMixin, metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_routes: set[FutureRoute] = set()
        self._future_statics: set[FutureStatic] = set()

    def _apply_route(self, route: FutureRoute) -> list[Route]:
        raise NotImplementedError  # noqa

    def route(
        self,
        uri: str,
        methods: Optional[Iterable[str]] = None,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = False,
        apply: bool = True,
        subprotocols: Optional[list[str]] = None,
        websocket: bool = False,
        unquote: bool = False,
        static: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteWrapper:
        """Decorate a function to be registered as a route.

        Args:
            uri (str): Path of the URL.
            methods (Optional[Iterable[str]]): List or tuple of
                methods allowed.
            host (Optional[Union[str, List[str]]]): The host, if required.
            strict_slashes (Optional[bool]): Whether to apply strict slashes
                to the route.
            stream (bool): Whether to allow the request to stream its body.
            version (Optional[Union[int, str, float]]): Route specific
                versioning.
            name (Optional[str]): User-defined route name for url_for.
            ignore_body (bool): Whether the handler should ignore request
                body (e.g. `GET` requests).
            apply (bool): Apply middleware to the route.
            subprotocols (Optional[List[str]]): List of subprotocols.
            websocket (bool): Enable WebSocket support.
            unquote (bool): Unquote special characters in the URL path.
            static (bool): Enable static route.
            version_prefix (str): URL path that should be before the version
                 value; default: `"/v"`.
            error_format (Optional[str]): Error format for the route.
            ctx_kwargs (Any): Keyword arguments that begin with a `ctx_*`
                prefix will be appended to the route context (`route.ctx`).

        Returns:
            RouteWrapper: Tuple of routes, decorated function.

        Examples:
            Using the method to define a GET endpoint:

            ```python
            @app.route("/hello")
            async def hello(request: Request):
                return text("Hello, World!")
            ```

            Adding context kwargs to the route:

            ```python
            @app.route("/greet", ctx_name="World")
            async def greet(request: Request):
                name = request.route.ctx.name
                return text(f"Hello, {name}!")
            ```
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

            name = self.generate_name(name, handler)

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
            overwrite = getattr(self, "_allow_route_overwrite", False)
            if overwrite:
                self._future_routes = set(
                    filter(lambda x: x.uri != uri, self._future_routes)
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
                self._apply_route(route, overwrite=overwrite)

            if static:
                return route, handler
            return handler

        return decorator

    def add_route(
        self,
        handler: RouteHandler,
        uri: str,
        methods: Iterable[str] = frozenset({"GET"}),
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        stream: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        unquote: bool = False,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """A helper method to register class-based view or functions as a handler to the application url routes.

        Args:
            handler (RouteHandler): Function or class-based view used as a route handler.
            uri (str): Path of the URL.
            methods (Iterable[str]): List or tuple of methods allowed; these are overridden if using an HTTPMethodView.
            host (Optional[Union[str, List[str]]]): Hostname or hostnames to match for this route.
            strict_slashes (Optional[bool]): If set, a route's slashes will be strict. E.g. `/foo` will not match `/foo/`.
            version (Optional[Union[int, str, float]]): Version of the API for this route.
            name (Optional[str]): User-defined route name for `url_for`.
            stream (bool): Boolean specifying if the handler is a stream handler.
            version_prefix (str): URL path that should be before the version value; default: ``/v``.
            error_format (Optional[str]): Custom error format string.
            unquote (bool): Boolean specifying if the handler requires unquoting.
            ctx_kwargs (Any): Keyword arguments that begin with a `ctx_*` prefix will be appended to the route context (``route.ctx``). See below for examples.

        Returns:
            RouteHandler: The route handler.

        Examples:
            ```python
            from sanic import Sanic, text

            app = Sanic("test")

            async def handler(request):
                return text("OK")

            app.add_route(handler, "/test", methods=["GET", "POST"])
            ```

            You can use `ctx_kwargs` to add custom context to the route. This
            can often be useful when wanting to add metadata to a route that
            can be used by other parts of the application (like middleware).

            ```python
            from sanic import Sanic, text

            app = Sanic("test")

            async def handler(request):
                return text("OK")

            async def custom_middleware(request):
                if request.route.ctx.monitor:
                    do_some_monitoring()

            app.add_route(handler, "/test", methods=["GET", "POST"], ctx_monitor=True)
            app.register_middleware(custom_middleware)
        """  # noqa: E501
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
            unquote=unquote,
            **ctx_kwargs,
        )(handler)
        return handler

    # Shorthand method decorators
    def get(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **GET** HTTP method.

        Args:
            uri (str): URL to be tagged to GET method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            ignore_body (bool): Whether the handler should ignore request
                body. This means the body of the request, if sent, will not
                be consumed. In that instance, you will see a warning in
                the logs. Defaults to `True`, meaning do not consume the body.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_* prefix` will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def post(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **POST** HTTP method.

        Args:
            uri (str): URL to be tagged to POST method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            stream (bool): Whether or not to stream the request body.
                Defaults to `False`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_*` prefix will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def put(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream: bool = False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **PUT** HTTP method.

        Args:
            uri (str): URL to be tagged to PUT method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            stream (bool): Whether or not to stream the request body.
                Defaults to `False`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_*` prefix will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def head(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **HEAD** HTTP method.

        Args:
            uri (str): URL to be tagged to HEAD method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            ignore_body (bool): Whether the handler should ignore request
                body. This means the body of the request, if sent, will not
                be consumed. In that instance, you will see a warning in
                the logs. Defaults to `True`, meaning do not consume the body.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_*` prefix will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def options(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **OPTIONS** HTTP method.

        Args:
            uri (str): URL to be tagged to OPTIONS method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            ignore_body (bool): Whether the handler should ignore request
                body. This means the body of the request, if sent, will not
                be consumed. In that instance, you will see a warning in
                the logs. Defaults to `True`, meaning do not consume the body.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_*` prefix will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def patch(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        stream=False,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **PATCH** HTTP method.

        Args:
            uri (str): URL to be tagged to PATCH method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for
                the service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a `/`.
            stream (bool): Set to `True` if full request streaming is needed,
                `False` otherwise. Defaults to `False`.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the route.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a
                `ctx_*` prefix will be appended to the route
                context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def delete(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        ignore_body: bool = False,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ) -> RouteHandler:
        """Decorate a function handler to create a route definition using the **DELETE** HTTP method.

        Args:
            uri (str): URL to be tagged to the DELETE method of HTTP.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN for the
                service to use.
            strict_slashes (Optional[bool]): Instruct Sanic to check if the
                request URLs need to terminate with a */*.
            version (Optional[Union[int, str, float]]): API Version.
            name (Optional[str]): Unique name that can be used to identify
                the Route.
            ignore_body (bool): Whether or not to ignore the body in the
                request. Defaults to `False`.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with a `ctx_*`
                prefix will be appended to the route context (`route.ctx`).

        Returns:
            RouteHandler: Object decorated with route method.
        """  # noqa: E501
        return cast(
            RouteHandler,
            self.route(
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
            ),
        )

    def websocket(
        self,
        uri: str,
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        subprotocols: Optional[list[str]] = None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        apply: bool = True,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ):
        """Decorate a function to be registered as a websocket route.

        Args:
            uri (str): Path of the URL.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN details.
            strict_slashes (Optional[bool]): If the API endpoint needs to
                terminate with a `"/"` or not.
            subprotocols (Optional[List[str]]): Optional list of str with
                supported subprotocols.
            version (Optional[Union[int, str, float]]): WebSocket
                protocol version.
            name (Optional[str]): A unique name assigned to the URL so that
                it can be used with url_for.
            apply (bool): If set to False, it doesn't apply the route to the
                app. Default is `True`.
            version_prefix (str): URL path that should be before the version
                value. Defaults to `"/v"`.
            error_format (Optional[str]): Custom error format string.
            **ctx_kwargs (Any): Keyword arguments that begin with
                a `ctx_* prefix` will be appended to the route
                context (`route.ctx`).

        Returns:
            tuple: Tuple of routes, decorated function.
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
        host: Optional[Union[str, list[str]]] = None,
        strict_slashes: Optional[bool] = None,
        subprotocols=None,
        version: Optional[Union[int, str, float]] = None,
        name: Optional[str] = None,
        version_prefix: str = "/v",
        error_format: Optional[str] = None,
        **ctx_kwargs: Any,
    ):
        """A helper method to register a function as a websocket route.

        Args:
            handler (Callable): A callable function or instance of a class
                that can handle the websocket request.
            uri (str): URL path that will be mapped to the websocket handler.
            host (Optional[Union[str, List[str]]]): Host IP or FQDN details.
            strict_slashes (Optional[bool]): If the API endpoint needs to
                terminate with a `"/"` or not.
            subprotocols (Optional[List[str]]): Subprotocols to be used with
                websocket handshake.
            version (Optional[Union[int, str, float]]): Versioning information.
            name (Optional[str]): A unique name assigned to the URL.
            version_prefix (str): URL path before the version value.
                Defaults to `"/v"`.
            error_format (Optional[str]): Format for error handling.
            **ctx_kwargs (Any): Keyword arguments beginning with `ctx_*`
                prefix will be appended to the route context (`route.ctx`).

        Returns:
            Callable: Object passed as the handler.
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

    def _build_route_context(self, raw: dict[str, Any]) -> HashableDict:
        ctx_kwargs = {
            key.replace("ctx_", ""): raw.pop(key)
            for key in {**raw}.keys()
            if key.startswith("ctx_")
        }
        if raw:
            unexpected_arguments = ", ".join(raw.keys())
            raise TypeError(
                f"Unexpected keyword arguments: {unexpected_arguments}"
            )
        return HashableDict(ctx_kwargs)
