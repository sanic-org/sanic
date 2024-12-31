from __future__ import annotations

import asyncio

from collections import deque
from dataclasses import dataclass
from enum import Enum
from inspect import isawaitable
from typing import Any, Optional, Union, cast

from sanic_routing import BaseRouter, Route, RouteGroup
from sanic_routing.exceptions import NotFound
from sanic_routing.utils import path_to_parts

from sanic.exceptions import InvalidSignal
from sanic.log import error_logger, logger
from sanic.models.handler_types import SignalHandler


class Event(Enum):
    """Event names for the SignalRouter"""

    SERVER_EXCEPTION_REPORT = "server.exception.report"
    SERVER_INIT_AFTER = "server.init.after"
    SERVER_INIT_BEFORE = "server.init.before"
    SERVER_SHUTDOWN_AFTER = "server.shutdown.after"
    SERVER_SHUTDOWN_BEFORE = "server.shutdown.before"
    HTTP_LIFECYCLE_BEGIN = "http.lifecycle.begin"
    HTTP_LIFECYCLE_COMPLETE = "http.lifecycle.complete"
    HTTP_LIFECYCLE_EXCEPTION = "http.lifecycle.exception"
    HTTP_LIFECYCLE_HANDLE = "http.lifecycle.handle"
    HTTP_LIFECYCLE_READ_BODY = "http.lifecycle.read_body"
    HTTP_LIFECYCLE_READ_HEAD = "http.lifecycle.read_head"
    HTTP_LIFECYCLE_REQUEST = "http.lifecycle.request"
    HTTP_LIFECYCLE_RESPONSE = "http.lifecycle.response"
    HTTP_ROUTING_AFTER = "http.routing.after"
    HTTP_ROUTING_BEFORE = "http.routing.before"
    HTTP_HANDLER_AFTER = "http.handler.after"
    HTTP_HANDLER_BEFORE = "http.handler.before"
    HTTP_LIFECYCLE_SEND = "http.lifecycle.send"
    HTTP_MIDDLEWARE_AFTER = "http.middleware.after"
    HTTP_MIDDLEWARE_BEFORE = "http.middleware.before"
    WEBSOCKET_HANDLER_AFTER = "websocket.handler.after"
    WEBSOCKET_HANDLER_BEFORE = "websocket.handler.before"
    WEBSOCKET_HANDLER_EXCEPTION = "websocket.handler.exception"


RESERVED_NAMESPACES = {
    "server": (
        Event.SERVER_EXCEPTION_REPORT.value,
        Event.SERVER_INIT_AFTER.value,
        Event.SERVER_INIT_BEFORE.value,
        Event.SERVER_SHUTDOWN_AFTER.value,
        Event.SERVER_SHUTDOWN_BEFORE.value,
    ),
    "http": (
        Event.HTTP_LIFECYCLE_BEGIN.value,
        Event.HTTP_LIFECYCLE_COMPLETE.value,
        Event.HTTP_LIFECYCLE_EXCEPTION.value,
        Event.HTTP_LIFECYCLE_HANDLE.value,
        Event.HTTP_LIFECYCLE_READ_BODY.value,
        Event.HTTP_LIFECYCLE_READ_HEAD.value,
        Event.HTTP_LIFECYCLE_REQUEST.value,
        Event.HTTP_LIFECYCLE_RESPONSE.value,
        Event.HTTP_ROUTING_AFTER.value,
        Event.HTTP_ROUTING_BEFORE.value,
        Event.HTTP_HANDLER_AFTER.value,
        Event.HTTP_HANDLER_BEFORE.value,
        Event.HTTP_LIFECYCLE_SEND.value,
        Event.HTTP_MIDDLEWARE_AFTER.value,
        Event.HTTP_MIDDLEWARE_BEFORE.value,
    ),
    "websocket": {
        Event.WEBSOCKET_HANDLER_AFTER.value,
        Event.WEBSOCKET_HANDLER_BEFORE.value,
        Event.WEBSOCKET_HANDLER_EXCEPTION.value,
    },
}

GENERIC_SIGNAL_FORMAT = "__generic__.__signal__.%s"


def _blank(): ...


class Signal(Route):
    """A `Route` that is used to dispatch signals to handlers"""


@dataclass
class SignalWaiter:
    """A record representing a future waiting for a signal"""

    signal: Signal
    event_definition: str
    trigger: str = ""
    requirements: Optional[dict[str, str]] = None
    exclusive: bool = True

    future: Optional[asyncio.Future] = None

    async def wait(self):
        """Block until the signal is next dispatched.

        Return the context of the signal dispatch, if any.
        """
        loop = asyncio.get_running_loop()
        self.future = loop.create_future()
        self.signal.ctx.waiters.append(self)
        try:
            return await self.future
        finally:
            self.signal.ctx.waiters.remove(self)

    def matches(self, event, condition):
        return (
            (condition is None and not self.exclusive)
            or (condition is None and not self.requirements)
            or condition == self.requirements
        ) and (self.trigger or event == self.event_definition)


