import trio
import os
import socket
import stat
import sys
import time
import traceback

from functools import partial
from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import RequestReceived, DataReceived, ConnectionTerminated
from inspect import isawaitable
from ipaddress import ip_address
from multiprocessing import Process
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import time, sleep as time_sleep
from httptools.parser.errors import HttpParserError

SIGHUP = SIGTERM

from sanic.compat import Header
from sanic.exceptions import (
    HeaderExpectationFailed,
    InvalidUsage,
    PayloadTooLarge,
    RequestTimeout,
    ServerError,
    VersionNotSupported,
    ServiceUnavailable,
)
from sanic.log import access_logger, logger
from sanic.request import EXPECT_HEADER, Request, StreamBuffer
from sanic.response import HTTPResponse, NewStreamingHTTPResponse


class Signal:
    stopped = False


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

class H1StreamRequest:
    __slots__ = "length", "pos", "stream", "set_timeout", "trigger_continue"
    def __init__(self, headers, stream, set_timeout, trigger_continue):
        self.length = int(headers.get("content-length"))
        if self.length < 0:
            raise InvalidUsage("Content-length must be positive")
        self.pos = 0
        self.stream = stream
        self.set_timeout = set_timeout
        self.trigger_continue = trigger_continue

    async def __aiter__(self):
        while True:
            data = await self.read()
            if not data: return
            yield data

    async def read(self):
        await self.trigger_continue()
        if self.pos == self.length: return None
        buf = await self.stream.receive_some()
        if len(buf) > self.length:
            push_back(self.stream, buf[self.length:])
            buf = buf[:self.length]
        self.pos += len(buf)
        # Extend or switch deadline
        self.set_timeout("request" if self.length else "response")
        return buf


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
        buffer = bytearray()
        req = await self._receive_request_using(buffer)
        if isinstance(req, bytearray):
            # HTTP1 but might be Upgrade to websocket or h2c
            headers = parse_h1_request(req)
            upgrade = headers.get("upgrade")
            if upgrade == "h2c":
                return self.http2(settings_header=headers["http2-settings"])
            if upgrade == "websocket":
                return self.websocket()
            return self.http1(headers=headers)
        push_back(self.stream, buffer)
        if req == "ssl":
            if not self.ssl:
                raise RuntimeError("Only plain HTTP supported (not SSL).")
            await self.ssl_init()
            if not self.alpn or self.alpn == "http/1.1":
                return self.http1()
            if self.alpn == "h2":
                return self.http2()
            raise RuntimeError(f"Unknown ALPN {self.alpn}")
        # HTTP2 (not Upgrade)
        if req == "h2":
            return self.http2()

    def set_timeout(self, timeout: str):
        self.nursery.cancel_scope.deadline = (
            trio.current_time() + getattr(self, f"{timeout}_timeout")
        )

    async def run(self, stream):
        assert not self.stream
        self.stream = stream
        try:
            async with stream, trio.open_nursery() as self.nursery:
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

    async def _receive_request_using(self, buffer: bytearray):
        idle_connections.add(self.nursery.cancel_scope)
        with trio.fail_after(self.request_timeout):
            async for data in self.stream:
                idle_connections.discard(self.nursery.cancel_scope)
                prevpos = max(0, len(buffer) - 3)
                buffer += data
                if buffer[0] < 0x20:
                    return "ssl"
                if len(buffer) > self.request_max_size:
                    raise RuntimeError("Request larger than request_max_size")
                pos = buffer.find(b"\r\n\r\n", prevpos)
                if pos > 0:
                    req = buffer[:pos]
                    if req == b"PRI * HTTP/2.0": return "h2"
                    del buffer[: pos + 4]
                    return req
        if buffer:
            raise RuntimeError(f"Peer disconnected after {buffer!r}")

    async def http1(self, headers=None):
        buffer = bytearray()
        _response = None
        while True:
            # Process request
            if headers is None:
                req = await self._receive_request_using(buffer)
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
            async def trigger_continue():
                nonlocal need_continue
                if need_continue is False:
                    return
                await self.stream.send_all(b"HTTP/1.1 100 Continue\r\n\r\n")
                need_continue = False
            if "chunked" in headers.get("transfer-encoding", "").lower():
                raise RuntimeError("Chunked requests not supported")  # FIXME
            if "content-length" in headers:
                push_back(self.stream, buffer)
                del buffer[:]
                request.stream = H1StreamRequest(
                    headers,
                    self.stream,
                    self.set_timeout,
                    trigger_continue,
                )
            else:
                self.set_timeout("response")
            headers = None
            _response = None
            # Implement request.respond:
            async def respond(response=None, *, status=200, headers=None, content_type="text/html"):
                nonlocal _response
                if _response:
                    raise ServerError("Duplicate responses for a single request!")
                await trigger_continue()
                if response is None:
                    _response = NewStreamingHTTPResponse(self.stream)
                    await _response.write_headers(status, headers, content_type)
                    return _response
                # Middleware has a chance to replace the response
                response = await self.app._run_response_middleware(
                    request, response
                )
                _response = response
                if not isinstance(response, HTTPResponse):
                    raise ServerError(f"Handling {request.path}: HTTPResponse expected but got {type(response).__name__}")
                await self.stream.send_all(
                    response.output("1.1", self.keep_alive, self.keep_alive_timeout)
                )

            request.respond = respond
            await self.request_handler(request)
            if not _response:
                raise ServerError("Request handler made no response.")
            if hasattr(_response, "aclose"):
                await _response.aclose()
            _response = None
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
                    #idle_connections.discard(self.nursery.cancel_scope)
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
    return server() if run_async else server()


