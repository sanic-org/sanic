import asyncio
import multiprocessing
import os
import secrets
import socket
import stat
import sys
import traceback

from collections import deque
from functools import partial
from inspect import isawaitable
from ipaddress import ip_address
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import time
from typing import Dict, Type, Union

from httptools import HttpRequestParser  # type: ignore
from httptools.parser.errors import HttpParserError  # type: ignore

from sanic.compat import Header, ctrlc_workaround_for_windows
from sanic.config import Config
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


try:
    import uvloop  # type: ignore

    if not isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

OS_IS_WINDOWS = os.name == "nt"


class Signal:
    stopped = False


class ConnInfo:
    """Local and remote addresses and SSL status info."""

    __slots__ = (
        "sockname",
        "peername",
        "server",
        "server_port",
        "client",
        "client_port",
        "ssl",
    )

    def __init__(self, transport, unix=None):
        self.ssl = bool(transport.get_extra_info("sslcontext"))
        self.server = self.client = ""
        self.server_port = self.client_port = 0
        self.peername = None
        self.sockname = addr = transport.get_extra_info("sockname")
        if isinstance(addr, str):  # UNIX socket
            self.server = unix or addr
            return
        # IPv4 (ip, port) or IPv6 (ip, port, flowinfo, scopeid)
        if isinstance(addr, tuple):
            self.server = addr[0] if len(addr) == 2 else f"[{addr[0]}]"
            self.server_port = addr[1]
            # self.server gets non-standard port appended
            if addr[1] != (443 if self.ssl else 80):
                self.server = f"{self.server}:{addr[1]}"
        self.peername = addr = transport.get_extra_info("peername")
        if isinstance(addr, tuple):
            self.client = addr[0] if len(addr) == 2 else f"[{addr[0]}]"
            self.client_port = addr[1]


