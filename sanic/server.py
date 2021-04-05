from __future__ import annotations

from ssl import SSLContext
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Type,
    Union,
)

from sanic.models.handler_types import ListenerType


if TYPE_CHECKING:
    from sanic.app import Sanic

import asyncio
import multiprocessing
import os
import secrets
import socket
import stat

from asyncio import CancelledError
from asyncio.transports import Transport
from functools import partial
from inspect import isawaitable
from ipaddress import ip_address
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import monotonic as current_time

from sanic.compat import OS_IS_WINDOWS, ctrlc_workaround_for_windows
from sanic.config import Config
from sanic.exceptions import RequestTimeout, ServiceUnavailable
from sanic.http import Http, Stage
from sanic.log import logger
from sanic.models.protocol_types import TransportProtocol
from sanic.request import Request


try:
    import uvloop  # type: ignore

    if not isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class Signal:
    stopped = False


class ConnInfo:
    """
    Local and remote addresses and SSL status info.
    """

    __slots__ = (
        "client_port",
        "client",
        "ctx",
        "peername",
        "server_port",
        "server",
        "sockname",
        "ssl",
    )

    def __init__(self, transport: TransportProtocol, unix=None):
        self.ctx = SimpleNamespace()
        self.peername = None
        self.server = self.client = ""
        self.server_port = self.client_port = 0
        self.sockname = addr = transport.get_extra_info("sockname")
        self.ssl: bool = bool(transport.get_extra_info("sslcontext"))

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
        "ctx",
        # request params
        "request",
        # request config
        "request_handler",
        "request_timeout",
        "response_timeout",
        "keep_alive_timeout",
        "request_max_size",
        "request_buffer_queue_size",
        "request_class",
        "error_handler",
        # enable or disable access log purpose
        "access_log",
        # connection management
        "state",
        "url",
        "_handler_task",
        "_can_write",
        "_data_received",
        "_time",
        "_task",
        "_http",
        "_exception",
        "recv_buffer",
        "_unix",
    )

    def __init__(
        self,
        *,
        loop,
        app: Sanic,
        signal=None,
        connections=None,
        state=None,
        unix=None,
        **kwargs,
    ):
        asyncio.set_event_loop(loop)
        self.loop = loop
        self.app: Sanic = app
        self.url = None
        self.transport: Optional[Transport] = None
        self.conn_info: Optional[ConnInfo] = None
        self.request: Optional[Request] = None
        self.signal = signal or Signal()
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
        self.state = state if state else {}
        if "requests_count" not in self.state:
            self.state["requests_count"] = 0
        self._data_received = asyncio.Event()
        self._can_write = asyncio.Event()
        self._can_write.set()
        self._exception = None
        self._unix = unix

    def _setup_connection(self):
        self._http = Http(self)
        self._time = current_time()
        self.check_timeouts()

    async def connection_task(self):
        """
        Run a HTTP connection.

        Timeouts and some additional error handling occur here, while most of
        everything else happens in class Http or in code called from there.
        """
        try:
            self._setup_connection()
            await self._http.http1()
        except CancelledError:
            pass
        except Exception:
            logger.exception("protocol.connection_task uncaught")
        finally:
            if self.app.debug and self._http:
                ip = self.transport.get_extra_info("peername")
                logger.error(
                    "Connection lost before response written"
                    f" @ {ip} {self._http.request}"
                )
            self._http = None
            self._task = None
            try:
                self.close()
            except BaseException:
                logger.exception("Closing failed")

    async def receive_more(self):
        """
        Wait until more data is received into the Server protocol's buffer
        """
        self.transport.resume_reading()
        self._data_received.clear()
        await self._data_received.wait()

    def check_timeouts(self):
        """
        Runs itself periodically to enforce any expired timeouts.
        """
        try:
            if not self._task:
                return
            duration = current_time() - self._time
            stage = self._http.stage
            if stage is Stage.IDLE and duration > self.keep_alive_timeout:
                logger.debug("KeepAlive Timeout. Closing connection.")
            elif stage is Stage.REQUEST and duration > self.request_timeout:
                logger.debug("Request Timeout. Closing connection.")
                self._http.exception = RequestTimeout("Request Timeout")
            elif stage is Stage.HANDLER and self._http.upgrade_websocket:
                logger.debug("Handling websocket. Timeouts disabled.")
                return
            elif (
                stage in (Stage.HANDLER, Stage.RESPONSE, Stage.FAILED)
                and duration > self.response_timeout
            ):
                logger.debug("Response Timeout. Closing connection.")
                self._http.exception = ServiceUnavailable("Response Timeout")
            else:
                interval = (
                    min(
                        self.keep_alive_timeout,
                        self.request_timeout,
                        self.response_timeout,
                    )
                    / 2
                )
                self.loop.call_later(max(0.1, interval), self.check_timeouts)
                return
            self._task.cancel()
        except Exception:
            logger.exception("protocol.check_timeouts")

    async def send(self, data):
        """
        Writes data with backpressure control.
        """
        await self._can_write.wait()
        if self.transport.is_closing():
            raise CancelledError
        self.transport.write(data)
        self._time = current_time()

    def close_if_idle(self) -> bool:
        """
        Close the connection if a request is not being sent or received

        :return: boolean - True if closed, false if staying open
        """
        if self._http is None or self._http.stage is Stage.IDLE:
            self.close()
            return True
        return False

    def close(self):
        """
        Force close the connection.
        """
        # Cause a call to connection_lost where further cleanup occurs
        if self.transport:
            self.transport.close()
            self.transport = None

    # -------------------------------------------- #
    # Only asyncio.Protocol callbacks below this
    # -------------------------------------------- #

    def connection_made(self, transport):
        try:
            # TODO: Benchmark to find suitable write buffer limits
            transport.set_write_buffer_limits(low=16384, high=65536)
            self.connections.add(self)
            self.transport = transport
            self._task = self.loop.create_task(self.connection_task())
            self.recv_buffer = bytearray()
            self.conn_info = ConnInfo(self.transport, unix=self._unix)
        except Exception:
            logger.exception("protocol.connect_made")

    def connection_lost(self, exc):
        try:
            self.connections.discard(self)
            self.resume_writing()
            if self._task:
                self._task.cancel()
        except Exception:
            logger.exception("protocol.connection_lost")

    def pause_writing(self):
        self._can_write.clear()

    def resume_writing(self):
        self._can_write.set()

    def data_received(self, data: bytes):
        try:
            self._time = current_time()
            if not data:
                return self.close()
            self.recv_buffer += data

            if (
                len(self.recv_buffer) > self.app.config.REQUEST_BUFFER_SIZE
                and self.transport
            ):
                self.transport.pause_reading()

            if self._data_received:
                self._data_received.set()
        except Exception:
            logger.exception("protocol.data_received")


