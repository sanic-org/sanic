import trio
import os
import socket
import stat
import sys
import time
import traceback

from functools import partial
from inspect import isawaitable
from ipaddress import ip_address
from multiprocessing import Process
from signal import SIG_IGN, SIGINT, SIGTERM, SIGHUP, Signals
from signal import signal as signal_func
from time import time, sleep as time_sleep

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError
from multidict import CIMultiDict

from sanic.compat import Header
from sanic.exceptions import (
    HeaderExpectationFailed,
    InvalidUsage,
    PayloadTooLarge,
    RequestTimeout,
    ServerError,
    ServiceUnavailable,
)
from sanic.log import access_logger, logger
from sanic.request import EXPECT_HEADER, Request, StreamBuffer
from sanic.response import HTTPResponse

class Signal:
    stopped = False

idle_connections = set()

class HttpProtocol:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.request_class = self.request_class or Request

    async def run(self, stream):
        try:
            async with stream, trio.open_nursery() as self.nursery:
                while True:
                    self.nursery.cancel_scope.deadline = trio.current_time() + self.request_timeout
                    # Read headers
                    buffer = bytearray()
                    idle_connections.add(self.nursery.cancel_scope)
                    async for data in stream:
                        idle_connections.remove(self.nursery.cancel_scope)
                        prevpos = max(0, len(buffer) - 3)
                        buffer += data
                        pos = buffer.find(b"\r\n\r\n", prevpos)
                        if pos > 0: break  # End of headers
                        if buffer > request_max_size:
                            self.error_response("request too large")
                            return
                    else:
                        return  # Peer closed connection
                    headers = buffer[:pos]
                    del buffer[:pos + 4]
                    try:
                        headers = headers.decode()
                    except UnicodeDecodeError:
                        headers = headers.decode("ISO-8859-1")
                    req, *headers = headers.split("\r\n")
                    method, path, version = req.split(" ")
                    version = version[5:]
                    assert version == "1.1"
                    headers = dict(h.split(": ", 1) for h in headers)
                    self.nursery.cancel_scope.deadline = trio.current_time() + self.response_timeout
                    request = self.request_class(
                        url_bytes=path.encode(),
                        headers=Header(headers),
                        version=version,
                        method=method,
                        transport=None,
                        app=self.app,
                    )
                    keep_alive = True
                    async def write_response(response):
                        await stream.send_all(response.output(
                            request.version, keep_alive, self.keep_alive_timeout
                        ))
                    await self.request_handler(request, write_response, None)
        except trio.BrokenResourceError:
            pass  # Connection reset by peer
        except Exception:
            logger.exception("Error in server")
        finally:
            idle_connections.remove(self.nursery.cancel_scope)

    async def error_response(self, message):
        pass

async def trigger_events(events):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event()
        if isawaitable(result):
            await result


def serve_multiple(server_settings, workers):
    return serve(**server_settings, workers=workers)

def serve(
    host,
    port,
    app,
    request_handler,
    error_handler,
    before_start=None,
    after_start=None,
    before_stop=None,
    after_stop=None,
    debug=False,
    request_timeout=60,
    response_timeout=60,
    keep_alive_timeout=5,
    ssl=None,
    sock=None,
    request_max_size=None,
    request_buffer_queue_size=100,
    protocol=HttpProtocol,
    backlog=100,
    register_sys_signals=True,
    run_multiple=False,
    run_async=False,
    connections=None,
    signal=Signal(),
    request_class=None,
    access_log=True,
    keep_alive=True,
    is_request_stream=False,
    router=None,
    websocket_max_size=None,
    websocket_max_queue=None,
    websocket_read_limit=2 ** 16,
    websocket_write_limit=2 ** 16,
    state=None,
    graceful_shutdown_timeout=15.0,
    asyncio_server_kwargs=None,
    workers=1,
    loop=None,
):
    async def handle_connection(stream):
        proto = protocol(
            connections=connections,
            signal=signal,
            app=app,
            request_handler=request_handler,
            error_handler=error_handler,
            request_timeout=request_timeout,
            response_timeout=response_timeout,
            keep_alive_timeout=keep_alive_timeout,
            request_max_size=request_max_size,
            request_class=request_class,
            access_log=access_log,
            keep_alive=keep_alive,
            is_request_stream=is_request_stream,
            router=router,
            websocket_max_size=websocket_max_size,
            websocket_max_queue=websocket_max_queue,
            websocket_read_limit=websocket_read_limit,
            websocket_write_limit=websocket_write_limit,
            state=state,
            debug=debug,
        )
        await proto.run(stream)

    app.asgi = False
    assert not (run_async or run_multiple or asyncio_server_kwargs or loop), "Not implemented"

    acceptor = partial(
        runaccept,
        before_start=before_start,
        after_start=after_start,
        before_stop=before_stop,
        after_stop=after_stop,
        handle_connection=handle_connection,
        graceful_shutdown_timeout=graceful_shutdown_timeout,
    )

    server = partial(
        runserver,
        acceptor=acceptor,
        host=host,
        port=port,
        ssl=ssl,
        sock=sock,
        backlog=backlog,
        workers=workers,
    )
    return server() if run_async else server()

