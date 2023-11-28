from __future__ import annotations

import os
import sys

from contextlib import suppress
from importlib import import_module
from inspect import isfunction
from pathlib import Path
from ssl import SSLContext
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union, cast

from sanic.http.tls.context import process_to_context
from sanic.http.tls.creators import MkcertCreator, TrustmeCreator


if TYPE_CHECKING:
    from sanic import Sanic as SanicApp

DEFAULT_APP_NAME = "app"


class AppLoader:
    """A helper to load application instances.

    Generally used by the worker to load the application instance.

    See [Dynamic Applications](/en/guide/deployment/app-loader) for information on when you may need to use this.

    Args:
        module_input (str): The module to load the application from.
        as_factory (bool): Whether the application is a factory.
        as_simple (bool): Whether the application is a simple server.
        args (Any): Arguments to pass to the application factory.
        factory (Callable[[], SanicApp]): A callable that returns a Sanic application instance.
    """  # noqa: E501

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
            if (
                delimiter in module_input
                and "\\" not in module_input
                and "/" not in module_input
            ):
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

            maybe_path = Path(self.module_input)
            if self.as_simple or (
                maybe_path.is_dir()
                and ("\\" in self.module_input or "/" in self.module_input)
            ):
                app = create_simple_server(maybe_path)
            else:
                implied_app_name = False
                if not self.module_name and not self.app_name:
                    self.module_name = self.module_input
                    self.app_name = DEFAULT_APP_NAME
                    implied_app_name = True
                module = import_module(self.module_name)
                app = getattr(module, self.app_name, None)
                if not app and implied_app_name:
                    raise ValueError(
                        "Looks like you only supplied a module name. Sanic "
                        "tried to locate an application instance named "
                        f"{self.module_name}:app, but was unable to locate "
                        "an application instance. Please provide a path "
                        "to a global instance of Sanic(), or a callable that "
                        "will return a Sanic() application instance."
                    )
                if self.as_factory or isfunction(app):
                    try:
                        app = app(self.args)
                    except TypeError:
                        app = app()

                app_type_name = type(app).__name__

                if (
                    not isinstance(app, Sanic)
                    and self.args
                    and hasattr(self.args, "target")
                ):
                    with suppress(ModuleNotFoundError):
                        maybe_module = import_module(self.module_input)
                        app = getattr(maybe_module, "app", None)
                    if not app:
                        message = (
                            "Module is not a Sanic app, "
                            f"it is a {app_type_name}\n"
                            f"  Perhaps you meant {self.args.target}:app?"
                        )
                        raise ValueError(message)
        return app


class CertLoader:
    _creators = {
        "mkcert": MkcertCreator,
        "trustme": TrustmeCreator,
    }

    def __init__(
        self,
        ssl_data: Optional[
            Union[SSLContext, Dict[str, Union[str, os.PathLike]]]
        ],
    ):
        self._ssl_data = ssl_data
        self._creator_class = None
        if not ssl_data or not isinstance(ssl_data, dict):
            return

        creator_name = cast(str, ssl_data.get("creator"))

        self._creator_class = self._creators.get(creator_name)
        if not creator_name:
            return

        if not self._creator_class:
            raise RuntimeError(f"Unknown certificate creator: {creator_name}")

        self._key = ssl_data["key"]
        self._cert = ssl_data["cert"]
        self._localhost = cast(str, ssl_data["localhost"])

    def load(self, app: SanicApp):
        if not self._creator_class:
            return process_to_context(self._ssl_data)

        creator = self._creator_class(app, self._key, self._cert)
        return creator.generate_cert(self._localhost)
