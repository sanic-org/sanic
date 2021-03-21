from typing import Any, Tuple
from warnings import warn

from sanic.mixins.exceptions import ExceptionMixin
from sanic.mixins.listeners import ListenerMixin
from sanic.mixins.middleware import MiddlewareMixin
from sanic.mixins.routes import RouteMixin
from sanic.mixins.signals import SignalMixin


class BaseSanic(
    RouteMixin,
    MiddlewareMixin,
    ListenerMixin,
    ExceptionMixin,
    SignalMixin,
):
    __fake_slots__: Tuple[str, ...]

    def __init__(self, *args, **kwargs) -> None:
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
                "deprecated and will be removed in version 21.9. You should "
                f"change your {self.__class__.__name__} instance to use "
                f"instance.ctx.{name} instead."
            )
        super().__setattr__(name, value)
