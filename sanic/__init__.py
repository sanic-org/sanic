__version__ = "18.12.0"

__all__ = ["Sanic", "Blueprint"]


def __getattr__(name):
    if name == "Sanic":
        from sanic.app import Sanic
        return Sanic
    if name == "Blueprint":
        from sanic.blueprints import Blueprint
        return Blueprint
