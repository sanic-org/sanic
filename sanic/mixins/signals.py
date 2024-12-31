from __future__ import annotations

from collections.abc import Coroutine
from enum import Enum
from typing import Any, Callable, Optional, Union

from sanic.base.meta import SanicMeta
from sanic.models.futures import FutureSignal
from sanic.models.handler_types import SignalHandler
from sanic.signals import Event, Signal
from sanic.types import HashableDict


class SignalMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_signals: set[FutureSignal] = set()

    def _apply_signal(self, signal: FutureSignal) -> Signal:
        raise NotImplementedError  # noqa

    def signal(
        self,
        event: Union[str, Enum],
        *,
        apply: bool = True,
        condition: Optional[dict[str, Any]] = None,
        exclusive: bool = True,
        priority: int = 0,
    ) -> Callable[[SignalHandler], SignalHandler]:
        """
        For creating a signal handler, used similar to a route handler:

        .. code-block:: python

            @app.signal("foo.bar.<thing>")
            async def signal_handler(thing, **kwargs):
                print(f"[signal_handler] {thing=}", kwargs)

        :param event: Representation of the event in ``one.two.three`` form
        :type event: str
        :param apply: For lazy evaluation, defaults to ``True``
        :type apply: bool, optional
        :param condition: For use with the ``condition`` argument in dispatch
            filtering, defaults to ``None``
        :param exclusive: When ``True``, the signal can only be dispatched
            when the condition has been met. When ``False``, the signal can
            be dispatched either with or without it. *THIS IS INAPPLICABLE TO
            BLUEPRINT SIGNALS. THEY ARE ALWAYS NON-EXCLUSIVE*, defaults
            to ``True``
        :type condition: Dict[str, Any], optional
        """
        event_value = str(event.value) if isinstance(event, Enum) else event

        def decorator(handler: SignalHandler):
            future_signal = FutureSignal(
                handler,
                event_value,
                HashableDict(condition or {}),
                exclusive,
                priority,
            )
            self._future_signals.add(future_signal)

            if apply:
                self._apply_signal(future_signal)

            return handler

        return decorator

    def add_signal(
        self,
        handler: Optional[Callable[..., Any]],
        event: Union[str, Enum],
        condition: Optional[dict[str, Any]] = None,
        exclusive: bool = True,
    ) -> Callable[..., Any]:
        """Registers a signal handler for a specific event.

        Args:
            handler (Optional[Callable[..., Any]]): The function to be called
                when the event occurs. Defaults to a noop if not provided.
            event (str): The name of the event to listen for.
            condition (Optional[Dict[str, Any]]): Optional condition to filter
                the event triggering. Defaults to `None`.
            exclusive (bool): Whether or not the handler is exclusive. When
                `True`, the signal can only be dispatched when the
                `condition` has been met. *This is inapplicable to blueprint
                signals, which are **ALWAYS** non-exclusive.* Defaults
                to `True`.

        Returns:
            Callable[..., Any]: The handler that was registered.
        """
        if not handler:

            async def noop(**context): ...

            handler = noop
        self.signal(event=event, condition=condition, exclusive=exclusive)(
            handler
        )
        return handler

    def event(self, event: str):
        raise NotImplementedError

    def catch_exception(
        self,
        handler: Callable[[SignalMixin, Exception], Coroutine[Any, Any, None]],
    ) -> None:
        """Register an exception handler for logging or processing.

        This method allows the registration of a custom exception handler to
        catch and process exceptions that occur in the application. Unlike a
        typical exception handler that might modify the response to the client,
        this is intended to capture exceptions for logging or other internal
        processing, such as sending them to an error reporting utility.

        Args:
            handler (Callable): A coroutine function that takes the application
                instance and the exception as arguments. It will be called when
                an exception occurs within the application's lifecycle.

        Example:
            ```python
            app = Sanic("TestApp")

            @app.catch_exception
            async def report_exception(app: Sanic, exception: Exception):
                logging.error(f"An exception occurred: {exception}")

                # Send to an error reporting service
                await error_service.report(exception)

            # Any unhandled exceptions within the application will now be
            # logged and reported to the error service.
            ```
        """  # noqa: E501

        async def signal_handler(exception: Exception):
            await handler(self, exception)

        self.signal(Event.SERVER_EXCEPTION_REPORT)(signal_handler)
