from __future__ import annotations

import asyncio

from inspect import isawaitable

from sanic_routing import BaseRouter, Route  # type: ignore
from sanic_routing.utils import path_to_parts  # type: ignore

from sanic.exceptions import InvalidSignal
from sanic.handlers import SignalHandler


class Signal(Route):
    def get_handler(self, raw_path, method, _):
        method = method or self.router.DEFAULT_METHOD
        raw_path = raw_path.lstrip(self.router.delimiter)
        try:
            return self.handlers[raw_path][method]
        except (IndexError, KeyError):
            raise self.router.method_handler_exception(
                f"Method '{method}' not found on {self}",
                method=method,
                allowed_methods=set(self.methods[raw_path]),
            )


class SignalRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(
            delimiter=".",
            route_class=Signal,
            stacking=True,
        )
        self.ctx.loop = None

    def get(self, event: str, extra=None):  # type: ignore
        return self.resolve(f".{event}", extra=extra)

    async def _dispatch(
        self, event: str, *fields, context=None, where=None
    ) -> None:
        if fields:
            try:
                event = self.delimiter.join([event, *fields])
            except TypeError as e:
                raise TypeError(
                    f"Cannot dispatch with supplied event: {e}."
                    "If you wanted to pass context or where, define them as"
                    "keyword arguments."
                )
        signal, handlers, params = self.get(event, extra=where)

        signal_event = signal.ctx.event
        signal_event.set()
        if context:
            params.update(context)

        try:
            for handler in handlers:
                maybe_coroutine = handler(**params)
                if isawaitable(maybe_coroutine):
                    await maybe_coroutine
        finally:
            signal_event.clear()

    async def dispatch(
        self, event: str, *fields, context=None, where=None
    ) -> None:
        self.ctx.loop.create_task(
            self._dispatch(
                event,
                *fields,
                context=context,
                where=where,
            )
        )
        await asyncio.sleep(0)

    def add(  # type: ignore
        self, handler: SignalHandler, event: str, requirements=None
    ) -> Signal:
        parts = path_to_parts(event, self.delimiter)

        if (
            len(parts) != 3
            or parts[0].startswith("<")
            or parts[1].startswith("<")
        ):
            raise InvalidSignal(f"Invalid signal event: {event}")

        if parts[2].startswith("<"):
            name = ".".join([*parts[:-1], "*"])
        else:
            name = event
        return super().add(
            event,
            handler,
            requirements=requirements,
            name=name,
        )  # type: ignore

    def finalize(self, do_compile: bool = True):
        try:
            self.ctx.loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("Cannot finalize signals outside of event loop")

        for signal in self.routes.values():
            signal.ctx.event = asyncio.Event()

        return super().finalize(do_compile=do_compile)
