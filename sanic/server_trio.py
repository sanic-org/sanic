import trio
import os
import socket
import stat
import traceback

from functools import partial
from inspect import isawaitable
from ipaddress import ip_address
from multiprocessing import Process
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import time

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError
from multidict import CIMultiDict

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


class HttpProtocol:
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
        "router",
        "error_handler",
        # enable or disable access log purpose
        "access_log",
        # connection management
        "_total_request_size",
        "_last_request_time",
        "_last_response_time",
        "_is_stream_handler",
        "_keep_alive",
        "_header_fragment",
        "state",
        "_debug",
        "nursery",
    )

    def __init__(
        self,
        *,
        loop,
        app,
        request_handler,
        error_handler,
        signal=Signal(),
        connections=None,
        request_timeout=60,
        response_timeout=60,
        keep_alive_timeout=5,
        request_max_size=None,
        request_buffer_queue_size=100,
        request_class=None,
        access_log=True,
        keep_alive=True,
        is_request_stream=False,
        router=None,
        state=None,
        debug=False,
        **kwargs
    ):
        self.app = app
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.router = router
        self.signal = signal
        self.access_log = access_log
        self.connections = connections or {}
        self.request_handler = request_handler
        self.error_handler = error_handler
        self.request_timeout = request_timeout
        self.request_buffer_queue_size = request_buffer_queue_size
        self.response_timeout = response_timeout
        self.keep_alive_timeout = keep_alive_timeout
        self.request_max_size = request_max_size
        self.request_class = request_class or Request
        self.is_request_stream = is_request_stream
        self._is_stream_handler = False
        self._total_request_size = 0
        self._last_request_time = None
        self._last_response_time = None
        self._keep_alive = keep_alive
        self._header_fragment = b""
        self.state = state or {}
        if "requests_count" not in self.state:
            self.state["requests_count"] = 0
        self._debug = debug

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
            and self.parser
            and self.parser.should_keep_alive()
        )

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
            if self._debug:
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
            headers=CIMultiDict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode(),
            transport=self.transport,
            app=self.app,
        )

        if self.request.headers.get(EXPECT_HEADER):
            self.expect_handler()

        if self.is_request_stream:
            self._is_stream_handler = self.router.is_stream_handler(
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
                    HeaderExpectationFailed(
                        "Unknown Expect: {expect}".format(expect=expect)
                    )
                )

    def on_body(self, body):
        if self.is_request_stream and self._is_stream_handler:
            self.nursery.start_soon(self.body_append, body)
        else:
            self.request.body_push(body)

    async def body_append(self, body):
        if self.request.stream.is_full():
            self.transport.pause_reading()
            await self.request.stream.put(body)
            self.transport.resume_reading()
        else:
            await self.request.stream.put(body)

    def on_message_complete(self):
        # Entire request (headers and whole body) is received.
        if self.is_request_stream and self._is_stream_handler:
            self._request_stream_task = self.loop.create_task(
                self.request.stream.put(None)
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
        self.nursery.cancel_scope.deadline = trio.current_time() + self.request_timeout
        self._last_request_time = time()
        self.nursery.start_soon(
            self.request_handler, self.request, self.write_response, self.stream_response
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
                    extra["host"] = "{0}:{1}".format(
                        self.request.ip, self.request.port
                    )

                extra["request"] = "{0} {1}".format(
                    self.request.method, self.request.url
                )
            else:
                extra["request"] = "nil"

            access_logger.info("", extra=extra)

    async def write_response(self, response):
        """
        Writes response content synchronously to the transport.
        """
        keep_alive = self.keep_alive
        try:
            await self.transport.send_all(
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
            if self._debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(repr(e))
            )
        finally:
            if not keep_alive:
                self.nursery.cancel_scope.cancel()
            else:
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
            if self._debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(repr(e))
            )
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self.nursery.cancel_scope.deadline = trio.current_time() + self.keep_alive_timeout
                self._last_response_time = time()
                self.cleanup()

    def write_error(self, exception):
        response = None
        try:
            response = self.error_handler.response(self.request, exception)
            version = self.request.version if self.request else "1.1"
            self.transport.send_all(response.output(version))
        except RuntimeError:
            if self._debug:
                logger.error(
                    "Connection lost before error written @ %s",
                    self.request.ip if self.request else "Unknown",
                )
        except Exception as e:
            self.bail_out(
                "Writing error failed, connection closed {}".format(repr(e)),
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
        self._total_request_size = 0
        self._is_stream_handler = False

    async def run(self, stream):
        async with stream, trio.open_nursery() as self.nursery:
            stream.get_extra_info = lambda option: "fake address"
            self.transport = stream
            self.nursery.cancel_scope.deadline = trio.current_time() + self.request_timeout
            async for data in stream:
                self.data_received(data)

async def trigger_events(events):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event()
        if isawaitable(result):
            await result

def bind_socket(host: str, port: int) -> socket:
    """Create socket and bind to host.
    :param host: IPv4, IPv6, hostname or unix:/tmp/socket may be specified
    :param port: IP port number, 0 or None for UNIX sockets
    :return: socket.socket object
    """
    if host.lower().startswith("unix:"):  # UNIX socket
        name = host[5:]
        sock = socket.socket(socket.AF_UNIX)
        if os.path.exists(name) and stat.S_ISSOCK(os.stat(name).st_mode):
            os.unlink(name)
        oldmask = os.umask(0o111)
        try:
            sock.bind(name)
        finally:
            os.umask(oldmask)
        return sock
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
    return sock


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

    # Handling when custom socket is not provided.
    if server_settings.get("sock") is None:
        sock = bind_socket(server_settings["host"], server_settings["port"])
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

    for _ in range(workers):
        process = Process(target=serve, kwargs=server_settings)
        process.daemon = True
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    # the above processes will block this until they're stopped
    for process in processes:
        process.terminate()

    sock = server_settings.get("sock")
    sockname = sock.getsockname()
    sock.close()
    # Remove UNIX socket
    if isinstance(sockname, str):
        os.unlink(sockname)

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
    reuse_port=False,
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
            loop=None,
        )
        await proto.run(stream)

    app.asgi = False
    assert not (run_async or run_multiple or asyncio_server_kwargs or loop), "Not implemented"

    server = partial(
        runserver,
        host,
        port,
        before_start,
        after_start,
        before_stop,
        after_stop,
        ssl,
        sock,
        reuse_port,
        backlog,
        register_sys_signals,
        run_multiple,
        graceful_shutdown_timeout,
        handle_connection
    )
    return server() if run_async else trio.run(server)

async def runserver(
    host,
    port,
    before_start,
    after_start,
    before_stop,
    after_stop,
    ssl,
    sock,
    reuse_port,
    backlog,
    register_sys_signals,
    run_multiple,
    graceful_shutdown_timeout,
    handle_connection
):
    async with trio.open_nursery() as main_nursery:
        await trigger_events(before_start)
        # open_tcp_listeners cannot bind UNIX sockets, so do it here
        if host and host.startswith("unix:"):
            unix_socket_name = host[5:]
            sock, host, port = bind_socket(host, port), None, None
        else:
            unix_socket_name = None
        try:
            listeners = await trio.open_tcp_listeners(
                host=host, port=port or 8000, backlog=backlog
            )
        except Exception:
            logger.exception("Unable to start server")
            return
        await trigger_events(after_start)
        pid = os.getpid()
        logger.info("Starting worker [%s]", pid)
        # Accept connections until a signal is received, then perform graceful exit
        async with trio.open_nursery() as acceptor:
            acceptor.start_soon(partial(
                trio.serve_listeners,
                handle_connection,
                listeners,
                handler_nursery=main_nursery
            ))
            with trio.open_signal_receiver(SIGINT, SIGTERM) as sigiter:
                async for _ in sigiter:
                    acceptor.cancel_scope.cancel()
                    break
        logger.info("Stopping worker [%s]", pid)
        await trigger_events(before_stop)
        if unix_socket_name:
            os.unlink(unix_socket_name)
        main_nursery.cancel_scope.deadline = trio.current_time() + graceful_shutdown_timeout
    await trigger_events(after_stop)
