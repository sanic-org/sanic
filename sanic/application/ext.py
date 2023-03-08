from __future__ import annotations

from contextlib import suppress
from importlib import import_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from sanic import Sanic


def setup_ext(app: Sanic, *, fail: bool = False, **kwargs):
    if not app.config.AUTO_EXTEND:
        return

    sanic_ext = None
    with suppress(ModuleNotFoundError):
        sanic_ext = import_module("sanic_ext")

    if not sanic_ext:  # no cov
        if fail:
            raise RuntimeError(
                "Sanic Extensions is not installed. You can add it to your "
                "environment using:\n$ pip install sanic[ext]\nor\n$ pip "
                "install sanic-ext"
            )

        return

    if not getattr(app, "_ext", None):
        Ext = getattr(sanic_ext, "Extend")
        app._ext = Ext(app, **kwargs)

        return app.ext
