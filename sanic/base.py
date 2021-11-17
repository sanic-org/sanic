import re

from typing import Any, Tuple
from warnings import warn

from sanic.exceptions import SanicException
from sanic.mixins.exceptions import ExceptionMixin
from sanic.mixins.listeners import ListenerMixin
from sanic.mixins.middleware import MiddlewareMixin
from sanic.mixins.routes import RouteMixin
from sanic.mixins.signals import SignalMixin


VALID_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]*$")


class BaseSanic(
    RouteMixin,
    MiddlewareMixin,
    ListenerMixin,
    ExceptionMixin,
    SignalMixin,
):
    __fake_slots__: Tuple[str, ...]

    def __init__(self, name: str = None, *args: Any, **kwargs: Any) -> None:
        class_name = self.__class__.__name__

        if name is None:
            raise SanicException(
                f"{class_name} instance cannot be unnamed. "
                "Please use Sanic(name='your_application_name') instead.",
            )

        if not VALID_NAME.match(name):
            warn(
                f"{class_name} instance named '{name}' uses a format that is"
                f"deprecated. Starting in version 21.12, {class_name} objects "
                "must be named only using alphanumeric characters, _, or -.",
                DeprecationWarning,
            )

        self.name = name

        for base in BaseSanic.__bases__:
            base.__init__(self, *args, **kwargs)  # type: ignore

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'

    def __setattr__(self, name: str, value: Any) -> None:
        # This is a temporary compat layer so we can raise a warning until
        # setting attributes on the app instance can be removed and deprecated
        # with a proper implementation of __slots__
        if name not in self.__fake_slots__:
            warn(
                f"Setting variables on {self.__class__.__name__} instances is "
                "deprecated and will be removed in version 21.12. You should "
                f"change your {self.__class__.__name__} instance to use "
                f"instance.ctx.{name} instead.",
                DeprecationWarning,
            )
        super().__setattr__(name, value)