def runserver(
    acceptor,
    host,
    port,
    ssl,
    sock,
    backlog,
    workers,
):
    if host and host.startswith("unix:"):
        open_listeners = partial(
            # Not Implemented: open_unix_listeners, path=host[5:], backlog=backlog
        )
    else:
        open_listeners = partial(
            trio.open_tcp_listeners,
            host=host, port=port or 8000, backlog=backlog
        )
    try:
        listeners = trio.run(open_listeners)
    except Exception:
        logger.exception("Unable to start server")
        return
    if ssl:
        listeners = [
            trio.SSLListener(l, ssl, https_compatible=True) for l in listeners
        ]
    master_pid = os.getpid()
    runworker = lambda: trio.run(acceptor, listeners, master_pid)
    processes = []
    # Setup signal handlers to avoid crashing
    sig = None
    def handler(s, tb):
        nonlocal sig
        sig = s
    for s in (SIGINT, SIGTERM, SIGHUP):
        signal_func(s, handler)

    if workers:
        for l in listeners: l.socket.set_inheritable(True)
        while True:
            while len(processes) < workers:
                p = Process(target=runworker)
                p.daemon = True
                p.start()
                processes.append(p)
            time_sleep(0.1)  # Poll for dead processes
            processes = [p for p in processes if p.is_alive()]
            s, sig = sig, None
            if not s:
                continue
            for p in processes: os.kill(p.pid, SIGHUP)
            if s in (SIGINT, SIGTERM):
                break
        for l in listeners: trio.run(l.aclose)
        for p in processes: p.join()
    else:
        runworker()


async def runaccept(listeners, master_pid, before_start, after_start, before_stop, after_stop, handle_connection, graceful_shutdown_timeout):
    try:
        pid = os.getpid()
        logger.info("Starting worker [%s]", pid)
        async with trio.open_nursery() as main_nursery:
            await trigger_events(before_start)
            # Accept connections until a signal is received, then perform graceful exit
            async with trio.open_nursery() as acceptor:
                acceptor.start_soon(partial(
                    trio.serve_listeners,
                    handler=handle_connection,
                    listeners=listeners,
                    handler_nursery=main_nursery
                ))
                await trigger_events(after_start)
                # Wait for a signal and then exit gracefully
                with trio.open_signal_receiver(SIGINT, SIGTERM, SIGHUP) as sigiter:
                    s = await sigiter.__anext__()
                    logger.info(f"Received {Signals(s).name}")
                    if s != SIGHUP:
                        os.kill(master_pid, SIGTERM)
                    acceptor.cancel_scope.cancel()
            now = trio.current_time()
            for c in idle_connections: c.cancel()
            main_nursery.cancel_scope.deadline = now + graceful_shutdown_timeout
            await trigger_events(before_stop)
        await trigger_events(after_stop)
        logger.info(f"Gracefully finished worker [{pid}]")
    except BaseException as e:
        logger.exception(f"Stopped worker [{pid}]")
