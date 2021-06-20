from __future__ import annotations

import asyncio

from inspect import isawaitable
from typing import Any, Dict, List, Optional, Tuple, Union

from sanic_routing import BaseRouter, Route, RouteGroup  # type: ignore
from sanic_routing.exceptions import NotFound  # type: ignore
from sanic_routing.utils import path_to_parts  # type: ignore

from sanic.exceptions import InvalidSignal
from sanic.log import logger
from sanic.models.handler_types import SignalHandler


RESERVED_NAMESPACES = {
    "server": (
        # "server.main.start",
        # "server.main.stop",
        "server.init.before",
        "server.init.after",
        "server.shutdown.before",
        "server.shutdown.after",
    ),
    "http": (
        "http.lifecycle.begin",
        "http.lifecycle.complete",
        "http.lifecycle.exception",
        "http.lifecycle.handle",
        "http.lifecycle.read_body",
        "http.lifecycle.read_head",
        "http.lifecycle.request",
        "http.lifecycle.response",
        "http.routing.after",
        "http.routing.before",
        "http.lifecycle.send",
        "http.middleware.after",
        "http.middleware.before",
    ),
}


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
        self.add(lambda: None, "sanic.__signal__.__init__")  # type: ignore

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
                return

        events = [signal.ctx.event for signal in group]
        for signal_event in events:
            signal_event.set()
        if context:
            params.update(context)

        if not reverse:
            handlers = handlers[::-1]
        try:
            for handler in handlers:
                if condition is None or condition == handler.__requirements__:
                    maybe_coroutine = handler(**params)
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
            fail_not_found=fail_not_found,
            reverse=reverse,
        )
        logger.debug(f"Dispatching signal: {event}")
        if inline:
            return await dispatch

        task = self.ctx.loop.create_task(dispatch)
        await asyncio.sleep(0)
        return task

    def add(  # type: ignore
        self,
        handler: SignalHandler,
        event: str,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Signal:
        parts = self._build_event_parts(event)
        if parts[2].startswith("<"):
            name = ".".join([*parts[:-1], "*"])
        else:
            name = event

        handler.__requirements__ = condition  # type: ignore

        return super().add(
            event,
            handler,
            requirements=condition,
            name=name,
            append=True,
        )  # type: ignore

    def finalize(self, do_compile: bool = True, do_optimize: bool = False):
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