class SignalGroup(RouteGroup):
    """A `RouteGroup` that is used to dispatch signals to handlers"""


class SignalRouter(BaseRouter):
    """A `BaseRouter` that is used to dispatch signals to handlers"""

    def __init__(self) -> None:
        super().__init__(
            delimiter=".",
            route_class=Signal,
            group_class=SignalGroup,
            stacking=True,
        )
        self.allow_fail_builtin = True
        self.ctx.loop = None

    @staticmethod
    def format_event(event: Union[str, Enum]) -> str:
        """Ensure event strings in proper format

        Args:
            event (str): event string

        Returns:
            str: formatted event string
        """
        if isinstance(event, Enum):
            event = str(event.value)
        if "." not in event:
            event = GENERIC_SIGNAL_FORMAT % event
        return event

    def get(  # type: ignore
        self,
        event: Union[str, Enum],
        condition: Optional[dict[str, str]] = None,
    ):
        """Get the handlers for a signal

        Args:
            event (str): The event to get the handlers for
            condition (Optional[Dict[str, str]], optional): A dictionary of conditions to match against the handlers. Defaults to `None`.

        Returns:
            Tuple[SignalGroup, List[SignalHandler], Dict[str, Any]]: A tuple of the `SignalGroup` that matched, a list of the handlers that matched, and a dictionary of the params that matched

        Raises:
            NotFound: If no handlers are found
        """  # noqa: E501
        event = self.format_event(event)
        extra = condition or {}
        try:
            group, param_basket = self.find_route(
                f".{event}",
                self.DEFAULT_METHOD,
                self,
                {"__params__": {}, "__matches__": {}},
                extra=extra,
            )
        except NotFound:
            message = "Could not find signal %s"
            terms: list[Union[str, Optional[dict[str, str]]]] = [event]
            if extra:
                message += " with %s"
                terms.append(extra)
            raise NotFound(message % tuple(terms))

        # Regex routes evaluate and can extract params directly. They are set
        # on param_basket["__params__"]
        params = param_basket["__params__"]
        if not params:
            # If param_basket["__params__"] does not exist, we might have
            # param_basket["__matches__"], which are indexed based matches
            # on path segments. They should already be cast types.
            params = {
                param.name: param_basket["__matches__"][idx]
                for idx, param in group.params.items()
            }

        return group, [route.handler for route in group], params

    async def _dispatch(
        self,
        event: str,
        context: Optional[dict[str, Any]] = None,
        condition: Optional[dict[str, str]] = None,
        fail_not_found: bool = True,
        reverse: bool = False,
    ) -> Any:
        event = self.format_event(event)
        try:
            group, handlers, params = self.get(event, condition=condition)
        except NotFound as e:
            is_reserved = event.split(".", 1)[0] in RESERVED_NAMESPACES
            if fail_not_found and (not is_reserved or self.allow_fail_builtin):
                raise e
            else:
                if self.ctx.app.debug and self.ctx.app.state.verbosity >= 1:
                    error_logger.warning(str(e))
                return None

        if context:
            params.update(context)
        params.pop("__trigger__", None)

        signals = group.routes
        if not reverse:
            signals = signals[::-1]
        try:
            for signal in signals:
                for waiter in signal.ctx.waiters:
                    if waiter.matches(event, condition):
                        waiter.future.set_result(dict(params))

            for signal in signals:
                requirements = signal.extra.requirements
                if (
                    (condition is None and signal.ctx.exclusive is False)
                    or (condition is None and not requirements)
                    or (condition == requirements)
                ) and (signal.ctx.trigger or event == signal.ctx.definition):
                    maybe_coroutine = signal.handler(**params)
                    if isawaitable(maybe_coroutine):
                        retval = await maybe_coroutine
                        if retval:
                            return retval
                    elif maybe_coroutine:
                        return maybe_coroutine
            return None
        except Exception as e:
            if self.ctx.app.debug and self.ctx.app.state.verbosity >= 1:
                error_logger.exception(e)

            if event != Event.SERVER_EXCEPTION_REPORT.value:
                await self.dispatch(
                    Event.SERVER_EXCEPTION_REPORT.value,
                    context={"exception": e},
                )
                setattr(e, "__dispatched__", True)
            raise e

    async def dispatch(
        self,
        event: Union[str, Enum],
        *,
        context: Optional[dict[str, Any]] = None,
        condition: Optional[dict[str, str]] = None,
        fail_not_found: bool = True,
        inline: bool = False,
        reverse: bool = False,
    ) -> Union[asyncio.Task, Any]:
        """Dispatch a signal to all handlers that match the event

        Args:
            event (str): The event to dispatch
            context (Optional[Dict[str, Any]], optional): A dictionary of context to pass to the handlers. Defaults to `None`.
            condition (Optional[Dict[str, str]], optional): A dictionary of conditions to match against the handlers. Defaults to `None`.
            fail_not_found (bool, optional): Whether to raise an exception if no handlers are found. Defaults to `True`.
            inline (bool, optional): Whether to run the handlers inline. An inline run means it will return the value of the signal handler. When `False` (which is the default) the signal handler will run in a background task. Defaults to `False`.
            reverse (bool, optional): Whether to run the handlers in reverse order. Defaults to `False`.

        Returns:
            Union[asyncio.Task, Any]: If `inline` is `True` then the return value of the signal handler will be returned. If `inline` is `False` then an `asyncio.Task` will be returned.

        Raises:
            RuntimeError: If the signal is dispatched outside of an event loop
        """  # noqa: E501

        event = self.format_event(event)
        dispatch = self._dispatch(
            event,
            context=context,
            condition=condition,
            fail_not_found=fail_not_found and inline,
            reverse=reverse,
        )
        logger.debug(f"Dispatching signal: {event}", extra={"verbosity": 1})

        if inline:
            return await dispatch

        task = asyncio.get_running_loop().create_task(dispatch)
        await asyncio.sleep(0)
        return task

    def get_waiter(
        self,
        event: Union[str, Enum],
        condition: Optional[dict[str, Any]] = None,
        exclusive: bool = True,
    ) -> Optional[SignalWaiter]:
        event_definition = self.format_event(event)
        name, trigger, _ = self._get_event_parts(event_definition)
        signal = cast(Signal, self.name_index.get(name))
        if not signal:
            return None

        if event_definition.endswith(".*") and not trigger:
            trigger = "*"
        return SignalWaiter(
            signal=signal,
            event_definition=event_definition,
            trigger=trigger,
            requirements=condition,
            exclusive=bool(exclusive),
        )

    def _get_event_parts(self, event: str) -> tuple[str, str, str]:
        parts = self._build_event_parts(event)
        if parts[2].startswith("<"):
            name = ".".join([*parts[:-1], "*"])
            trigger = self._clean_trigger(parts[2])
        else:
            name = event
            trigger = ""

        if not trigger:
            event = ".".join([*parts[:2], "<__trigger__>"])

        return name, trigger, event

    def add(  # type: ignore
        self,
        handler: SignalHandler,
        event: Union[str, Enum],
        condition: Optional[dict[str, Any]] = None,
        exclusive: bool = True,
        *,
        priority: int = 0,
    ) -> Signal:
        event_definition = self.format_event(event)
        name, trigger, event_string = self._get_event_parts(event_definition)

        signal = super().add(
            event_string,
            handler,
            name=name,
            append=True,
            priority=priority,
        )  # type: ignore

        signal.ctx.exclusive = exclusive
        signal.ctx.trigger = trigger
        signal.ctx.definition = event_definition
        signal.extra.requirements = condition

        return cast(Signal, signal)

    def finalize(self, do_compile: bool = True, do_optimize: bool = False):
        """Finalize the router and compile the routes

        Args:
            do_compile (bool, optional): Whether to compile the routes. Defaults to `True`.
            do_optimize (bool, optional): Whether to optimize the routes. Defaults to `False`.

        Returns:
            SignalRouter: The router

        Raises:
            RuntimeError: If the router is finalized outside of an event loop
        """  # noqa: E501
        self.add(_blank, "sanic.__signal__.__init__")

        try:
            self.ctx.loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("Cannot finalize signals outside of event loop")

        for signal in self.routes:
            signal.ctx.waiters = deque()

        return super().finalize(do_compile=do_compile, do_optimize=do_optimize)

    def _build_event_parts(self, event: str) -> tuple[str, str, str]:
        parts = path_to_parts(event, self.delimiter)
        if (
            len(parts) != 3
            or parts[0].startswith("<")
            or parts[1].startswith("<")
        ):
            raise InvalidSignal("Invalid signal event: %s" % event)

        if (
            parts[0] in RESERVED_NAMESPACES
            and event not in RESERVED_NAMESPACES[parts[0]]
            and not (parts[2].startswith("<") and parts[2].endswith(">"))
        ):
            raise InvalidSignal(
                "Cannot declare reserved signal event: %s" % event
            )
        return parts

    def _clean_trigger(self, trigger: str) -> str:
        trigger = trigger[1:-1]
        if ":" in trigger:
            trigger, _ = trigger.split(":")
        return trigger
