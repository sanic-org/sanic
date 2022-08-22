from __future__ import annotations

import os
import sys

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional


if TYPE_CHECKING:
    from sanic import Sanic as SanicApp


class AppLoader:
    def __init__(
        self,
        module_input: str = "",
        as_factory: bool = False,
        as_simple: bool = False,
        args: Any = None,
        factory: Optional[Callable[[], SanicApp]] = None,
    ) -> None:
        self.module_input = module_input
        self.module_name = ""
        self.app_name = ""
        self.as_factory = as_factory
        self.as_simple = as_simple
        self.args = args
        self.factory = factory
        self.cwd = os.getcwd()

        if module_input:
            delimiter = ":" if ":" in module_input else "."
            module_name, app_name = module_input.rsplit(delimiter, 1)
            self.module_name = module_name
            self.app_name = app_name
            if self.app_name.endswith("()"):
                self.as_factory = True
                self.app_name = self.app_name[:-2]

    def load(self) -> SanicApp:
        module_path = os.path.abspath(self.cwd)
        if module_path not in sys.path:
            sys.path.append(module_path)

        if self.factory:
            return self.factory()
        else:
            from sanic.app import Sanic
            from sanic.simple import create_simple_server

            if self.as_simple:
                path = Path(self.module_input)
                app = create_simple_server(path)
            else:
                if self.module_name == "" and os.path.isdir(self.module_input):
                    raise ValueError(
                        "App not found.\n"
                        "   Please use --simple if you are passing a "
                        "directory to sanic.\n"
                        f"   eg. sanic {self.module_input} --simple"
                    )

                module = import_module(self.module_name)
                app = getattr(module, self.app_name, None)
                if self.as_factory:
                    try:
                        app = app(self.args)
                    except TypeError:
                        app = app()

                app_type_name = type(app).__name__

                if (
                    not isinstance(app, Sanic)
                    and self.args
                    and hasattr(self.args, "module")
                ):
                    if callable(app):
                        solution = f"sanic {self.args.module} --factory"
                        raise ValueError(
                            "Module is not a Sanic app, it is a "
                            f"{app_type_name}\n"
                            "  If this callable returns a "
                            f"Sanic instance try: \n{solution}"
                        )

                    raise ValueError(
                        f"Module is not a Sanic app, it is a {app_type_name}\n"
                        f"  Perhaps you meant {self.args.module}:app?"
                    )
        return app
