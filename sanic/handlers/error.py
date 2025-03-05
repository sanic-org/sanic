from __future__ import annotations

from typing import Optional

from sanic.errorpages import BaseRenderer, TextRenderer, exception_response
from sanic.exceptions import ServerError
from sanic.log import error_logger
from sanic.models.handler_types import RouteHandler
from sanic.request.types import Request
from sanic.response import text
from sanic.response.types import HTTPResponse


class ErrorHandler:
    """Process and handle all uncaught exceptions.

    This error handling framework is built into the core that can be extended
    by the developers to perform a wide range of tasks from recording the error
    stats to reporting them to an external service that can be used for
    realtime alerting system.

    Args:
        base (BaseRenderer): The renderer to use for the error pages.
    """  # noqa: E501

    def __init__(
        self,
        base: type[BaseRenderer] = TextRenderer,
    ):
        self.cached_handlers: dict[
            tuple[type[BaseException], Optional[str]], Optional[RouteHandler]
        ] = {}
        self.debug = False
        self.base = base

    def _full_lookup(self, exception, route_name: Optional[str] = None):
        return self.lookup(exception, route_name)

    def _add(
        self,
        key: tuple[type[BaseException], Optional[str]],
        handler: RouteHandler,
    ) -> None:
        if key in self.cached_handlers:
            exc, name = key
            if name is None:
                name = "__ALL_ROUTES__"

            message = (
                f"Duplicate exception handler definition on: route={name} "
                f"and exception={exc}"
            )
            raise ServerError(message)
        self.cached_handlers[key] = handler

    def add(self, exception, handler, route_names: Optional[list[str]] = None):
        """Add a new exception handler to an already existing handler object.

        Args:
            exception (sanic.exceptions.SanicException or Exception): Type
                of exception that needs to be handled.
            handler (function): Reference to the function that will
                handle the exception.

        Returns:
            None

        """  # noqa: E501
        if route_names:
            for route in route_names:
                self._add((exception, route), handler)
        else:
            self._add((exception, None), handler)

    def lookup(self, exception, route_name: Optional[str] = None):
        """Lookup the existing instance of `ErrorHandler` and fetch the registered handler for a specific type of exception.

        This method leverages a dict lookup to speedup the retrieval process.

        Args:
            exception (sanic.exceptions.SanicException or Exception): Type
                of exception.

        Returns:
            Registered function if found, ``None`` otherwise.

        """  # noqa: E501
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
                    self.cached_handlers[(exception_class, route_name)] = (
                        handler
                    )
                    return handler

                if ancestor is BaseException:
                    break
        self.cached_handlers[(exception_class, route_name)] = None
        handler = None
        return handler

    _lookup = _full_lookup

    def response(self, request, exception):
        """Fetch and executes an exception handler and returns a response object.

        Args:
            request (sanic.request.Request): Instance of the request.
            exception (sanic.exceptions.SanicException or Exception): Exception to handle.

        Returns:
            Wrap the return value obtained from the `default` function or the registered handler for that type of exception.

        """  # noqa: E501
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
                'Exception raised in exception handler "%s" for uri: %s'
            )
            error_logger.exception(response_message, handler.__name__, url)

            if self.debug:
                return text(response_message % (handler.__name__, url), 500)
            else:
                return text("An error occurred while handling an error", 500)
        return response

    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        """Provide a default behavior for the objects of ErrorHandler.

        If a developer chooses to extend the ErrorHandler, they can
        provide a custom implementation for this method to behave in a way
        they see fit.

        Args:
            request (sanic.request.Request): Incoming request.
            exception (sanic.exceptions.SanicException or Exception): Exception object.

        Returns:
            HTTPResponse: The response object.

        Examples:
            ```python
            class CustomErrorHandler(ErrorHandler):
                def default(self, request: Request, exception: Exception) -> HTTPResponse:
                    # Custom logic for handling the exception and creating a response
                    custom_response = my_custom_logic(request, exception)
                    return custom_response

            app = Sanic("MyApp", error_handler=CustomErrorHandler())
            ```
        """  # noqa: E501
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
    def log(request: Request, exception: Exception) -> None:
        """Logs information about an incoming request and the associated exception.

        Args:
            request (Request): The incoming request to be logged.
            exception (Exception): The exception that occurred during the handling of the request.

        Returns:
            None
        """  # noqa: E501
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