class HttpProtocol(asyncio.Protocol):
    """
    This class provides a basic HTTP implementation of the sanic framework.
    """

    __slots__ = (
        # app
        "app",
        # event loop, connection
        "loop",
        "transport",
        "connections",
        "signal",
        "conn_info",
        # request params
        "parser",
        "request",
        "url",
        "headers",
        # request config
        "request_handler",
        "request_timeout",
        "response_timeout",
        "keep_alive_timeout",
        "request_max_size",
        "request_buffer_queue_size",
        "request_class",
        "is_request_stream",
        "error_handler",
        # enable or disable access log purpose
        "access_log",
        # connection management
        "_total_request_size",
        "_request_timeout_handler",
        "_response_timeout_handler",
        "_keep_alive_timeout_handler",
        "_last_request_time",
        "_last_response_time",
        "_is_stream_handler",
        "_not_paused",
        "_request_handler_task",
        "_request_stream_task",
        "_keep_alive",
        "_header_fragment",
        "state",
        "_unix",
        "_body_chunks",
    )

    def __init__(
        self,
        *,
        loop,
        app,
        signal=Signal(),
        connections=None,
        state=None,
        unix=None,
        **kwargs,
    ):
        asyncio.set_event_loop(loop)
        self.loop = loop
        deprecated_loop = self.loop if sys.version_info < (3, 7) else None
        self.app = app
        self.transport = None
        self.conn_info = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.signal = signal
        self.access_log = self.app.config.ACCESS_LOG
        self.connections = connections if connections is not None else set()
        self.request_handler = self.app.handle_request
        self.error_handler = self.app.error_handler
        self.request_timeout = self.app.config.REQUEST_TIMEOUT
        self.request_buffer_queue_size = (
            self.app.config.REQUEST_BUFFER_QUEUE_SIZE
        )
        self.response_timeout = self.app.config.RESPONSE_TIMEOUT
        self.keep_alive_timeout = self.app.config.KEEP_ALIVE_TIMEOUT
        self.request_max_size = self.app.config.REQUEST_MAX_SIZE
        self.request_class = self.app.request_class or Request
        self.is_request_stream = self.app.is_request_stream
        self._is_stream_handler = False
        self._not_paused = asyncio.Event(loop=deprecated_loop)
        self._total_request_size = 0
        self._request_timeout_handler = None
        self._response_timeout_handler = None
        self._keep_alive_timeout_handler = None
        self._last_request_time = None
        self._last_response_time = None
        self._request_handler_task = None
        self._request_stream_task = None
        self._keep_alive = self.app.config.KEEP_ALIVE
        self._header_fragment = b""
        self.state = state if state else {}
        if "requests_count" not in self.state:
            self.state["requests_count"] = 0
        self._unix = unix
        self._not_paused.set()
        self._body_chunks = deque()

    @property
    def keep_alive(self):
        """
        Check if the connection needs to be kept alive based on the params
        attached to the `_keep_alive` attribute, :attr:`Signal.stopped`
        and :func:`HttpProtocol.parser.should_keep_alive`

        :return: ``True`` if connection is to be kept alive ``False`` else
        """
        return (
            self._keep_alive
            and not self.signal.stopped
            and self.parser.should_keep_alive()
        )

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections.add(self)
        self._request_timeout_handler = self.loop.call_later(
            self.request_timeout, self.request_timeout_callback
        )
        self.transport = transport
        self.conn_info = ConnInfo(transport, unix=self._unix)
        self._last_request_time = time()

    def connection_lost(self, exc):
        self.connections.discard(self)
        if self._request_handler_task:
            self._request_handler_task.cancel()
        if self._request_stream_task:
            self._request_stream_task.cancel()
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()

    def pause_writing(self):
        self._not_paused.clear()

    def resume_writing(self):
        self._not_paused.set()

    def request_timeout_callback(self):
        # See the docstring in the RequestTimeout exception, to see
        # exactly what this timeout is checking for.
        # Check if elapsed time since request initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = time() - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._request_timeout_handler = self.loop.call_later(
                time_left, self.request_timeout_callback
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            self.write_error(RequestTimeout("Request Timeout"))

    def response_timeout_callback(self):
        # Check if elapsed time since response was initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = time() - self._last_request_time
        if time_elapsed < self.response_timeout:
            time_left = self.response_timeout - time_elapsed
            self._response_timeout_handler = self.loop.call_later(
                time_left, self.response_timeout_callback
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            self.write_error(ServiceUnavailable("Response Timeout"))

    def keep_alive_timeout_callback(self):
        """
        Check if elapsed time since last response exceeds our configured
        maximum keep alive timeout value and if so, close the transport
        pipe and let the response writer handle the error.

        :return: None
        """
        time_elapsed = time() - self._last_response_time
        if time_elapsed < self.keep_alive_timeout:
            time_left = self.keep_alive_timeout - time_elapsed
            self._keep_alive_timeout_handler = self.loop.call_later(
                time_left, self.keep_alive_timeout_callback
            )
        else:
            logger.debug("KeepAlive Timeout. Closing connection.")
            self.transport.close()
            self.transport = None

    # -------------------------------------------- #
    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            self.write_error(PayloadTooLarge("Payload Too Large"))

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = HttpRequestParser(self)

        # requests count
        self.state["requests_count"] = self.state["requests_count"] + 1

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except HttpParserError:
            message = "Bad Request"
            if self.app.debug:
                message += "\n" + traceback.format_exc()
            self.write_error(InvalidUsage(message))

    def on_url(self, url):
        if not self.url:
            self.url = url
        else:
            self.url += url

    def on_header(self, name, value):
        self._header_fragment += name

        if value is not None:
            if (
                self._header_fragment == b"Content-Length"
                and int(value) > self.request_max_size
            ):
                self.write_error(PayloadTooLarge("Payload Too Large"))
            try:
                value = value.decode()
            except UnicodeDecodeError:
                value = value.decode("latin_1")
            self.headers.append(
                (self._header_fragment.decode().casefold(), value)
            )

            self._header_fragment = b""

    def on_headers_complete(self):
        self.request = self.request_class(
            url_bytes=self.url,
            headers=Header(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode(),
            transport=self.transport,
            app=self.app,
        )
        self.request.conn_info = self.conn_info
        # Remove any existing KeepAlive handler here,
        # It will be recreated if required on the new request.
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()
            self._keep_alive_timeout_handler = None

        if self.request.headers.get(EXPECT_HEADER):
            self.expect_handler()

        if self.is_request_stream:
            self._is_stream_handler = self.app.router.is_stream_handler(
                self.request
            )
            if self._is_stream_handler:
                self.request.stream = StreamBuffer(
                    self.request_buffer_queue_size
                )
                self.execute_request_handler()

    def expect_handler(self):
        """
        Handler for Expect Header.
        """
        expect = self.request.headers.get(EXPECT_HEADER)
        if self.request.version == "1.1":
            if expect.lower() == "100-continue":
                self.transport.write(b"HTTP/1.1 100 Continue\r\n\r\n")
            else:
                self.write_error(
                    HeaderExpectationFailed(f"Unknown Expect: {expect}")
                )

    def on_body(self, body):
        if self.is_request_stream and self._is_stream_handler:
            # body chunks can be put into asyncio.Queue out of order if
            # multiple tasks put concurrently and the queue is full in python
            # 3.7. so we should not create more than one task putting into the
            # queue simultaneously.
            self._body_chunks.append(body)
            if (
                not self._request_stream_task
                or self._request_stream_task.done()
            ):
                self._request_stream_task = self.loop.create_task(
                    self.stream_append()
                )
        else:
            self.request.body_push(body)

    async def body_append(self, body):
        if (
            self.request is None
            or self._request_stream_task is None
            or self._request_stream_task.cancelled()
        ):
            return

        if self.request.stream.is_full():
            self.transport.pause_reading()
            await self.request.stream.put(body)
            self.transport.resume_reading()
        else:
            await self.request.stream.put(body)

    async def stream_append(self):
        while self._body_chunks:
            body = self._body_chunks.popleft()
            if self.request:
                if self.request.stream.is_full():
                    self.transport.pause_reading()
                    await self.request.stream.put(body)
                    self.transport.resume_reading()
                else:
                    await self.request.stream.put(body)

    def on_message_complete(self):
        # Entire request (headers and whole body) is received.
        # We can cancel and remove the request timeout handler now.
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
            self._request_timeout_handler = None
        if self.is_request_stream and self._is_stream_handler:
            self._body_chunks.append(None)
            if (
                not self._request_stream_task
                or self._request_stream_task.done()
            ):
                self._request_stream_task = self.loop.create_task(
                    self.stream_append()
                )
            return
        self.request.body_finish()
        self.execute_request_handler()

    def execute_request_handler(self):
        """
        Invoke the request handler defined by the
        :func:`sanic.app.Sanic.handle_request` method

        :return: None
        """
        self._response_timeout_handler = self.loop.call_later(
            self.response_timeout, self.response_timeout_callback
        )
        self._last_request_time = time()
        self._request_handler_task = self.loop.create_task(
            self.request_handler(
                self.request, self.write_response, self.stream_response
            )
        )

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #
    def log_response(self, response):
        """
        Helper method provided to enable the logging of responses in case if
        the :attr:`HttpProtocol.access_log` is enabled.

        :param response: Response generated for the current request

        :type response: :class:`sanic.response.HTTPResponse` or
            :class:`sanic.response.StreamingHTTPResponse`

        :return: None
        """
        if self.access_log:
            extra = {"status": getattr(response, "status", 0)}

            if isinstance(response, HTTPResponse):
                extra["byte"] = len(response.body)
            else:
                extra["byte"] = -1

            extra["host"] = "UNKNOWN"
            if self.request is not None:
                if self.request.ip:
                    extra["host"] = f"{self.request.ip}:{self.request.port}"

                extra["request"] = f"{self.request.method} {self.request.url}"
            else:
                extra["request"] = "nil"

            access_logger.info("", extra=extra)

    def write_response(self, response):
        """
        Writes response content synchronously to the transport.
        """
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None
        try:
            keep_alive = self.keep_alive
            self.transport.write(
                response.output(
                    self.request.version, keep_alive, self.keep_alive_timeout
                )
            )
            self.log_response(response)
        except AttributeError:
            logger.error(
                "Invalid response object for url %s, "
                "Expected Type: HTTPResponse, Actual Type: %s",
                self.url,
                type(response),
            )
            self.write_error(ServerError("Invalid response type"))
        except RuntimeError:
            if self.app.debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(f"Writing response failed, connection closed {e!r}")
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout, self.keep_alive_timeout_callback
                )
                self._last_response_time = time()
                self.cleanup()

    async def drain(self):
        await self._not_paused.wait()

    async def push_data(self, data):
        self.transport.write(data)

    async def stream_response(self, response):
        """
        Streams a response to the client asynchronously. Attaches
        the transport to the response so the response consumer can
        write to the response as needed.
        """
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None

        try:
            keep_alive = self.keep_alive
            response.protocol = self
            await response.stream(
                self.request.version, keep_alive, self.keep_alive_timeout
            )
            self.log_response(response)
        except AttributeError:
            logger.error(
                "Invalid response object for url %s, "
                "Expected Type: HTTPResponse, Actual Type: %s",
                self.url,
                type(response),
            )
            self.write_error(ServerError("Invalid response type"))
        except RuntimeError:
            if self.app.debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(f"Writing response failed, connection closed {e!r}")
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout, self.keep_alive_timeout_callback
                )
                self._last_response_time = time()
                self.cleanup()

    def write_error(self, exception):
        # An error _is_ a response.
        # Don't throw a response timeout, when a response _is_ given.
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None
        response = None
        try:
            response = self.error_handler.response(self.request, exception)
            version = self.request.version if self.request else "1.1"
            self.transport.write(response.output(version))
        except RuntimeError:
            if self.app.debug:
                logger.error(
                    "Connection lost before error written @ %s",
                    self.request.ip if self.request else "Unknown",
                )
        except Exception as e:
            self.bail_out(
                f"Writing error failed, connection closed {e!r}",
                from_error=True,
            )
        finally:
            if self.parser and (
                self.keep_alive or getattr(response, "status", 0) == 408
            ):
                self.log_response(response)
            try:
                self.transport.close()
            except AttributeError:
                logger.debug("Connection lost before server could close it.")

    def bail_out(self, message, from_error=False):
        """
        In case if the transport pipes are closed and the sanic app encounters
        an error while writing data to the transport pipe, we log the error
        with proper details.

        :param message: Error message to display
        :param from_error: If the bail out was invoked while handling an
            exception scenario.

        :type message: str
        :type from_error: bool

        :return: None
        """
        if from_error or self.transport is None or self.transport.is_closing():
            logger.error(
                "Transport closed @ %s and exception "
                "experienced during error handling",
                (
                    self.transport.get_extra_info("peername")
                    if self.transport is not None
                    else "N/A"
                ),
            )
            logger.debug("Exception:", exc_info=True)
        else:
            self.write_error(ServerError(message))
            logger.error(message)

    def cleanup(self):
        """This is called when KeepAlive feature is used,
        it resets the connection in order for it to be able
        to handle receiving another request on the same connection."""
        self.parser = None
        self.request = None
        self.url = None
        self.headers = None
        self._request_handler_task = None
        self._request_stream_task = None
        self._total_request_size = 0
        self._is_stream_handler = False

    def close_if_idle(self):
        """Close the connection if a request is not being sent or received

        :return: boolean - True if closed, false if staying open
        """
        if not self.parser and self.transport is not None:
            self.transport.close()
            return True
        return False

    def close(self):
        """
        Force close the connection.
        """
        if self.transport is not None:
            self.transport.close()
            self.transport = None


