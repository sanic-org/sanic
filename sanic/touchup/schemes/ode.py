from ast import Attribute, Await, Expr, NodeTransformer
from typing import Any, List

from sanic.log import logger

from .base import BaseScheme


class OptionalDispatchEvent(BaseScheme):
    ident = "ODE"
    SYNC_SIGNAL_NAMESPACES = "http."

    def __init__(self, app) -> None:
        super().__init__(app)

        self._sync_events()
        self._registered_events = [
            signal.name for signal in app.signal_router.routes
        ]

    def visitors(self) -> List[NodeTransformer]:
        return [RemoveDispatch(self._registered_events)]

    def _sync_events(self):
        all_events = set()
        app_events = {}
        for app in self.app.__class__._app_registry.values():
            if app.state.server_info:
                app_events[app] = {
                    signal.name for signal in app.signal_router.routes
                }
                all_events.update(app_events[app])

        for app, events in app_events.items():
            missing = {
                x
                for x in all_events.difference(events)
                if any(x.startswith(y) for y in self.SYNC_SIGNAL_NAMESPACES)
            }
            if missing:
                was_finalized = app.signal_router.finalized
                if was_finalized:  # no cov
                    app.signal_router.reset()
                for event in missing:
                    app.signal(event)(self.noop)
                if was_finalized:  # no cov
                    app.signal_router.finalize()

    @staticmethod
    async def noop(**_):  # no cov
        ...


class RemoveDispatch(NodeTransformer):
    def __init__(self, registered_events) -> None:
        self._registered_events = registered_events

    def visit_Expr(self, node: Expr) -> Any:
        call = node.value
        if isinstance(call, Await):
            call = call.value

        func = getattr(call, "func", None)
        args = getattr(call, "args", None)
        if not func or not args:
            return node

        if isinstance(func, Attribute) and func.attr == "dispatch":
            event = args[0]
            if hasattr(event, "s"):
                event_name = getattr(event, "value", event.s)
                if self._not_registered(event_name):
                    logger.debug(
                        f"Disabling event: {event_name}",
                        extra={"verbosity": 2},
                    )
                    return None
        return node

    def _not_registered(self, event_name):
        dynamic = []
        for event in self._registered_events:
            if event.endswith(">"):
                namespace_concern, _ = event.rsplit(".", 1)
                dynamic.append(namespace_concern)

        namespace_concern, _ = event_name.rsplit(".", 1)
        return (
            event_name not in self._registered_events
            and namespace_concern not in dynamic
        )
