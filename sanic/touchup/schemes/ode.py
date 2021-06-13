from ast import Attribute, Await, Dict, Expr, parse
from inspect import getsource
from textwrap import dedent
from typing import Any

from sanic.log import logger

from .base import BaseScheme


class OptionalDispatchEvent(BaseScheme):
    ident = "ODE"

    def __init__(self, app) -> None:
        super().__init__(app)

        self._registered_events = [
            signal.path for signal in app.signal_router.routes
        ]

    def run(self, method, module_globals):
        raw_source = getsource(method)
        src = dedent(raw_source)
        tree = parse(src)
        node = self._clean_node(tree)
        compiled_src = compile(node, method.__name__, "exec")
        exec_locals: Dict[str, Any] = {}
        exec(compiled_src, module_globals, exec_locals)

        return exec_locals[method.__name__]

    def _clean_node(self, node):
        if hasattr(node, "body"):
            new_body = []
            for item in node.body:
                new_item = self._clean_node(item)
                if new_item:
                    new_body.append(new_item)
            node.body = new_body
        elif isinstance(node, Expr):
            expr = node.value
            if isinstance(expr, Await):
                expr = expr.value

            if (
                hasattr(expr, "func")
                and isinstance(expr.func, Attribute)
                and expr.func.attr == "dispatch"
            ):
                event = expr.args[0]

                if event.value not in self._registered_events:
                    logger.debug(f"Disabling event: {event.value}")
                    return None
        return node
