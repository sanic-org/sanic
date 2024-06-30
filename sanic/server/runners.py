from __future__ import annotations

from ssl import SSLContext
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

from sanic.config import Config
from sanic.exceptions import ServerError
from sanic.http.constants import HTTP
from sanic.http.tls import get_ssl_context


if TYPE_CHECKING:
    from sanic.app import Sanic

import asyncio
import os
import socket

from functools import partial
from signal import SIG_IGN, SIGINT, SIGTERM
from signal import signal as signal_func

from sanic.application.ext import setup_ext
from sanic.compat import OS_IS_WINDOWS, ctrlc_workaround_for_windows
from sanic.http.http3 import SessionTicketStore, get_config
from sanic.log import error_logger, server_logger
from sanic.logging.setup import setup_logging
from sanic.models.server_types import Signal
from sanic.server.async_server import AsyncioServer
from sanic.server.protocols.http_protocol import Http3Protocol, HttpProtocol
from sanic.server.socket import bind_unix_socket, remove_unix_socket


try:
    from aioquic.asyncio import serve as quic_serve

    HTTP3_AVAILABLE = True
except ModuleNotFoundError:  # no cov
    HTTP3_AVAILABLE = False


def serve(
    host,
    port,
    app: Sanic,
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
):
    """Start asynchronous HTTP Server on an individual process.

    :param host: Address to host on
    :param port: Port to host on
    :param before_start: function to be executed before the server starts
                         listening. Takes arguments `app` instance and `loop`
    :param after_start: function to be executed after the server starts
                        listening. Takes  arguments `app` instance and `loop`
    :param before_stop: function to be executed when a stop signal is
                        received before it is respected. Takes arguments
                        `app` instance and `loop`
    :param after_stop: function to be executed when a stop signal is
                       received after it is respected. Takes arguments
                       `app` instance and `loop`
    :param ssl: SSLContext
    :param sock: Socket for the server to accept connections from
    :param unix: Unix socket to listen on instead of TCP port
    :param reuse_port: `True` for multiple workers
    :param loop: asyncio compatible event loop
    :param run_async: bool: Do not create a new event loop for the server,
                      and return an AsyncServer object rather than running it
    :param asyncio_server_kwargs: key-value args for asyncio/uvloop
                                  create_server method
    :return: Nothing

    Args:
        host (str): Address to host on
        port (int): Port to host on
        app (Sanic): Sanic app instance
        ssl (Optional[SSLContext], optional): SSLContext. Defaults to `None`.
        sock (Optional[socket.socket], optional): Socket for the server to
            accept connections from. Defaults to `None`.
        unix (Optional[str], optional): Unix socket to listen on instead of
            TCP port. Defaults to `None`.
        reuse_port (bool, optional): `True` for multiple workers. Defaults
            to `False`.
        loop: asyncio compatible event loop. Defaults
            to `None`.
        protocol (Type[asyncio.Protocol], optional): Protocol to use. Defaults
            to `HttpProtocol`.
        backlog (int, optional): The maximum number of queued connections
            passed to socket.listen(). Defaults to `100`.
        register_sys_signals (bool, optional): Register SIGINT and SIGTERM.
            Defaults to `True`.
        run_multiple (bool, optional): Run multiple workers. Defaults
            to `False`.
        run_async (bool, optional): Return an AsyncServer object.
            Defaults to `False`.
        connections: Connections. Defaults to `None`.
        signal (Signal, optional): Signal. Defaults to `Signal()`.
        state: State. Defaults to `None`.
        asyncio_server_kwargs (Optional[Dict[str, Union[int, float]]], optional):
            key-value args for asyncio/uvloop create_server method. Defaults
            to `None`.
        version (str, optional): HTTP version. Defaults to `HTTP.VERSION_1`.

    Raises:
        ServerError: Cannot run HTTP/3 server without aioquic installed.

    Returns:
        AsyncioServer: AsyncioServer object if `run_async` is `True`.
    """  # noqa: E501
    if not run_async and not loop:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    setup_logging(app.debug, app.config.NO_COLOR)

    if app.debug:
        loop.set_debug(app.debug)

    app.asgi = False

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


def _setup_system_signals(
    app: Sanic,
    run_multiple: bool,
    register_sys_signals: bool,
    loop: asyncio.AbstractEventLoop,
) -> None:  # no cov
    signal_func(SIGINT, SIG_IGN)
    signal_func(SIGTERM, SIG_IGN)
    os.environ["SANIC_WORKER_PROCESS"] = "true"
    # Register signals for graceful termination
    if register_sys_signals:
        if OS_IS_WINDOWS:
            ctrlc_workaround_for_windows(app)
        else:
            for _signal in [SIGINT, SIGTERM]:
                loop.add_signal_handler(
                    _signal, partial(app.stop, terminate=False)
                )