def trigger_events(events, loop):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event(loop)
        if isawaitable(result):
            loop.run_until_complete(result)


class AsyncioServer:
    """
    Wraps an asyncio server with functionality that might be useful to
    a user who needs to manage the server lifecycle manually.
    """

    __slots__ = (
        "loop",
        "serve_coro",
        "_after_start",
        "_before_stop",
        "_after_stop",
        "server",
        "connections",
    )

    def __init__(
        self,
        loop,
        serve_coro,
        connections,
        after_start,
        before_stop,
        after_stop,
    ):
        # Note, Sanic already called "before_server_start" events
        # before this helper was even created. So we don't need it here.
        self.loop = loop
        self.serve_coro = serve_coro
        self._after_start = after_start
        self._before_stop = before_stop
        self._after_stop = after_stop
        self.server = None
        self.connections = connections

    def after_start(self):
        """Trigger "after_server_start" events"""
        trigger_events(self._after_start, self.loop)

    def before_stop(self):
        """Trigger "before_server_stop" events"""
        trigger_events(self._before_stop, self.loop)

    def after_stop(self):
        """Trigger "after_server_stop" events"""
        trigger_events(self._after_stop, self.loop)

    def is_serving(self):
        if self.server:
            return self.server.is_serving()
        return False

    def wait_closed(self):
        if self.server:
            return self.server.wait_closed()

    def close(self):
        if self.server:
            self.server.close()
            coro = self.wait_closed()
            task = asyncio.ensure_future(coro, loop=self.loop)
            return task

    def start_serving(self):
        if self.server:
            try:
                return self.server.start_serving()
            except AttributeError:
                raise NotImplementedError(
                    "server.start_serving not available in this version "
                    "of asyncio or uvloop."
                )

    def serve_forever(self):
        if self.server:
            try:
                return self.server.serve_forever()
            except AttributeError:
                raise NotImplementedError(
                    "server.serve_forever not available in this version "
                    "of asyncio or uvloop."
                )

    def __await__(self):
        """Starts the asyncio server, returns AsyncServerCoro"""
        task = asyncio.ensure_future(self.serve_coro)
        while not task.done():
            yield
        self.server = task.result()
        return self


