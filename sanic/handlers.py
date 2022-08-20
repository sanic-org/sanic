from __future__ import annotations

from functools import partial
from inspect import isawaitable
from traceback import format_exc
from typing import Dict, List, Optional, Tuple, Type

from sanic_routing import Route

from sanic.errorpages import BaseRenderer, TextRenderer, exception_response
from sanic.exceptions import (
    HeaderNotFound,
    InvalidRangeType,
    RangeNotSatisfiable,
    SanicException,
    ServerError,
)
from sanic.http.constants import Stage
from sanic.log import deprecation, error_logger, logger
from sanic.models.handler_types import RouteHandler
from sanic.request import Request
from sanic.response import BaseHTTPResponse, HTTPResponse, ResponseStream, text


class RequestHandler:
    def __init__(self, func, request_middleware, response_middleware):
        self.func = func
        self.request_middleware = request_middleware
        self.response_middleware = response_middleware

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class RequestManager:
    request: Request

    def __init__(self, request: Request):
        self.request_middleware_run = False
        self.response_middleware_run = False
        self.handler = self._noop
        self.set_request(request)

    @classmethod
    def create(cls, request: Request) -> RequestManager:
        return cls(request)

    def set_request(self, request: Request):
        request._manager = self
        self.request = request
        self.request_middleware = request.app.request_middleware
        self.response_middleware = request.app.response_middleware

    async def handle(self):
        route = self.resolve_route()

        if self.handler is None:
            await self.error(
                ServerError(
                    (
                        "'None' was returned while requesting a "
                        "handler from the router"
                    )
                )
            )
            return

        if (
            self.request.stream
            and self.request.stream.request_body
            and not route.ctx.ignore_body
        ):
            await self.receive_body()

        await self.lifecycle(
            partial(self.handler, self.request, **self.request.match_info)
        )

    async def lifecycle(self, handler):
        response: Optional[BaseHTTPResponse] = None
        if not self.request_middleware_run and self.request_middleware:
            response = await self.run(self.run_request_middleware)

        if not response:
            # Run response handler
            response = await self.run(handler)

        if not self.response_middleware_run and self.response_middleware:
            response = await self.run(
                partial(self.run_response_middleware, response)
            )

        await self.cleanup(response)

    async def run(self, operation) -> Optional[BaseHTTPResponse]:
        try:
            response = operation()
            if isawaitable(response):
                response = await response
        except Exception as e:
            response = await self.error(e)
        return response

    async def error(self, exception: Exception):
        error_handler = self.request.app.error_handler
        if (
            self.request.stream is not None
            and self.request.stream.stage is not Stage.HANDLER
        ):
            error_logger.exception(exception, exc_info=True)
            logger.error(
                "The error response will not be sent to the client for "
                f'the following exception:"{exception}". A previous response '
                "has at least partially been sent."
            )

            handler = error_handler._lookup(
                exception, self.request.name if self.request else None
            )
            if handler:
                logger.warning(
                    "An error occurred while handling the request after at "
                    "least some part of the response was sent to the client. "
                    "The response from your custom exception handler "
                    f"{handler.__name__} will not be sent to the client."
                    "Exception handlers should only be used to generate the "
                    "exception responses. If you would like to perform any "
                    "other action on a raised exception, consider using a "
                    "signal handler like "
                    '`@app.signal("http.lifecycle.exception")`\n'
                    "For further information, please see the docs: "
                    "https://sanicframework.org/en/guide/advanced/"
                    "signals.html",
                )
            return

        try:
            await self.lifecycle(
                partial(error_handler.response, self.request, exception)
            )
        except Exception as e:
            await self.lifecycle(
                partial(error_handler.default, self.request, e)
            )
            if isinstance(e, SanicException):
                response = error_handler.default(self.request, e)
            elif self.request.app.debug:
                response = HTTPResponse(
                    (
                        f"Error while handling error: {e}\n"
                        f"Stack: {format_exc()}"
                    ),
                    status=500,
                )
            else:
                response = HTTPResponse(
                    "An error occurred while handling an error", status=500
                )
            return response
        return None

    async def cleanup(self, response: Optional[BaseHTTPResponse]):
        if self.request.responded:
            if response is not None:
                error_logger.error(
                    "The response object returned by the route handler "
                    "will not be sent to client. The request has already "
                    "been responded to."
                )
            if self.request.stream is not None:
                response = self.request.stream.response
        elif response is not None:
            self.request.reset_response()
            response = await self.request.respond(response)  # type: ignore
        elif not hasattr(self.handler, "is_websocket"):
            response = self.request.stream.response  # type: ignore

        # Marked for cleanup and DRY with handle_request/handle_exception
        # when ResponseStream is no longer supporder
        if isinstance(response, BaseHTTPResponse):
            # await self.dispatch(
            #     "http.lifecycle.response",
            #     inline=True,
            #     context={
            #         "request": self.request,
            #         "response": response,
            #     },
            # )
            ...
            await response.send(end_stream=True)
        elif isinstance(response, ResponseStream):
            await response(self.request)  # type: ignore
            # await self.dispatch(
            #     "http.lifecycle.response",
            #     inline=True,
            #     context={
            #         "request": self.request,
            #         "response": resp,
            #     },
            # )
            await response.eof()  # type: ignore
        else:
            if not hasattr(self.handler, "is_websocket"):
                raise ServerError(
                    f"Invalid response type {response!r} "
                    "(need HTTPResponse)"
                )

    async def receive_body(self):
        if hasattr(self.handler, "is_stream"):
            # Streaming handler: lift the size limit
            self.request.stream.request_max_size = float("inf")
        else:
            # Non-streaming handler: preload body
            await self.request.receive_body()

    async def run_request_middleware(self) -> Optional[BaseHTTPResponse]:
        self.request._request_middleware_started = True
        self.request_middleware_run = True

        for middleware in self.request_middleware:
            # await self.dispatch(
            #     "http.middleware.before",
            #     inline=True,
            #     context={
            #         "request": request,
            #         "response": None,
            #     },
            #     condition={"attach_to": "request"},
            # )

            response = await self.run(partial(middleware, self.request))

            # await self.dispatch(
            #     "http.middleware.after",
            #     inline=True,
            #     context={
            #         "request": request,
            #         "response": None,
            #     },
            #     condition={"attach_to": "request"},
            # )

            if response:
                return response
        return None

    async def run_response_middleware(
        self, response: BaseHTTPResponse
    ) -> BaseHTTPResponse:
        self.response_middleware_run = True
        for middleware in self.response_middleware:
            # await self.dispatch(
            #     "http.middleware.before",
            #     inline=True,
            #     context={
            #         "request": request,
            #         "response": None,
            #     },
            #     condition={"attach_to": "request"},
            # )

            resp = await self.run(partial(middleware, self.request, response))

            # await self.dispatch(
            #     "http.middleware.after",
            #     inline=True,
            #     context={
            #         "request": request,
            #         "response": None,
            #     },
            #     condition={"attach_to": "request"},
            # )

            if resp:
                return resp
        return response
        # try:
        #     middleware = (
        #         self.route and self.route.extra.response_middleware
        #     ) or self.app.response_middleware
        #     if middleware:
        #         response = await self.app._run_response_middleware(
        #             self, response, middleware
        #         )
        # except CancelledErrors:
        #     raise
        # except Exception:
        #     error_logger.exception(
        #         "Exception occurred in one of response middleware handlers"
        #     )
        # return None

    def resolve_route(self) -> Route:
        # Fetch handler from router
        route, handler, kwargs = self.request.app.router.get(
            self.request.path,
            self.request.method,
            self.request.headers.getone("host", None),
        )

        self.request._match_info = {**kwargs}
        self.request.route = route
        self.handler = handler

        if route.handler and route.handler.request_middleware:
            self.request_middleware = route.handler.request_middleware

        if route.handler and route.handler.response_middleware:
            self.response_middleware = route.handler.response_middleware

        return route

    @staticmethod
    def _noop(_):
        ...


