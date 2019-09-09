import os
import socket
import stat
import sys
import time
import traceback

from enum import Enum
from functools import partial
from inspect import isawaitable
from ipaddress import ip_address
import multiprocessing as mp
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import sleep as time_sleep
from time import time

import trio

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import ConnectionTerminated, DataReceived, RequestReceived
from httptools.parser.errors import HttpParserError

from sanic.compat import Header
from sanic.exceptions import (
    HeaderExpectationFailed,
    InvalidUsage,
    PayloadTooLarge,
    RequestTimeout,
    SanicException,
    ServerError,
    ServiceUnavailable,
    VersionNotSupported,
)
from sanic.log import access_logger, logger
from sanic.protocol import H1Stream
from sanic.request import EXPECT_HEADER, Request, StreamBuffer
from sanic.response import HTTPResponse


try:
    from signal import SIGHUP
except:
    SIGHUP = SIGTERM



class Signal:
    stopped = False

SSL, H2 = Enum("Protocol", "SSL H2")

h2config = H2Configuration(
    client_side=False,
    header_encoding="utf-8",
    validate_outbound_headers=False,
    normalize_outbound_headers=False,
    validate_inbound_headers=False,
    normalize_inbound_headers=False,
    logger=None,  # logger
)


idle_connections = set()
quit = trio.Event()

def trigger_graceful_exit():
    """Signals all running connections to terminate smoothly."""
    # Disallow new requests
    quit.set()
    # Promptly terminate idle connections
    for c in idle_connections:
        c.cancel()

def parse_h1_request(data: bytes) -> dict:
    try:
        data = data.decode()
    except UnicodeDecodeError:
        data = data.decode("ISO-8859-1")
    req, *hlines = data.split("\r\n")
    method, path, version = req.split(" ", 2)
    if version != "HTTP/1.1":
        raise VersionNotSupported(f"Expected 'HTTP/1.1', got '{version}'")
    headers = {":method": method, ":path": path}
    for name, value in (h.split(": ", 1) for h in hlines):
        name = name.lower()
        old = headers.get(name)
        headers[name] = value if old is None else f"{old}, {value}"
    return headers


def push_back(stream, data):
    if not data:
        return
    stream_type = type(stream)

    class PushbackStream(stream_type):
        async def receive_some(self, max_bytes=None):
            if max_bytes and max_bytes < len(data):
                ret = data[:max_bytes]
                del data[:max_bytes]
                return ret
            self.__class__ = stream_type
            return data

    stream.__class__ = PushbackStream