def _run_server_forever(loop, before_stop, after_stop, cleanup, unix):
    pid = os.getpid()
    try:
        server_logger.info("Starting worker [%s]", pid)
        loop.run_forever()
    finally:
        server_logger.info("Stopping worker [%s]", pid)

        loop.run_until_complete(before_stop())

        if cleanup:
            cleanup()

        loop.run_until_complete(after_stop())
        remove_unix_socket(unix)
        loop.close()
        server_logger.info("Worker complete [%s]", pid)


def _serve_http_1(
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
):
    connections = connections if connections is not None else set()
    protocol_kwargs = _build_protocol_kwargs(protocol, app.config)
    server = partial(
        protocol,
        loop=loop,
        connections=connections,
        signal=signal,
        app=app,
        state=state,
        unix=unix,
        **protocol_kwargs,
    )
    asyncio_server_kwargs = (
        asyncio_server_kwargs if asyncio_server_kwargs else {}
    )
    if OS_IS_WINDOWS and sock:
        pid = os.getpid()
        sock = sock.share(pid)
        sock = socket.fromshare(sock)
    # UNIX sockets are always bound by us (to preserve semantics between modes)
    elif unix:
        sock = bind_unix_socket(unix, backlog=backlog)
    server_coroutine = loop.create_server(
        server,
        None if sock else host,
        None if sock else port,
        ssl=ssl,
        reuse_port=reuse_port,
        sock=sock,
        backlog=backlog,
        **asyncio_server_kwargs,
    )

    setup_ext(app)
    if run_async:
        return AsyncioServer(
            app=app,
            loop=loop,
            serve_coro=server_coroutine,
            connections=connections,
        )

    loop.run_until_complete(app._startup())
    loop.run_until_complete(app._server_event("init", "before"))
    app.ack()

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except BaseException:
        error_logger.exception("Unable to start server", exc_info=True)
        return

    def _cleanup():
        # Wait for event loop to finish and all connections to drain
        http_server.close()
        loop.run_until_complete(http_server.wait_closed())

        # Complete all tasks on the loop
        signal.stopped = True
        for connection in connections:
            connection.close_if_idle()

        # Gracefully shutdown timeout.
        # We should provide graceful_shutdown_timeout,
        # instead of letting connection hangs forever.
        # Let's roughly calcucate time.
        graceful = app.config.GRACEFUL_SHUTDOWN_TIMEOUT
        start_shutdown: float = 0
        while connections and (start_shutdown < graceful):
            loop.run_until_complete(asyncio.sleep(0.1))
            start_shutdown = start_shutdown + 0.1

        app.shutdown_tasks(graceful - start_shutdown)

        # Force close non-idle connection after waiting for
        # graceful_shutdown_timeout
        for conn in connections:
            if hasattr(conn, "websocket") and conn.websocket:
                conn.websocket.fail_connection(code=1001)
            else:
                conn.abort()

        app.set_serving(False)

    _setup_system_signals(app, run_multiple, register_sys_signals, loop)
    loop.run_until_complete(app._server_event("init", "after"))
    app.set_serving(True)
    _run_server_forever(
        loop,
        partial(app._server_event, "shutdown", "before"),
        partial(app._server_event, "shutdown", "after"),
        _cleanup,
        unix,
    )


def _serve_http_3(
    host,
    port,
    app,
    loop,
    ssl,
    register_sys_signals: bool = True,
    run_multiple: bool = False,
):
    if not HTTP3_AVAILABLE:
        raise ServerError(
            "Cannot run HTTP/3 server without aioquic installed. "
        )
    protocol = partial(Http3Protocol, app=app)
    ticket_store = SessionTicketStore()
    ssl_context = get_ssl_context(app, ssl)
    config = get_config(app, ssl_context)
    coro = quic_serve(
        host,
        port,
        configuration=config,
        create_protocol=protocol,
        session_ticket_fetcher=ticket_store.pop,
        session_ticket_handler=ticket_store.add,
    )
    server = AsyncioServer(app, loop, coro, [])
    loop.run_until_complete(server.startup())
    loop.run_until_complete(server.before_start())
    app.ack()
    loop.run_until_complete(server)
    _setup_system_signals(app, run_multiple, register_sys_signals, loop)
    loop.run_until_complete(server.after_start())

    # TODO: Create connection cleanup and graceful shutdown
    cleanup = None
    _run_server_forever(
        loop, server.before_stop, server.after_stop, cleanup, None
    )


def _build_protocol_kwargs(
    protocol: Type[asyncio.Protocol], config: Config
) -> Dict[str, Union[int, float]]:
    if hasattr(protocol, "websocket_handshake"):
        return {
            "websocket_max_size": config.WEBSOCKET_MAX_SIZE,
            "websocket_ping_timeout": config.WEBSOCKET_PING_TIMEOUT,
            "websocket_ping_interval": config.WEBSOCKET_PING_INTERVAL,
        }
    return {}