class ErrorHandler:
    """
    Provide :class:`sanic.app.Sanic` application with a mechanism to handle
    and process any and all uncaught exceptions in a way the application
    developer will set fit.

    This error handling framework is built into the core that can be extended
    by the developers to perform a wide range of tasks from recording the error
    stats to reporting them to an external service that can be used for
    realtime alerting system.

    """

    def __init__(
        self,
        base: Type[BaseRenderer] = TextRenderer,
    ):
        self.cached_handlers: Dict[
            Tuple[Type[BaseException], Optional[str]], Optional[RouteHandler]
        ] = {}
        self.debug = False
        self.base = base

    @classmethod
    def finalize(cls, *args, **kwargs):
        deprecation(
            "ErrorHandler.finalize is deprecated and no longer needed. "
            "Please remove update your code to remove it. ",
            22.12,
        )

    def _full_lookup(self, exception, route_name: Optional[str] = None):
        return self.lookup(exception, route_name)

    def add(self, exception, handler, route_names: Optional[List[str]] = None):
        """
        Add a new exception handler to an already existing handler object.

        :param exception: Type of exception that need to be handled
        :param handler: Reference to the method that will handle the exception

        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`
        :type handler: ``function``

        :return: None
        """
        if route_names:
            for route in route_names:
                self.cached_handlers[(exception, route)] = handler
        else:
            self.cached_handlers[(exception, None)] = handler

    def lookup(self, exception, route_name: Optional[str] = None):
        """
        Lookup the existing instance of :class:`ErrorHandler` and fetch the
        registered handler for a specific type of exception.

        This method leverages a dict lookup to speedup the retrieval process.

        :param exception: Type of exception

        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`

        :return: Registered function if found ``None`` otherwise
        """
        exception_class = type(exception)

        for name in (route_name, None):
            exception_key = (exception_class, name)
            handler = self.cached_handlers.get(exception_key)
            if handler:
                return handler

        for name in (route_name, None):
            for ancestor in type.mro(exception_class):
                exception_key = (ancestor, name)
                if exception_key in self.cached_handlers:
                    handler = self.cached_handlers[exception_key]
                    self.cached_handlers[
                        (exception_class, route_name)
                    ] = handler
                    return handler

                if ancestor is BaseException:
                    break
        self.cached_handlers[(exception_class, route_name)] = None
        handler = None
        return handler

    _lookup = _full_lookup

    def response(self, request, exception):
        """Fetches and executes an exception handler and returns a response
        object

        :param request: Instance of :class:`sanic.request.Request`
        :param exception: Exception to handle

        :type request: :class:`sanic.request.Request`
        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`

        :return: Wrap the return value obtained from :func:`default`
            or registered handler for that type of exception.
        """
        route_name = request.name if request else None
        handler = self._lookup(exception, route_name)
        response = None
        try:
            if handler:
                response = handler(request, exception)
            if response is None:
                response = self.default(request, exception)
        except Exception:
            try:
                url = repr(request.url)
            except AttributeError:  # no cov
                url = "unknown"
            response_message = (
                "Exception raised in exception handler " '"%s" for uri: %s'
            )
            error_logger.exception(response_message, handler.__name__, url)

            if self.debug:
                return text(response_message % (handler.__name__, url), 500)
            else:
                return text("An error occurred while handling an error", 500)
        return response

    def default(self, request, exception):
        """
        Provide a default behavior for the objects of :class:`ErrorHandler`.
        If a developer chooses to extent the :class:`ErrorHandler` they can
        provide a custom implementation for this method to behave in a way
        they see fit.

        :param request: Incoming request
        :param exception: Exception object

        :type request: :class:`sanic.request.Request`
        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`
        :return:
        """
        self.log(request, exception)
        fallback = request.app.config.FALLBACK_ERROR_FORMAT
        return exception_response(
            request,
            exception,
            debug=self.debug,
            base=self.base,
            fallback=fallback,
        )

    @staticmethod
    def log(request, exception):
        quiet = getattr(exception, "quiet", False)
        noisy = getattr(request.app.config, "NOISY_EXCEPTIONS", False)
        if quiet is False or noisy is True:
            try:
                url = repr(request.url)
            except AttributeError:  # no cov
                url = "unknown"

            error_logger.exception(
                "Exception occurred while handling uri: %s", url
            )


