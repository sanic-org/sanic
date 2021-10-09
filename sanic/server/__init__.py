import asyncio

from sanic.models.server_types import ConnInfo, Signal
from sanic.server.async_server import AsyncioServer
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.runners import serve, serve_multiple, serve_single


def use_uvloop() -> bool:
    """
    Use uvloop (if available) instead of the default
    asyncio loop.
    """
    try:
        import uvloop  # type: ignore

        if not isinstance(
            asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy
        ):
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        return False
    return True


__all__ = (
    "AsyncioServer",
    "ConnInfo",
    "HttpProtocol",
    "Signal",
    "serve",
    "serve_multiple",
    "serve_single",
)