def trigger_events(events: Optional[Iterable[Callable[..., Any]]], loop):
    """
    Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    if events:
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
        after_start: Optional[Iterable[ListenerType]],
        before_stop: Optional[Iterable[ListenerType]],
        after_stop: Optional[Iterable[ListenerType]],
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
        """
        Trigger "after_server_start" events
        """
        trigger_events(self._after_start, self.loop)

    def before_stop(self):
        """
        Trigger "before_server_stop" events
        """
        trigger_events(self._before_stop, self.loop)

    def after_stop(self):
        """
        Trigger "after_server_stop" events
        """
        trigger_events(self._after_stop, self.loop)

    def is_serving(self) -> bool:
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
        """
        Starts the asyncio server, returns AsyncServerCoro
        """
        task = asyncio.ensure_future(self.serve_coro)
        while not task.done():
            yield
        self.server = task.result()
        return self


def serve(
    host,
    port,
    app,
    before_start: Optional[Iterable[ListenerType]] = None,
    after_start: Optional[Iterable[ListenerType]] = None,
    before_stop: Optional[Iterable[ListenerType]] = None,
    after_stop: Optional[Iterable[ListenerType]] = None,
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
        start_shutdown: float = 0
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

        remove_unix_socket(unix)


def _build_protocol_kwargs(
    protocol: Type[asyncio.Protocol], config: Config
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


def remove_unix_socket(path: Optional[str]) -> None:
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

    trigger_events(main_stop, loop)

    sock.close()
    loop.close()
    remove_unix_socket(unix)
