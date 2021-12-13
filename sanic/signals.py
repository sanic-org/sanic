from __future__ import annotations

import asyncio

from enum import Enum
from inspect import isawaitable
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from sanic_routing import BaseRouter, Route, RouteGroup  # type: ignore
from sanic_routing.exceptions import NotFound  # type: ignore
from sanic_routing.utils import path_to_parts  # type: ignore

from sanic.exceptions import InvalidSignal
from sanic.log import error_logger, logger
from sanic.models.handler_types import SignalHandler


class Event(Enum):
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
    HTTP_LIFECYCLE_SEND = "http.lifecycle.send"
    HTTP_MIDDLEWARE_AFTER = "http.middleware.after"
    HTTP_MIDDLEWARE_BEFORE = "http.middleware.before"


RESERVED_NAMESPACES = {
    "server": (
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
        Event.HTTP_LIFECYCLE_SEND.value,
        Event.HTTP_MIDDLEWARE_AFTER.value,
        Event.HTTP_MIDDLEWARE_BEFORE.value,
    ),
}


def _blank():
    ...


class Signal(Route):
    ...


class SignalGroup(RouteGroup):
    ...


class SignalRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(
            delimiter=".",
            route_class=Signal,
            group_class=SignalGroup,
            stacking=True,
        )
        self.ctx.loop = None

    def get(  # type: ignore
        self,
        event: str,
        condition: Optional[Dict[str, str]] = None,
    ):
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
            terms: List[Union[str, Optional[Dict[str, str]]]] = [event]
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
        context: Optional[Dict[str, Any]] = None,
        condition: Optional[Dict[str, str]] = None,
        fail_not_found: bool = True,
        reverse: bool = False,
    ) -> Any:
        try:
            group, handlers, params = self.get(event, condition=condition)
        except NotFound as e:
            if fail_not_found:
                raise e
            else:
                if self.ctx.app.debug and self.ctx.app.state.verbosity >= 1:
                    error_logger.warning(str(e))
                return None

        events = [signal.ctx.event for signal in group]
        for signal_event in events:
            signal_event.set()
        if context:
            params.update(context)

        signals = group.routes
        if not reverse:
            signals = signals[::-1]
        try:
            for signal in signals:
                params.pop("__trigger__", None)
                if (
                    (condition is None and signal.ctx.exclusive is False)
                    or (
                        condition is None
                        and not signal.handler.__requirements__
                    )
                    or (condition == signal.handler.__requirements__)
                ) and (signal.ctx.trigger or event == signal.ctx.definition):
                    maybe_coroutine = signal.handler(**params)
                    if isawaitable(maybe_coroutine):
                        retval = await maybe_coroutine
                        if retval:
                            return retval
                    elif maybe_coroutine:
                        return maybe_coroutine
            return None
        finally:
            for signal_event in events:
                signal_event.clear()

    async def dispatch(
        self,
        event: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        condition: Optional[Dict[str, str]] = None,
        fail_not_found: bool = True,
        inline: bool = False,
        reverse: bool = False,
    ) -> Union[asyncio.Task, Any]:
        dispatch = self._dispatch(
            event,
            context=context,
            condition=condition,
            fail_not_found=fail_not_found and inline,
            reverse=reverse,
        )
        logger.debug(f"Dispatching signal: {event}")

        if inline:
            return await dispatch

        task = asyncio.get_running_loop().create_task(dispatch)
        await asyncio.sleep(0)
        return task

    def add(  # type: ignore
        self,
        handler: SignalHandler,
        event: str,
        condition: Optional[Dict[str, Any]] = None,
        exclusive: bool = True,
    ) -> Signal:
        event_definition = event
        parts = self._build_event_parts(event)
        if parts[2].startswith("<"):
            name = ".".join([*parts[:-1], "*"])
            trigger = self._clean_trigger(parts[2])
        else:
            name = event
            trigger = ""

        if not trigger:
            event = ".".join([*parts[:2], "<__trigger__>"])

        handler.__requirements__ = condition  # type: ignore
        handler.__trigger__ = trigger  # type: ignore

        signal = super().add(
            event,
            handler,
            name=name,
            append=True,
        )  # type: ignore

        signal.ctx.exclusive = exclusive
        signal.ctx.trigger = trigger
        signal.ctx.definition = event_definition

        return cast(Signal, signal)

    def finalize(self, do_compile: bool = True, do_optimize: bool = False):
        self.add(_blank, "sanic.__signal__.__init__")

        try:
            self.ctx.loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("Cannot finalize signals outside of event loop")

        for signal in self.routes:
            signal.ctx.event = asyncio.Event()

        return super().finalize(do_compile=do_compile, do_optimize=do_optimize)

    def _build_event_parts(self, event: str) -> Tuple[str, str, str]:
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
