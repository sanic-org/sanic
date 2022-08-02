import asyncio
import socket

from multiprocessing.connection import Connection
from ssl import SSLContext
from typing import Optional, Type

from sanic.application.constants import ServerStage
from sanic.application.state import ApplicationServerInfo
from sanic.http.constants import HTTP
from sanic.models.server_types import Signal
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.runners import _serve_http_1, _serve_http_3
from sanic.worker.multiplexer import WorkerMultiplexer


def worker_serve(
    host,
    port,
    app_name: str,
    restart_flag: Optional[Connection],
    server_info: Optional[ApplicationServerInfo] = None,
    ssl: Optional[SSLContext] = None,
    sock: Optional[socket.socket] = None,
    unix: Optional[str] = None,
    reuse_port: bool = False,
    loop=None,
    protocol: Type[asyncio.Protocol] = HttpProtocol,
    backlog: int = 100,
    register_sys_signals: bool = True,
    run_multiple: bool = False,
    run_async: bool = False,
    connections=None,
    signal=Signal(),
    state=None,
    asyncio_server_kwargs=None,
    version=HTTP.VERSION_1,
    config=None,
):
    from sanic import Sanic

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Sanic.get_app(app_name).refresh(server_info)

    if restart_flag:
        app.multiplexer = WorkerMultiplexer(restart_flag)

    if app.debug:
        loop.set_debug(app.debug)

    app.asgi = False
    primary_server_info = app.state.server_info[0]
    primary_server_info.stage = ServerStage.SERVING
    if config:
        app.update_config(config)

    if version is HTTP.VERSION_3:
        return _serve_http_3(host, port, app, loop, ssl)
    return _serve_http_1(
        host,
        port,
        app,
        ssl,
        sock,
        unix,
        reuse_port,
        loop,
        protocol,
        backlog,
        register_sys_signals,
        run_multiple,
        run_async,
        connections,
        signal,
        state,
        asyncio_server_kwargs,
    )
