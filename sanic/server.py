import asyncio
import os
import traceback
from functools import partial
from inspect import isawaitable
from multiprocessing import Process
from signal import (
    SIGTERM, SIGINT, SIG_IGN,
    signal as signal_func,
    Signals
)
from socket import (
    socket,
    SOL_SOCKET,
    SO_REUSEADDR,
)
from time import time

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from sanic.log import logger, access_logger
from sanic.response import HTTPResponse
from sanic.request import Request
from sanic.exceptions import (
    RequestTimeout, PayloadTooLarge, InvalidUsage, ServerError,
    ServiceUnavailable)

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
        'request_handler', 'request_timeout', 'response_timeout',
        'keep_alive_timeout', 'request_max_size', 'request_class',
        'is_request_stream', 'router',
        # enable or disable access log purpose
        'access_log',
        # connection management
        '_total_request_size', '_request_timeout_handler',
        '_response_timeout_handler', '_keep_alive_timeout_handler',
        '_last_request_time', '_last_response_time', '_is_stream_handler')

    def __init__(self, *, loop, request_handler, error_handler,
                 signal=Signal(), connections=set(), request_timeout=60,
                 response_timeout=60, keep_alive_timeout=5,
                 request_max_size=None, request_class=None, access_log=True,
                 keep_alive=True, is_request_stream=False, router=None,
                 state=None, debug=False, **kwargs):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.router = router
        self.signal = signal
        self.access_log = access_log
        self.connections = connections
        self.request_handler = request_handler
        self.error_handler = error_handler
        self.request_timeout = request_timeout
        self.response_timeout = response_timeout
        self.keep_alive_timeout = keep_alive_timeout
        self.request_max_size = request_max_size
        self.request_class = request_class or Request
        self.is_request_stream = is_request_stream
        self._is_stream_handler = False
        self._total_request_size = 0
        self._request_timeout_handler = None
        self._response_timeout_handler = None
        self._keep_alive_timeout_handler = None
        self._last_request_time = None
        self._last_response_time = None
        self._request_handler_task = None
        self._request_stream_task = None
        self._keep_alive = keep_alive
        self._header_fragment = b''
        self.state = state if state else {}
        if 'requests_count' not in self.state:
            self.state['requests_count'] = 0
        self._debug = debug

    @property
    def keep_alive(self):
        return (
            self._keep_alive and
            not self.signal.stopped and
            self.parser.should_keep_alive())

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections.add(self)
        self._request_timeout_handler = self.loop.call_later(
            self.request_timeout, self.request_timeout_callback)
        self.transport = transport
        self._last_request_time = current_time

    def connection_lost(self, exc):
        self.connections.discard(self)
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()

    def request_timeout_callback(self):
        # See the docstring in the RequestTimeout exception, to see
        # exactly what this timeout is checking for.
        # Check if elapsed time since request initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._request_timeout_handler = (
                self.loop.call_later(time_left,
                                     self.request_timeout_callback)
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            try:
                raise RequestTimeout('Request Timeout')
            except RequestTimeout as exception:
                self.write_error(exception)

    def response_timeout_callback(self):
        # Check if elapsed time since response was initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.response_timeout:
            time_left = self.response_timeout - time_elapsed
            self._response_timeout_handler = (
                self.loop.call_later(time_left,
                                     self.response_timeout_callback)
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            try:
                raise ServiceUnavailable('Response Timeout')
            except ServiceUnavailable as exception:
                self.write_error(exception)

    def keep_alive_timeout_callback(self):
        # Check if elapsed time since last response exceeds our configured
        # maximum keep alive timeout value
        time_elapsed = current_time - self._last_response_time
        if time_elapsed < self.keep_alive_timeout:
            time_left = self.keep_alive_timeout - time_elapsed
            self._keep_alive_timeout_handler = (
                self.loop.call_later(time_left,
                                     self.keep_alive_timeout_callback)
            )
        else:
            logger.debug('KeepAlive Timeout. Closing connection.')
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
            exception = PayloadTooLarge('Payload Too Large')
            self.write_error(exception)

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = HttpRequestParser(self)

        # requests count
        self.state['requests_count'] = self.state['requests_count'] + 1

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except HttpParserError:
            message = 'Bad Request'
            if self._debug:
                message += '\n' + traceback.format_exc()
            exception = InvalidUsage(message)
            self.write_error(exception)

    def on_url(self, url):
        if not self.url:
            self.url = url
        else:
            self.url += url

    def on_header(self, name, value):
        self._header_fragment += name

        if value is not None:
            if self._header_fragment == b'Content-Length' \
                    and int(value) > self.request_max_size:
                exception = PayloadTooLarge('Payload Too Large')
                self.write_error(exception)
            try:
                value = value.decode()
            except UnicodeDecodeError:
                value = value.decode('latin_1')
            self.headers.append(
                    (self._header_fragment.decode().casefold(), value))

            self._header_fragment = b''

    def on_headers_complete(self):
        self.request = self.request_class(
            url_bytes=self.url,
            headers=CIDict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode(),
            transport=self.transport
        )
        # Remove any existing KeepAlive handler here,
        # It will be recreated if required on the new request.
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()
            self._keep_alive_timeout_handler = None
        if self.is_request_stream:
            self._is_stream_handler = self.router.is_stream_handler(
                self.request)
            if self._is_stream_handler:
                self.request.stream = asyncio.Queue()
                self.execute_request_handler()

    def on_body(self, body):
        if self.is_request_stream and self._is_stream_handler:
            self._request_stream_task = self.loop.create_task(
                self.request.stream.put(body))
            return
        self.request.body.append(body)

    def on_message_complete(self):
        # Entire request (headers and whole body) is received.
        # We can cancel and remove the request timeout handler now.
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
            self._request_timeout_handler = None
        if self.is_request_stream and self._is_stream_handler:
            self._request_stream_task = self.loop.create_task(
                self.request.stream.put(None))
            return
        self.request.body = b''.join(self.request.body)
        self.execute_request_handler()

    def execute_request_handler(self):
        self._response_timeout_handler = self.loop.call_later(
            self.response_timeout, self.response_timeout_callback)
        self._last_request_time = current_time
        self._request_handler_task = self.loop.create_task(
            self.request_handler(
                self.request,
                self.write_response,
                self.stream_response))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #
    def log_response(self, response):
        if self.access_log:
            extra = {
                'status': getattr(response, 'status', 0),
            }

            if isinstance(response, HTTPResponse):
                extra['byte'] = len(response.body)
            else:
                extra['byte'] = -1

            extra['host'] = 'UNKNOWN'
            if self.request is not None:
                if self.request.ip:
                    extra['host'] = '{0}:{1}'.format(self.request.ip,
                                                     self.request.port)

                extra['request'] = '{0} {1}'.format(self.request.method,
                                                    self.request.url)
            else:
                extra['request'] = 'nil'

            access_logger.info('', extra=extra)

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
                    self.request.version, keep_alive,
                    self.keep_alive_timeout))
            self.log_response(response)
        except AttributeError:
            logger.error('Invalid response object for url %s, '
                         'Expected Type: HTTPResponse, Actual Type: %s',
                         self.url, type(response))
            self.write_error(ServerError('Invalid response type'))
        except RuntimeError:
            if self._debug:
                logger.error('Connection lost before response written @ %s',
                             self.request.ip)
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(
                    repr(e)))
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout,
                    self.keep_alive_timeout_callback)
                self._last_response_time = current_time
                self.cleanup()

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
            response.transport = self.transport
            await response.stream(
                self.request.version, keep_alive, self.keep_alive_timeout)
            self.log_response(response)
        except AttributeError:
            logger.error('Invalid response object for url %s, '
                         'Expected Type: HTTPResponse, Actual Type: %s',
                         self.url, type(response))
            self.write_error(ServerError('Invalid response type'))
        except RuntimeError:
            if self._debug:
                logger.error('Connection lost before response written @ %s',
                             self.request.ip)
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(
                    repr(e)))
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout,
                    self.keep_alive_timeout_callback)
                self._last_response_time = current_time
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
            version = self.request.version if self.request else '1.1'
            self.transport.write(response.output(version))
        except RuntimeError:
            if self._debug:
                logger.error('Connection lost before error written @ %s',
                             self.request.ip if self.request else 'Unknown')
        except Exception as e:
            self.bail_out(
                "Writing error failed, connection closed {}".format(
                    repr(e)), from_error=True
            )
        finally:
            if self.parser and (self.keep_alive
                                or getattr(response, 'status', 0) == 408):
                self.log_response(response)
            try:
                self.transport.close()
            except AttributeError as e:
                logger.debug('Connection lost before server could close it.')

    def bail_out(self, message, from_error=False):
        if from_error or self.transport.is_closing():
            logger.error("Transport closed @ %s and exception "
                         "experienced during error handling",
                         self.transport.get_extra_info('peername'))
            logger.debug('Exception:\n%s', traceback.format_exc())
        else:
            exception = ServerError(message)
            self.write_error(exception)
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
        if not self.parser:
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
          request_timeout=60, response_timeout=60, keep_alive_timeout=5,
          ssl=None, sock=None, request_max_size=None, reuse_port=False,
          loop=None, protocol=HttpProtocol, backlog=100,
          register_sys_signals=True, run_multiple=False, run_async=False,
          connections=None, signal=Signal(), request_class=None,
          access_log=True, keep_alive=True, is_request_stream=False,
          router=None, websocket_max_size=None, websocket_max_queue=None,
          websocket_read_limit=2 ** 16, websocket_write_limit=2 ** 16,
          state=None, graceful_shutdown_timeout=15.0):
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
    :param response_timeout: time in seconds
    :param keep_alive_timeout: time in seconds
    :param ssl: SSLContext
    :param sock: Socket for the server to accept connections from
    :param request_max_size: size in bytes, `None` for no limit
    :param reuse_port: `True` for multiple workers
    :param loop: asyncio compatible event loop
    :param protocol: subclass of asyncio protocol class
    :param request_class: Request class to use
    :param access_log: disable/enable access log
    :param is_request_stream: disable/enable Request.stream
    :param router: Router object
    :return: Nothing
    """
    if not run_async:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if debug:
        loop.set_debug(debug)

    connections = connections if connections is not None else set()
    server = partial(
        protocol,
        loop=loop,
        connections=connections,
        signal=signal,
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
        _singals = (SIGTERM,) if run_multiple else (SIGINT, SIGTERM)
        for _signal in _singals:
            try:
                loop.add_signal_handler(_signal, loop.stop)
            except NotImplementedError:
                logger.warning('Sanic tried to use loop.add_signal_handler '
                               'but it is not implemented on this platform.')
    pid = os.getpid()
    try:
        logger.info('Starting worker [%s]', pid)
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
        start_shutdown = 0
        while connections and (start_shutdown < graceful_shutdown_timeout):
            loop.run_until_complete(asyncio.sleep(0.1))
            start_shutdown = start_shutdown + 0.1

        # Force close non-idle connection after waiting for
        # graceful_shutdown_timeout
        coros = []
        for conn in connections:
            if hasattr(conn, "websocket") and conn.websocket:
                coros.append(
                    conn.websocket.close_connection(after_handshake=True)
                )
            else:
                conn.close()

        _shutdown = asyncio.gather(*coros, loop=loop)
        loop.run_until_complete(_shutdown)

        trigger_events(after_stop, loop)

        loop.close()


def serve_multiple(server_settings, workers):
    """Start multiple server processes simultaneously.  Stop on interrupt
    and terminate signals, and drain connections when complete.

    :param server_settings: kw arguments to be passed to the serve function
    :param workers: number of workers to launch
    :param stop_event: if provided, is used as a stop signal
    :return:
    """
    server_settings['reuse_port'] = True
    server_settings['run_multiple'] = True

    # Handling when custom socket is not provided.
    if server_settings.get('sock') is None:
        sock = socket()
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((server_settings['host'], server_settings['port']))
        sock.set_inheritable(True)
        server_settings['sock'] = sock
        server_settings['host'] = None
        server_settings['port'] = None

    def sig_handler(signal, frame):
        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        for process in processes:
            os.kill(process.pid, SIGTERM)

    signal_func(SIGINT, lambda s, f: sig_handler(s, f))
    signal_func(SIGTERM, lambda s, f: sig_handler(s, f))

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
    server_settings.get('sock').close()
