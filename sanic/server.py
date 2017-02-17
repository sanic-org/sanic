import asyncio
import os
import traceback
import warnings
from functools import partial
from inspect import isawaitable
from multiprocessing import Process, Event
from os import set_inheritable
from signal import SIGTERM, SIGINT
from signal import signal as signal_func
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from time import time

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError

try:
    import uvloop as async_loop
except ImportError:
    async_loop = asyncio

from sanic.log import log
from sanic.request import Request
from sanic.exceptions import (
    RequestTimeout, PayloadTooLarge, InvalidUsage, ServerError)

current_time = None


class Signal:
    stopped = False


class CIDict(dict):
    """Case Insensitive dict where all keys are converted to lowercase
    This does not maintain the inputted case when calling items() or keys()
    in favor of speed, since headers are case insensitive
    """

    def get(self, key, default=None):
        return super().get(key.casefold(), default)

    def __getitem__(self, key):
        return super().__getitem__(key.casefold())

    def __setitem__(self, key, value):
        return super().__setitem__(key.casefold(), value)

    def __contains__(self, key):
        return super().__contains__(key.casefold())


class HttpProtocol(asyncio.Protocol):
    __slots__ = (
        # event loop, connection
        'loop', 'transport', 'connections', 'signal',
        # request params
        'parser', 'request', 'url', 'headers',
        # request config
        'request_handler', 'request_timeout', 'request_max_size',
        # connection management
        '_total_request_size', '_timeout_handler', '_last_communication_time')

    def __init__(self, *, loop, request_handler, error_handler,
                 signal=Signal(), connections=set(), request_timeout=60,
                 request_max_size=None):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.signal = signal
        self.connections = connections
        self.request_handler = request_handler
        self.error_handler = error_handler
        self.request_timeout = request_timeout
        self.request_max_size = request_max_size
        self._total_request_size = 0
        self._timeout_handler = None
        self._last_request_time = None
        self._request_handler_task = None

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections.add(self)
        self._timeout_handler = self.loop.call_later(
            self.request_timeout, self.connection_timeout)
        self.transport = transport
        self._last_request_time = current_time

    def connection_lost(self, exc):
        self.connections.discard(self)
        self._timeout_handler.cancel()

    def connection_timeout(self):
        # Check if
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._timeout_handler = (
                self.loop.call_later(time_left, self.connection_timeout))
        else:
            if self._request_handler_task:
                self._request_handler_task.cancel()
            exception = RequestTimeout('Request Timeout')
            self.write_error(exception)

    # -------------------------------------------- #
    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            exception = PayloadTooLarge('Payload Too Large')
            self.write_error(exception)

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = HttpRequestParser(self)

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except HttpParserError:
            exception = InvalidUsage('Bad Request')
            self.write_error(exception)

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        if name == b'Content-Length' and int(value) > self.request_max_size:
            exception = PayloadTooLarge('Payload Too Large')
            self.write_error(exception)

        self.headers.append((name.decode().casefold(), value.decode()))

    def on_headers_complete(self):
        self.request = Request(
            url_bytes=self.url,
            headers=CIDict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode(),
            transport=self.transport
        )

    def on_body(self, body):
        self.request.body.append(body)

    def on_message_complete(self):
        if self.request.body:
            self.request.body = b''.join(self.request.body)
        self._request_handler_task = self.loop.create_task(
            self.request_handler(self.request, self.write_response))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    def write_response(self, response):
        keep_alive = (
            self.parser.should_keep_alive() and not self.signal.stopped)
        try:
            self.transport.write(
                response.output(
                    self.request.version, keep_alive, self.request_timeout))
        except AttributeError:
            log.error(
                ('Invalid response object for url {}, '
                 'Expected Type: HTTPResponse, Actual Type: {}').format(
                    self.url, type(response)))
            self.write_error(ServerError('Invalid response type'))
        except RuntimeError:
            log.error(
                'Connection lost before response written @ {}'.format(
                    self.request.ip))
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(
                    repr(e)))
        finally:
            if not keep_alive:
                self.transport.close()
            else:
                # Record that we received data
                self._last_request_time = current_time
                self.cleanup()

    def write_error(self, exception):
        try:
            response = self.error_handler.response(self.request, exception)
            version = self.request.version if self.request else '1.1'
            self.transport.write(response.output(version))
        except RuntimeError:
            log.error(
                'Connection lost before error written @ {}'.format(
                    self.request.ip if self.request else 'Unknown'))
        except Exception as e:
            self.bail_out(
                "Writing error failed, connection closed {}".format(repr(e)),
                from_error=True)
        finally:
            self.transport.close()

    def bail_out(self, message, from_error=False):
        if from_error and self.transport.is_closing():
            log.error(
                ("Transport closed @ {} and exception "
                 "experienced during error handling").format(
                    self.transport.get_extra_info('peername')))
            log.debug(
                'Exception:\n{}'.format(traceback.format_exc()))
        else:
            exception = ServerError(message)
            self.write_error(exception)
            log.error(message)

    def cleanup(self):
        self.parser = None
        self.request = None
        self.url = None
        self.headers = None
        self._request_handler_task = None
        self._total_request_size = 0

    def close_if_idle(self):
        """Close the connection if a request is not being sent or received

        :return: boolean - True if closed, false if staying open
        """
        if not self.parser:
            self.transport.close()
            return True
        return False