def runserver(acceptor, host, port, sock, backlog, workers):
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
        listeners = trio.run(open_listeners)
    except Exception:
        logger.exception("Unable to start server")
        return
    for l in listeners:
        l.socket.set_inheritable(True)
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
        while True:
            while len(processes) < workers:
                p = Process(target=trio.run, args=(acceptor, listeners, master_pid))
                p.daemon = True
                p.start()
                processes.append(p)
            time_sleep(0.1)  # Poll for dead processes
            processes = [p for p in processes if p.is_alive()]
            s, sig = sig, None
            if not s:
                continue
            for p in processes:
                os.kill(p.pid, SIGHUP)
            if s in (SIGINT, SIGTERM):
                break
        for l in listeners:
            trio.run(l.aclose)
        for p in processes:
            p.join()
    else:
        runworker()


async def runaccept(
    listeners,
    master_pid,
    before_start,
    after_start,
    before_stop,
    after_stop,
    proto,
    graceful_shutdown_timeout,
):
    try:
        pid = os.getpid()
        logger.info("Starting worker [%s]", pid)
        async with trio.open_nursery() as main_nursery:
            await trigger_events(before_start)
            # Accept connections until a signal is received, then perform graceful exit
            async with trio.open_nursery() as acceptor:
                acceptor.start_soon(
                    partial(
                        trio.serve_listeners,
                        handler=lambda stream: proto().run(stream),
                        listeners=listeners,
                        handler_nursery=main_nursery,
                    )
                )
                await trigger_events(after_start)
                # Wait for a signal and then exit gracefully
                with trio.open_signal_receiver(
                    SIGINT, SIGTERM, SIGHUP
                ) as sigiter:
                    s = await sigiter.__anext__()
                    logger.info(f"Received {Signals(s).name}")
                    if s != SIGHUP:
                        os.kill(master_pid, SIGTERM)
                    acceptor.cancel_scope.cancel()
            now = trio.current_time()
            for c in idle_connections:
                c.cancel()
            main_nursery.cancel_scope.deadline = (
                now + graceful_shutdown_timeout
            )
            await trigger_events(before_stop)
        await trigger_events(after_stop)
        logger.info(f"Gracefully finished worker [{pid}]")
    except BaseException as e:
        logger.exception(f"Stopped worker [{pid}]")