class HttpProtocol:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.request_class = self.request_class or Request
        self.stream = None
        self.servername = None  # User-visible server hostname, no port!

    async def ssl_init(self):
        def servername_callback(sock, req_hostname, cb_context):
            self.servername = req_hostname

        self.ssl.sni_callback = servername_callback
        self.stream = trio.SSLStream(
            self.stream, self.ssl, server_side=True, https_compatible=True
        )
        await self.stream.do_handshake()
        self.alpn = self.stream.selected_alpn_protocol()

    async def sniff_protocol(self):
        req = await self.receive_request()
        if isinstance(req, bytearray):
            # HTTP1 but might be Upgrade to websocket or h2c
            headers = parse_h1_request(req)
            upgrade = headers.get("upgrade")
            if upgrade == "h2c":
                return self.http2(settings_header=headers["http2-settings"])
            if upgrade == "websocket":
                self.websocket = True
            return self.http1(headers=headers)
        if req is SSL:
            if not self.ssl:
                raise RuntimeError("Only plain HTTP supported (not SSL).")
            await self.ssl_init()
            if not self.alpn or self.alpn == "http/1.1":
                return self.http1()
            if self.alpn == "h2":
                return self.http2()
            raise RuntimeError(f"Unknown ALPN {self.alpn}")
        # HTTP2 (not Upgrade)
        if req is H2:
            return self.http2()

    def set_timeout(self, timeout: str):
        self.nursery.cancel_scope.deadline = trio.current_time() + getattr(
            self, f"{timeout}_timeout"
        )

    async def run(self, stream):
        assert not self.stream
        self.stream = stream
        self.stream.push_back = partial(push_back, stream)
        async with stream, trio.open_nursery() as self.nursery:
            try:
                self.set_timeout("request")
                protocol_coroutine = await self.sniff_protocol()
                if not protocol_coroutine:
                    return
                await protocol_coroutine
                self.nursery.cancel_scope.cancel()  # Terminate all connections
            except trio.BrokenResourceError:
                pass  # Connection reset by peer
            except Exception:
                logger.exception("Error in server")
            finally:
                idle_connections.discard(self.nursery.cancel_scope)

    async def receive_request(self):
        idle_connections.add(self.nursery.cancel_scope)
        with trio.fail_after(self.request_timeout):
            buffer = bytearray()
            async for data in self.stream:
                idle_connections.discard(self.nursery.cancel_scope)
                prevpos = max(0, len(buffer) - 3)
                buffer += data
                if buffer[0] == 0x16:
                    self.stream.push_back(buffer)
                    return SSL
                if len(buffer) > self.request_max_size:
                    raise RuntimeError("Request larger than request_max_size")
                pos = buffer.find(b"\r\n\r\n", prevpos)
                if pos > 0:
                    req = buffer[:pos]
                    if req == b"PRI * HTTP/2.0":
                        self.stream.push_back(buffer)
                        return H2
                    self.stream.push_back(buffer[pos+4:])
                    return req
        if buffer:
            raise RuntimeError(f"Peer disconnected after {buffer!r:.200}")

    async def http1(self, headers=None):
        _response = None
        while not quit.is_set():
            # Process request
            if headers is None:
                req = await self.receive_request()
                if not req:
                    return
                headers = parse_h1_request(req)
            request = self.request_class(
                url_bytes=headers[":path"].encode(),
                headers=Header(headers),
                version="1.1",
                method=headers[":method"],
                transport=None,
                app=self.app,
            )
            need_continue = headers.get("expect", "").lower() == "100-continue"

            if "chunked" in headers.get("transfer-encoding", "").lower():
                raise RuntimeError("Chunked requests not supported")  # FIXME
            request.stream = H1Stream(
                headers, self.stream, self.set_timeout, need_continue
            )
            headers = None
            try:
                await self.request_handler(request)
            except trio.BrokenResourceError:
                logger.info(f"Client disconnected during {request.method} {request.path}")
                return
            except Exception as e:
                r = self.app.error_handler.default(request, e)
                try:
                    await request.stream.respond(r.status, r.headers).send(
                        data_bytes=r.body
                    )
                except RuntimeError:
                    pass  # If we cannot send to client anymore
                raise
            finally:
                await request.stream.aclose()
            self.set_timeout("request")

    async def h2_sender(self):
        async for _ in self.can_send:
            await self.stream.send_all(self.conn.data_to_send())

    async def http2(self, settings_header=None):
        self.conn = H2Connection(config=h2config)
        if settings_header:  # Upgrade from HTTP 1.1
            self.conn.initiate_upgrade_connection(settings_header)
            await self.stream.send_all(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Connection: Upgrade\r\n"
                b"Upgrade: h2c\r\n"
                b"\r\n" + self.conn.data_to_send()
            )
        else:  # straight into HTTP/2 mode
            self.conn.initiate_connection()
            await self.stream.send_all(self.conn.data_to_send())
        # A trigger mechanism that ensures promptly sending data from self.conn
        # to stream; size must be > 0 to avoid data left unsent in buffer
        # when a stream is canceled while awaiting on send_some.
        self.send_some, self.can_send = trio.open_memory_channel(1)
        self.nursery.start_soon(self.h2_sender)
        idle_connections.add(self.nursery.cancel_scope)
        self.requests = {}
        async for data in self.stream:
            for event in self.conn.receive_data(data):
                # print("-*-", event)
                if isinstance(event, RequestReceived):
                    self.nursery.start_soon(
                        self.h2request, event.stream_id, event.headers
                    )
                    # idle_connections.discard(self.nursery.cancel_scope)
                if isinstance(event, ConnectionTerminated):
                    return
            await self.send_some.send(...)

    async def h2request(self, stream_id, headers):
        hdrs = {}
        for name, value in headers:
            old = hdrs.get(name)
            hdrs[name] = value if old is None else f"{old}, {value}"
        # Process response
        request = self.request_class(
            url_bytes=hdrs.get(":path", "").encode(),
            headers=Header(headers),
            version="h2",
            method=hdrs[":method"],
            transport=None,
            app=self.app,
        )

        async def write_response(response):
            headers = (
                (":status", f"{response.status}"),
                ("content-length", f"{len(response.body)}"),
                ("content-type", response.content_type),
                *response.headers,
            )
            self.conn.send_headers(stream_id, headers)
            self.conn.send_data(stream_id, response.body, end_stream=True)
            await self.send_some.send(...)

        with trio.fail_after(self.response_timeout):
            await self.request_handler(request, write_response, None)

    async def websocket(self):
        logger.info("Websocket requested, not yet implemented")


