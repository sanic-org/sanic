from typing import Set

from sanic.base.meta import SanicMeta
from sanic.models.futures import FutureException


class ExceptionMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_exceptions: Set[FutureException] = set()

    def _apply_exception_handler(self, handler: FutureException):
        raise NotImplementedError  # noqa

    def exception(self, *exceptions, apply=True):
        """
        This method enables the process of creating a global exception
        handler for the current blueprint under question.

        :param args: List of Python exceptions to be caught by the handler
        :param kwargs: Additional optional arguments to be passed to the
            exception handler

        :return a decorated method to handle global exceptions for any
            route registered under this blueprint.
        """

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
