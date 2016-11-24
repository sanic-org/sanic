import asyncio
from functools import partial
from inspect import isawaitable
from multidict import CIMultiDict
from signal import SIGINT, SIGTERM
from time import time
import httptools

try:
    import uvloop as async_loop
except ImportError:
    async_loop = asyncio

from .log import log
from .request import Request
from .response import HTTPResponse, json, text


class Signal:
    stopped = False


current_time = None


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

    def __init__(self, *, loop, request_handler, signal=Signal(),
                 connections={}, request_timeout=60,
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
        self.request_timeout = request_timeout
        self.request_max_size = request_max_size
        self._total_request_size = 0
        self._timeout_handler = None
        self._last_request_time = None

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections[self] = True
        self._timeout_handler = self.loop.call_later(
            self.request_timeout, self.connection_timeout)
        self.transport = transport
        self._last_request_time = current_time

    def connection_lost(self, exc):
        del self.connections[self]
        self._timeout_handler.cancel()
        self.cleanup()

    def connection_timeout(self):
        # Check if
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._timeout_handler = \
                self.loop.call_later(time_left, self.connection_timeout)
        else:
            self.bail_out("Request timed out, connection closed")

    # -------------------------------------------- #
    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            return self.bail_out(
                "Request too large ({}), connection closed".format(
                    self._total_request_size))

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = httptools.HttpRequestParser(self)

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            self.bail_out(
                "Invalid request data, connection closed ({})".format(e))

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        if name == b'Content-Length' and int(value) > self.request_max_size:
            return self.bail_out(
                "Request body too large ({}), connection closed".format(value))

        self.headers.append((name.decode(), value.decode('utf-8')))

    def on_headers_complete(self):
        remote_addr = self.transport.get_extra_info('peername')
        if remote_addr:
            self.headers.append(('Remote-Addr', '%s:%s' % remote_addr))

        self.request = Request(
            url_bytes=self.url,
            headers=CIMultiDict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode()
        )

    def on_body(self, body):
        if self.request.body:
            self.request.body += body
        else:
            self.request.body = body

    def on_message_complete(self):
        self.loop.create_task(
            self.request_handler(self.request, self.write_response))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    def write_response(self, response):
        """Attempts to write the response to the transport

        This will attempt to intelligently handle any type of python object
        with dicts being treated like json and everything else being casted
        to str if it is not an HTTPResponse object
        """
        try:
            keep_alive = all(
                [self.parser.should_keep_alive(), self.signal.stopped])
            if isinstance(response, HTTPResponse):  # Easy pass first
                pass
            elif isinstance(response, (dict, list)):
                response = json(response)
            else:
                response = text(str(response))
            self.transport.write(
                response.output(
                    self.request.version, keep_alive, self.request_timeout))
            if not keep_alive:
                self.transport.close()
            else:
                # Record that we received data
                self._last_request_time = current_time
                self.cleanup()
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(e))

    def bail_out(self, message):
        log.debug(message)
        self.transport.close()

    def cleanup(self):
        self.parser = None
        self.request = None
        self.url = None
        self.headers = None
        self._total_request_size = 0

    def close_if_idle(self):
        """
        Close the connection if a request is not being sent or received
        :return: boolean - True if closed, false if staying open
        """
        if not self.parser:
            self.transport.close()
            return True
        return False


def update_current_time(loop):
    """
    Caches the current time, since it is needed
    at the end of every keep-alive request to update the request timeout time
    :param loop:
    :return:
    """
    global current_time
    current_time = time()
    loop.call_later(1, partial(update_current_time, loop))


def trigger_events(events, loop):
    """
    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    if events:
        if not isinstance(events, list):
            events = [events]
        for event in events:
            result = event(loop)
            if isawaitable(result):
                loop.run_until_complete(result)


def serve(host, port, request_handler, before_start=None, after_start=None,
          before_stop=None, after_stop=None,
          debug=False, request_timeout=60, sock=None,
          request_max_size=None, reuse_port=False, loop=None):
    """
    Starts asynchronous HTTP Server on an individual process.
    :param host: Address to host on
    :param port: Port to host on
    :param request_handler: Sanic request handler with middleware
    :param after_start: Function to be executed after the server starts
    listening. Takes single argument `loop`
    :param before_stop: Function to be executed when a stop signal is
    received before it is respected. Takes single argumenet `loop`
    :param debug: Enables debug output (slows server)
    :param request_timeout: time in seconds
    :param sock: Socket for the server to accept connections from
    :param request_max_size: size in bytes, `None` for no limit
    :param reuse_port: `True` for multiple workers
    :param loop: asyncio compatible event loop
    :return: Nothing
    """
    loop = loop or async_loop.new_event_loop()
    asyncio.set_event_loop(loop)

    if debug:
        loop.set_debug(debug)

    trigger_events(before_start, loop)

    connections = {}
    signal = Signal()
    server_coroutine = loop.create_server(lambda: HttpProtocol(
        loop=loop,
        connections=connections,
        signal=signal,
        request_handler=request_handler,
        request_timeout=request_timeout,
        request_max_size=request_max_size,
    ), host, port, reuse_port=reuse_port, sock=sock)

    # Instead of pulling time at the end of every request,
    # pull it once per minute
    loop.call_soon(partial(update_current_time, loop))

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except Exception:
        log.exception("Unable to start server")
        return

    trigger_events(after_start, loop)

    # Register signals for graceful termination
    for _signal in (SIGINT, SIGTERM):
        loop.add_signal_handler(_signal, loop.stop)

    try:
        loop.run_forever()
    finally:
        log.info("Stop requested, draining connections...")

        # Run the on_stop function if provided
        trigger_events(before_stop, loop)

        # Wait for event loop to finish and all connections to drain
        http_server.close()
        loop.run_until_complete(http_server.wait_closed())

        # Complete all tasks on the loop
        signal.stopped = True
        for connection in connections.keys():
            connection.close_if_idle()

        while connections:
            loop.run_until_complete(asyncio.sleep(0.1))

        trigger_events(after_stop, loop)

        loop.close()