async def trigger_events(events):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event()
        if isawaitable(result):
            await result


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
    proto = partial(
        protocol,
        connections=connections,
        signal=signal,
        app=app,
        ssl=ssl,
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

    app.asgi = False
    assert not (
        run_async or run_multiple or asyncio_server_kwargs or loop
    ), "Not implemented"

    acceptor = partial(
        runaccept,
        before_start=before_start,
        after_start=after_start,
        before_stop=before_stop,
        after_stop=after_stop,
        proto=proto,
        graceful_shutdown_timeout=graceful_shutdown_timeout,
    )

    server = partial(
        runserver,
        acceptor=acceptor,
        host=host,
        port=port,
        sock=sock,
        backlog=backlog,
        workers=workers,
    )
    return server() if run_async else trio.run(server)


async def runserver(acceptor, host, port, sock, backlog, workers):
    if host and host.startswith("unix:"):
        open_listeners = partial(
            # Not Implemented: open_unix_listeners, path=host[5:], backlog=backlog
        )
    else:
        open_listeners = partial(
            trio.open_tcp_listeners,
            host=host,
            port=port or 8000,
            backlog=backlog,
        )
    try:
        listeners = await open_listeners()
    except Exception:
        logger.exception("Unable to start server")
        return
    for l in listeners:
        l.socket.set_inheritable(True)
    processes = []

    try:
        if workers:
            # Spawn method is consistent across platforms and, unlike the fork
            # method, can be used from within async functions (such as this one).
            mp.set_start_method("spawn")
            with trio.open_signal_receiver(SIGINT, SIGTERM, SIGHUP) as sigiter:
                logger.info(f"Server starting, {workers} worker processes")
                while True:
                    while len(processes) < workers:
                        p = mp.Process(
                            target=trio.run, args=(acceptor, listeners)
                        )
                        p.daemon = True
                        p.start()
                        processes.append(p)
                        logger.info("Worker [%s]", p.pid)
                    # Wait for signals and periodically check processes
                    with trio.move_on_after(0.1):
                        s = await sigiter.__anext__()
                        logger.info(f"Server received {Signals(s).name}")
                        for p in processes:
                            p.terminate()
                        if s in (SIGTERM, SIGINT):
                            break
                    processes = [p for p in processes if p.is_alive()]
        else:  # workers=0
            logger.info("Server and worker started")
            await acceptor(listeners)
    finally:
        with trio.CancelScope() as cs:
            cs.shield = True
            # Close listeners and wait for workers to terminate
            for l in listeners:
                await l.aclose()
            for p in processes:
                p.join()
            logger.info("Server stopped")

async def sighandler(scopes, task_status=trio.TASK_STATUS_IGNORED):
    with trio.open_signal_receiver(SIGINT, SIGTERM, SIGHUP) as sigiter:
        t = None
        task_status.started()
        async for s in sigiter:
            # Ignore spuriously repeated signals
            if t is not None and trio.current_time() - t < 0.5:
                logger.debug(f"Ignored {Signals(s).name}")
                continue
            logger.info(f"Received {Signals(s).name}")
            if not scopes:
                raise trio.Cancelled("Signaled too many times")
            scopes.pop().cancel()
            t = trio.current_time()

async def runaccept(
    listeners,
    before_start,
    after_start,
    before_stop,
    after_stop,
    proto,
    graceful_shutdown_timeout,
):
    try:
        async with trio.open_nursery() as signal_nursery:
            cancel_scopes = [signal_nursery.cancel_scope]
            sigscope = await signal_nursery.start(sighandler, cancel_scopes)
            async with trio.open_nursery() as main_nursery:
                cancel_scopes.append(main_nursery.cancel_scope)
                await trigger_events(before_start)
                # Accept connections until a signal is received
                async with trio.open_nursery() as acceptor:
                    cancel_scopes.append(acceptor.cancel_scope)
                    acceptor.start_soon(
                        partial(
                            trio.serve_listeners,
                            handler=lambda stream: proto().run(stream),
                            listeners=listeners,
                            handler_nursery=main_nursery,
                        )
                    )
                    await trigger_events(after_start)
                # No longer accepting new connections. Attempt graceful exit.
                main_nursery.cancel_scope.deadline = (
                    trio.current_time() + graceful_shutdown_timeout
                )
                trigger_graceful_exit()
                await trigger_events(before_stop)
            await trigger_events(after_stop)
            signal_nursery.cancel_scope.cancel()  # Exit signal handler
        logger.info(f"Worker finished gracefully")
    except BaseException:
        logger.exception(f"Worker terminating")
