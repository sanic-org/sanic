from typing import Any, Callable, List, Set, Type, Union

from sanic.base.meta import SanicMeta
from sanic.models.futures import FutureException


class ExceptionMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_exceptions: Set[FutureException] = set()

    def _apply_exception_handler(self, handler: FutureException):
        raise NotImplementedError  # noqa

    def exception(
        self,
        *exceptions: Union[Type[Exception], List[Type[Exception]]],
        apply: bool = True,
    ) -> Callable:
        """Decorator used to register an exception handler for the current application or blueprint instance.

        This method allows you to define a handler for specific exceptions that
        may be raised within the routes of this blueprint. You can specify one
        or more exception types to catch, and the handler will be applied to
        those exceptions.

        When used on a Blueprint, the handler will only be applied to routes
        registered under that blueprint. That means they only apply to
        requests that have been matched, and the exception is raised within
        the handler function (or middleware) for that route.

        A general exception like `NotFound` should only be registered on the
        application instance, not on a blueprint.

        See [Exceptions](/en/guide/best-practices/exceptions.html) for more information.

        Args:
            exceptions (Union[Type[Exception], List[Type[Exception]]]): List of
                Python exceptions to be caught by the handler.
            apply (bool, optional): Whether the exception handler should be
                applied. Defaults to True.

        Returns:
            Callable: A decorated method to handle global exceptions for any route
                registered under this blueprint.

        Example:
            ```python
            from sanic import Blueprint, text

            bp = Blueprint('my_blueprint')

            @bp.exception(Exception)
            def handle_exception(request, exception):
                return text("Oops, something went wrong!", status=500)
            ```

            ```python
            from sanic import Sanic, NotFound, text

            app = Sanic('MyApp')

            @app.exception(NotFound)
            def ignore_404s(request, exception):
                return text(f"Yep, I totally found the page: {request.url}")
        """  # noqa: E501

        def decorator(handler):
            nonlocal apply
            nonlocal exceptions

            if isinstance(exceptions[0], list):
                exceptions = tuple(*exceptions)

            future_exception = FutureException(handler, exceptions)
            self._future_exceptions.add(future_exception)
            if apply:
                self._apply_exception_handler(future_exception)
            return handler

        return decorator

    def all_exceptions(
        self, handler: Callable[..., Any]
    ) -> Callable[..., Any]:
        """Enables the process of creating a global exception handler as a convenience.

        This following two examples are equivalent:

        ```python
        @app.exception(Exception)
        async def handler(request: Request, exception: Exception) -> HTTPResponse:
            return text(f"Exception raised: {exception}")
        ```

        ```python
        @app.all_exceptions
        async def handler(request: Request, exception: Exception) -> HTTPResponse:
            return text(f"Exception raised: {exception}")
        ```

        Args:
            handler (Callable[..., Any]): A coroutine function to handle exceptions.

        Returns:
            Callable[..., Any]: A decorated method to handle global exceptions for
                any route registered under this blueprint.
        """  # noqa: E501
        return self.exception(Exception)(handler)
