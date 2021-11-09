from __future__ import annotations

import sys

from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict


if TYPE_CHECKING:
    from sanic import Sanic

    try:
        from sanic_ext import Extend
    except ImportError:
        ...

arg_cache: Dict[str, Dict[str, Any]] = {}


def setup_ext(app: Sanic):
    sanic_ext = sys.modules.get("sanic_ext")
    if sanic_ext:
        Ext: Extend = getattr(sanic_ext, "Extend")

        kwargs = arg_cache.pop(app.name, {})
        Ext(app, **kwargs)


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