def update_current_time(loop):
    """Cache the current time, since it is needed at the end of every
    keep-alive request to update the request timeout time

    :param loop:
    :return:
    """
    global current_time
    current_time = time()
    loop.call_later(1, partial(update_current_time, loop))


def trigger_events(events, loop):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event(loop)
        if isawaitable(result):
            loop.run_until_complete(result)


def serve(host, port, request_handler, error_handler, before_start=None,
          after_start=None, before_stop=None, after_stop=None, debug=False,
          request_timeout=60, ssl=None, sock=None, request_max_size=None,
          reuse_port=False, loop=None, protocol=HttpProtocol, backlog=100,
          register_sys_signals=True, run_async=False):
    """Start asynchronous HTTP Server on an individual process.

    :param host: Address to host on
    :param port: Port to host on
    :param request_handler: Sanic request handler with middleware
    :param error_handler: Sanic error handler with middleware
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
    :param debug: enables debug output (slows server)
    :param request_timeout: time in seconds
    :param ssl: SSLContext
    :param sock: Socket for the server to accept connections from
    :param request_max_size: size in bytes, `None` for no limit
    :param reuse_port: `True` for multiple workers
    :param loop: asyncio compatible event loop
    :param protocol: subclass of asyncio protocol class
    :return: Nothing
    """
    if not run_async:
        loop = async_loop.new_event_loop()
        asyncio.set_event_loop(loop)

    if debug:
        loop.set_debug(debug)

    trigger_events(before_start, loop)

    connections = set()
    signal = Signal()
    server = partial(
        protocol,
        loop=loop,
        connections=connections,
        signal=signal,
        request_handler=request_handler,
        error_handler=error_handler,
        request_timeout=request_timeout,
        request_max_size=request_max_size,
    )

    server_coroutine = loop.create_server(
        server,
        host,
        port,
        ssl=ssl,
        reuse_port=reuse_port,
        sock=sock,
        backlog=backlog
    )
    # Instead of pulling time at the end of every request,
    # pull it once per minute
    loop.call_soon(partial(update_current_time, loop))

    if run_async:
        return server_coroutine

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except:
        log.exception("Unable to start server")
        return

    trigger_events(after_start, loop)

    # Register signals for graceful termination
    if register_sys_signals:
        for _signal in (SIGINT, SIGTERM):
            try:
                loop.add_signal_handler(_signal, loop.stop)
            except NotImplementedError:
                log.warn('Sanic tried to use loop.add_signal_handler but it is'
                         ' not implemented on this platform.')
    pid = os.getpid()
    try:
        log.info('Starting worker [{}]'.format(pid))
        loop.run_forever()
    finally:
        log.info("Stopping worker [{}]".format(pid))

        # Run the on_stop function if provided
        trigger_events(before_stop, loop)

        # Wait for event loop to finish and all connections to drain
        http_server.close()
        loop.run_until_complete(http_server.wait_closed())

        # Complete all tasks on the loop
        signal.stopped = True
        for connection in connections:
            connection.close_if_idle()

        while connections:
            loop.run_until_complete(asyncio.sleep(0.1))

        trigger_events(after_stop, loop)

        loop.close()


def serve_multiple(server_settings, workers, stop_event=None):
    """Start multiple server processes simultaneously.  Stop on interrupt
    and terminate signals, and drain connections when complete.

    :param server_settings: kw arguments to be passed to the serve function
    :param workers: number of workers to launch
    :param stop_event: if provided, is used as a stop signal
    :return:
    """
    if server_settings.get('loop', None) is not None:
        if server_settings.get('debug', False):
            warnings.simplefilter('default')
        warnings.warn("Passing a loop will be deprecated in version 0.4.0"
                      " https://github.com/channelcat/sanic/pull/335"
                      " has more information.", DeprecationWarning)
    server_settings['reuse_port'] = True

    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((server_settings['host'], server_settings['port']))
    set_inheritable(sock.fileno(), True)
    server_settings['sock'] = sock
    server_settings['host'] = None
    server_settings['port'] = None

    if stop_event is None:
        stop_event = Event()

    signal_func(SIGINT, lambda s, f: stop_event.set())
    signal_func(SIGTERM, lambda s, f: stop_event.set())

    processes = []
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
    sock.close()

    asyncio.get_event_loop().stop()
