from __future__ import annotations

from contextlib import suppress
from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict


if TYPE_CHECKING:  # no cov
    from sanic import Sanic

    try:
        from sanic_ext import Extend  # type: ignore
    except ImportError:
        ...

arg_cache: Dict[str, Dict[str, Any]] = {}


def setup_ext(app: Sanic):
    sanic_ext = None
    with suppress(ModuleNotFoundError):
        sanic_ext = import_module("sanic_ext")

    if sanic_ext and not getattr(app, "_ext", None):
        Ext: Extend = getattr(sanic_ext, "Extend")

        kwargs = arg_cache.pop(app.name, {})
        app._ext = Ext(app, **kwargs)

        return app.ext


def cache_args(app: Sanic, **kwargs):
    try:
        import_module("sanic_ext")
    except ModuleNotFoundError:
        raise RuntimeError(
            "Sanic Extensions is not installed. You can add it to your "
            "environment using:\n$ pip install sanic[ext]\nor\n$ pip install "
            "sanic-ext"
        )
    else:
        arg_cache[app.name] = kwargs