def serve(
    host,
    port,
    app,
    before_start=None,
    after_start=None,
    before_stop=None,
    after_stop=None,
    ssl=None,
    sock=None,
    unix=None,
    reuse_port=False,
    loop=None,
    protocol=HttpProtocol,
    backlog=100,
    register_sys_signals=True,
    run_multiple=False,
    run_async=False,
    connections=None,
    signal=Signal(),
    state=None,
    asyncio_server_kwargs=None,
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
    if not run_async:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if app.debug:
        loop.set_debug(app.debug)

    app.asgi = False

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
    # UNIX sockets are always bound by us (to preserve semantics between modes)
    if unix:
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

    if run_async:
        return AsyncioServer(
            loop=loop,
            serve_coro=server_coroutine,
            connections=connections,
            after_start=after_start,
            before_stop=before_stop,
            after_stop=after_stop,
        )

    trigger_events(before_start, loop)

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except BaseException:
        logger.exception("Unable to start server")
        return

    trigger_events(after_start, loop)

    # Ignore SIGINT when run_multiple
    if run_multiple:
        signal_func(SIGINT, SIG_IGN)

    # Register signals for graceful termination
    if register_sys_signals:
        if OS_IS_WINDOWS:
            ctrlc_workaround_for_windows(app)
        else:
            for _signal in [SIGTERM] if run_multiple else [SIGINT, SIGTERM]:
                loop.add_signal_handler(_signal, app.stop)
    pid = os.getpid()
    try:
        logger.info("Starting worker [%s]", pid)
        loop.run_forever()
    finally:
        logger.info("Stopping worker [%s]", pid)

        # Run the on_stop function if provided
        trigger_events(before_stop, loop)

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
        start_shutdown = 0
        while connections and (start_shutdown < graceful):
            loop.run_until_complete(asyncio.sleep(0.1))
            start_shutdown = start_shutdown + 0.1

        # Force close non-idle connection after waiting for
        # graceful_shutdown_timeout
        coros = []
        for conn in connections:
            if hasattr(conn, "websocket") and conn.websocket:
                coros.append(conn.websocket.close_connection())
            else:
                conn.close()

        _shutdown = asyncio.gather(*coros)
        loop.run_until_complete(_shutdown)

        trigger_events(after_stop, loop)

        loop.close()
        remove_unix_socket(unix)


def _build_protocol_kwargs(
    protocol: Type[HttpProtocol], config: Config
) -> Dict[str, Union[int, float]]:
    if hasattr(protocol, "websocket_handshake"):
        return {
            "websocket_max_size": config.WEBSOCKET_MAX_SIZE,
            "websocket_max_queue": config.WEBSOCKET_MAX_QUEUE,
            "websocket_read_limit": config.WEBSOCKET_READ_LIMIT,
            "websocket_write_limit": config.WEBSOCKET_WRITE_LIMIT,
            "websocket_ping_timeout": config.WEBSOCKET_PING_TIMEOUT,
            "websocket_ping_interval": config.WEBSOCKET_PING_INTERVAL,
        }
    return {}


def bind_socket(host: str, port: int, *, backlog=100) -> socket.socket:
    """Create TCP server socket.
    :param host: IPv4, IPv6 or hostname may be specified
    :param port: TCP port number
    :param backlog: Maximum number of connections to queue
    :return: socket.socket object
    """
    try:  # IP address: family must be specified for IPv6 at least
        ip = ip_address(host)
        host = str(ip)
        sock = socket.socket(
            socket.AF_INET6 if ip.version == 6 else socket.AF_INET
        )
    except ValueError:  # Hostname, may become AF_INET or AF_INET6
        sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(backlog)
    return sock


def bind_unix_socket(path: str, *, mode=0o666, backlog=100) -> socket.socket:
    """Create unix socket.
    :param path: filesystem path
    :param backlog: Maximum number of connections to queue
    :return: socket.socket object
    """
    """Open or atomically replace existing socket with zero downtime."""
    # Sanitise and pre-verify socket path
    path = os.path.abspath(path)
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Socket folder does not exist: {folder}")
    try:
        if not stat.S_ISSOCK(os.stat(path, follow_symlinks=False).st_mode):
            raise FileExistsError(f"Existing file is not a socket: {path}")
    except FileNotFoundError:
        pass
    # Create new socket with a random temporary name
    tmp_path = f"{path}.{secrets.token_urlsafe()}"
    sock = socket.socket(socket.AF_UNIX)
    try:
        # Critical section begins (filename races)
        sock.bind(tmp_path)
        try:
            os.chmod(tmp_path, mode)
            # Start listening before rename to avoid connection failures
            sock.listen(backlog)
            os.rename(tmp_path, path)
        except:  # noqa: E722
            try:
                os.unlink(tmp_path)
            finally:
                raise
    except:  # noqa: E722
        try:
            sock.close()
        finally:
            raise
    return sock


def remove_unix_socket(path: str) -> None:
    """Remove dead unix socket during server exit."""
    if not path:
        return
    try:
        if stat.S_ISSOCK(os.stat(path, follow_symlinks=False).st_mode):
            # Is it actually dead (doesn't belong to a new server instance)?
            with socket.socket(socket.AF_UNIX) as testsock:
                try:
                    testsock.connect(path)
                except ConnectionRefusedError:
                    os.unlink(path)
    except FileNotFoundError:
        pass


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
        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        for process in processes:
            os.kill(process.pid, SIGTERM)

    signal_func(SIGINT, lambda s, f: sig_handler(s, f))
    signal_func(SIGTERM, lambda s, f: sig_handler(s, f))
    mp = multiprocessing.get_context("fork")

    for _ in range(workers):
        process = mp.Process(target=serve, kwargs=server_settings)
        process.daemon = True
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    # the above processes will block this until they're stopped
    for process in processes:
        process.terminate()

    sock.close()
    remove_unix_socket(unix)
