from __future__ import annotations

from inspect import signature
from typing import Dict, List, Optional, Tuple, Type, Union

from sanic.config import Config
from sanic.errorpages import (
    DEFAULT_FORMAT,
    BaseRenderer,
    HTMLRenderer,
    exception_response,
)
from sanic.exceptions import (
    ContentRangeError,
    HeaderNotFound,
    InvalidRangeType,
    SanicException,
)
from sanic.helpers import Default, _default
from sanic.log import deprecation, error_logger
from sanic.models.handler_types import RouteHandler
from sanic.response import text


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

    # Beginning in v22.3, the base renderer will be TextRenderer
    def __init__(
        self,
        fallback: Union[str, Default] = _default,
        base: Type[BaseRenderer] = HTMLRenderer,
    ):
        self.handlers: List[Tuple[Type[BaseException], RouteHandler]] = []
        self.cached_handlers: Dict[
            Tuple[Type[BaseException], Optional[str]], Optional[RouteHandler]
        ] = {}
        self.debug = False
        self._fallback = fallback
        self.base = base

        if fallback is not _default:
            self._warn_fallback_deprecation()

    @property
    def fallback(self):
        # This is for backwards compat and can be removed in v22.6
        if self._fallback is _default:
            return DEFAULT_FORMAT
        return self._fallback

    @fallback.setter
    def fallback(self, value: str):
        self._warn_fallback_deprecation()
        if not isinstance(value, str):
            raise SanicException(
                f"Cannot set error handler fallback to: value={value}"
            )
        self._fallback = value

    @staticmethod
    def _warn_fallback_deprecation():
        deprecation(
            "Setting the ErrorHandler fallback value directly is "
            "deprecated and no longer supported. This feature will "
            "be removed in v22.6. Instead, use "
            "app.config.FALLBACK_ERROR_FORMAT.",
            22.6,
        )

    @classmethod
    def _get_fallback_value(cls, error_handler: ErrorHandler, config: Config):
        if error_handler._fallback is not _default:
            if config._FALLBACK_ERROR_FORMAT is _default:
                return error_handler.fallback

            error_logger.warning(
                "Conflicting error fallback values were found in the "
                "error handler and in the app.config while handling an "
                "exception. Using the value from app.config."
            )
        return config.FALLBACK_ERROR_FORMAT

    @classmethod
    def finalize(
        cls,
        error_handler: ErrorHandler,
        fallback: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        if fallback:
            deprecation(
                "Setting the ErrorHandler fallback value via finalize() "
                "is deprecated and no longer supported. This feature will "
                "be removed in v22.6. Instead, use "
                "app.config.FALLBACK_ERROR_FORMAT.",
                22.6,
            )

        if config is None:
            deprecation(
                "Starting in v22.3, config will be a required argument "
                "for ErrorHandler.finalize().",
                22.3,
            )

        if fallback and fallback != DEFAULT_FORMAT:
            if error_handler._fallback is not _default:
                error_logger.warning(
                    f"Setting the fallback value to {fallback}. This changes "
                    "the current non-default value "
                    f"'{error_handler._fallback}'."
                )
            error_handler._fallback = fallback

        if not isinstance(error_handler, cls):
            error_logger.warning(
                f"Error handler is non-conforming: {type(error_handler)}"
            )

        sig = signature(error_handler.lookup)
        if len(sig.parameters) == 1:
            deprecation(
                "You are using a deprecated error handler. The lookup "
                "method should accept two positional parameters: "
                "(exception, route_name: Optional[str]). "
                "Until you upgrade your ErrorHandler.lookup, Blueprint "
                "specific exceptions will not work properly. Beginning "
                "in v22.3, the legacy style lookup method will not "
                "work at all.",
                22.3,
            )
            legacy_lookup = error_handler._legacy_lookup
            error_handler._lookup = legacy_lookup  # type: ignore

    def _full_lookup(self, exception, route_name: Optional[str] = None):
        return self.lookup(exception, route_name)

    def _legacy_lookup(self, exception, route_name: Optional[str] = None):
        return self.lookup(exception)

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
        # self.handlers is deprecated and will be removed in version 22.3
        self.handlers.append((exception, handler))

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
            except AttributeError:
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
        fallback = ErrorHandler._get_fallback_value(self, request.app.config)
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
            except AttributeError:
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
            raise ContentRangeError(
                "'%s' is invalid for Content Range" % (start_b,), self
            )
        try:
            self.end = int(end_b) if end_b else None
        except ValueError:
            raise ContentRangeError(
                "'%s' is invalid for Content Range" % (end_b,), self
            )
        if self.end is None:
            if self.start is None:
                raise ContentRangeError(
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
            raise ContentRangeError(
                "Invalid for Content Range parameters", self
            )
        self.size = self.end - self.start + 1
        self.headers = {
            "Content-Range": "bytes %s-%s/%s"
            % (self.start, self.end, self.total)
        }

    def __bool__(self):
        return self.size > 0
