from __future__ import annotations

import sys

from ssl import SSLContext
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

from sanic.config import Config
from sanic.exceptions import ServerError
from sanic.http.constants import HTTP
from sanic.http.tls import get_ssl_context
from sanic.server.events import trigger_events


if TYPE_CHECKING:
    from sanic.app import Sanic

import asyncio
import multiprocessing
import os
import socket

from functools import partial
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func

from sanic.application.ext import setup_ext
from sanic.compat import OS_IS_WINDOWS, ctrlc_workaround_for_windows
from sanic.http.http3 import SessionTicketStore, get_config
from sanic.log import error_logger, server_logger
from sanic.models.server_types import Signal
from sanic.server.async_server import AsyncioServer
from sanic.server.protocols.http_protocol import Http3Protocol, HttpProtocol
from sanic.server.socket import (
    bind_socket,
    bind_unix_socket,
    remove_unix_socket,
)


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
    """
    if not run_async and not loop:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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
    # Ignore SIGINT when run_multiple
    if run_multiple:
        signal_func(SIGINT, SIG_IGN)
        os.environ["SANIC_WORKER_PROCESS"] = "true"

    # Register signals for graceful termination
    if register_sys_signals:
        if OS_IS_WINDOWS:
            ctrlc_workaround_for_windows(app)
        else:
            for _signal in [SIGTERM] if run_multiple else [SIGINT, SIGTERM]:
                loop.add_signal_handler(
                    _signal, partial(app.stop, terminate=False)
                )


def _run_server_forever(loop, before_stop, after_stop, cleanup, unix):
    pid = os.getpid()
    try:
        server_logger.info("Starting worker [%s]", pid)
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server_logger.info("Stopping worker [%s]", pid)

        loop.run_until_complete(before_stop())

        if cleanup:
            cleanup()

        loop.run_until_complete(after_stop())
        remove_unix_socket(unix)
        loop.close()


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

        if sys.version_info > (3, 7):
            app.shutdown_tasks(graceful - start_shutdown)

        # Force close non-idle connection after waiting for
        # graceful_shutdown_timeout
        for conn in connections:
            if hasattr(conn, "websocket") and conn.websocket:
                conn.websocket.fail_connection(code=1001)
            else:
                conn.abort()

    _setup_system_signals(app, run_multiple, register_sys_signals, loop)
    loop.run_until_complete(app._server_event("init", "after"))
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


def serve_single(server_settings):
    main_start = server_settings.pop("main_start", None)
    main_stop = server_settings.pop("main_stop", None)

    if not server_settings.get("run_async"):
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server_settings["loop"] = loop

    trigger_events(main_start, server_settings["loop"])
    serve(**server_settings)
    trigger_events(main_stop, server_settings["loop"])

    server_settings["loop"].close()


def serve_multiple(server_settings, workers):
    """Start multiple server processes simultaneously.  Stop on interrupt
    and terminate signals, and drain connections when complete.

    :param server_settings: kw arguments to be passed to the serve function
    :param workers: number of workers to launch
    :param stop_event: if provided, is used as a stop signal
    :return:
    """
    server_settings["reuse_port"] = True
    server_settings["run_multiple"] = True

    main_start = server_settings.pop("main_start", None)
    main_stop = server_settings.pop("main_stop", None)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    trigger_events(main_start, loop)

    # Create a listening socket or use the one in settings
    sock = server_settings.get("sock")
    unix = server_settings["unix"]
    backlog = server_settings["backlog"]
    if unix:
        sock = bind_unix_socket(unix, backlog=backlog)
        server_settings["unix"] = unix
    if sock is None:
        sock = bind_socket(
            server_settings["host"], server_settings["port"], backlog=backlog
        )
        sock.set_inheritable(True)
        server_settings["sock"] = sock
        server_settings["host"] = None
        server_settings["port"] = None

    processes = []

    def sig_handler(signal, frame):
        server_logger.info(
            "Received signal %s. Shutting down.", Signals(signal).name
        )
        for process in processes:
            os.kill(process.pid, SIGTERM)

    signal_func(SIGINT, lambda s, f: sig_handler(s, f))
    signal_func(SIGTERM, lambda s, f: sig_handler(s, f))
    mp = multiprocessing.get_context("fork")

    for _ in range(workers):
        process = mp.Process(
            target=serve,
            kwargs=server_settings,
        )
        process.daemon = True
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    # the above processes will block this until they're stopped
    for process in processes:
        process.terminate()

    trigger_events(main_stop, loop)

    sock.close()
    loop.close()
    remove_unix_socket(unix)


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