class ContentRangeHandler:
    """
    A mechanism to parse and process the incoming request headers to
    extract the content range information.

    :param request: Incoming api request
    :param stats: Stats related to the content

    :type request: :class:`sanic.request.Request`
    :type stats: :class:`posix.stat_result`

    :ivar start: Content Range start
    :ivar end: Content Range end
    :ivar size: Length of the content
    :ivar total: Total size identified by the :class:`posix.stat_result`
        instance
    :ivar ContentRangeHandler.headers: Content range header ``dict``
    """

    __slots__ = ("start", "end", "size", "total", "headers")

    def __init__(self, request, stats):
        self.total = stats.st_size
        _range = request.headers.getone("range", None)
        if _range is None:
            raise HeaderNotFound("Range Header Not Found")
        unit, _, value = tuple(map(str.strip, _range.partition("=")))
        if unit != "bytes":
            raise InvalidRangeType(
                "%s is not a valid Range Type" % (unit,), self
            )
        start_b, _, end_b = tuple(map(str.strip, value.partition("-")))
        try:
            self.start = int(start_b) if start_b else None
        except ValueError:
            raise RangeNotSatisfiable(
                "'%s' is invalid for Content Range" % (start_b,), self
            )
        try:
            self.end = int(end_b) if end_b else None
        except ValueError:
            raise RangeNotSatisfiable(
                "'%s' is invalid for Content Range" % (end_b,), self
            )
        if self.end is None:
            if self.start is None:
                raise RangeNotSatisfiable(
                    "Invalid for Content Range parameters", self
                )
            else:
                # this case represents `Content-Range: bytes 5-`
                self.end = self.total - 1
        else:
            if self.start is None:
                # this case represents `Content-Range: bytes -5`
                self.start = self.total - self.end
                self.end = self.total - 1
        if self.start >= self.end:
            raise RangeNotSatisfiable(
                "Invalid for Content Range parameters", self
            )
        self.size = self.end - self.start + 1
        self.headers = {
            "Content-Range": "bytes %s-%s/%s"
            % (self.start, self.end, self.total)
        }

    def __bool__(self):
        return self.size > 0
