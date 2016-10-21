import asyncio
from functools import partial
from inspect import isawaitable
from signal import SIGINT, SIGTERM

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError

try:
    import uvloop as async_loop
except ImportError:
    async_loop = asyncio

from .log import log
from .request import Request

CONNECTIONS = set()


class STATUS:
    running = True  # sanic runs!


class HttpProtocol(asyncio.Protocol):
    __slots__ = (
        # event loop, connection
        'loop', 'transport',
        # request params
        'parser', 'request', 'url', 'headers',
        # request config
        'request_handler', 'request_timeout', 'request_max_size',
        # connection management
        '_total_request_size', '_timeout_handler')

    def __init__(self, *, loop, request_handler,
                 request_timeout=60, request_max_size=None):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.request_handler = request_handler
        self.request_timeout = request_timeout
        self.request_max_size = request_max_size
        self._total_request_size = 0
        self._timeout_handler = None

        # -------------------------------------------- #

    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        CONNECTIONS.add(self)
        self._timeout_handler = self.loop.call_later(
            self.request_timeout, self.connection_timeout)
        self.transport = transport

    def connection_lost(self, exc):
        CONNECTIONS.discard(self)
        self._timeout_handler.cancel()

    def connection_timeout(self):
        log.error('Request timed out, connection closed')
        self.transport.close()

        # -------------------------------------------- #

    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            log.error(
                'Request too large (%s), connection closed',
                self._total_request_size
            )
            self.transport.close()
            return

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.parser = HttpRequestParser(self)

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except HttpParserError as e:
            log.error('Invalid request data, connection closed (%s)', e)
            self.transport.close()

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        if name == b'Content-Length' and int(value) > self.request_max_size:
            log.error('Request body too large (%s), connection closed', value)
            self.transport.close()
            return

        if self.headers is None:
            self.headers = {}

        self.headers[name.decode()] = value.decode('utf-8')

    def on_headers_complete(self):
        self.request = Request(
            url_bytes=self.url,
            headers=self.headers,
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode()
        )

    def on_body(self, body):
        self.request.body = body

    def on_message_complete(self):
        self.loop.create_task(
            self.request_handler(self.request, self.write_response))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    def write_response(self, response):
        try:
            keep_alive = STATUS.running and self.parser.should_keep_alive()
            self.transport.write(
                response.output(
                    self.request.version, keep_alive, self.request_timeout))
            if keep_alive:
                self.parser = None
                self.request = None
                self.url = None
                self.headers = None
                self._total_request_size = 0
            else:
                self.transport.close()
        except Exception as e:
            log.error('Writing request failed, connection closed %s', e)
            self.transport.close()

    def close_if_idle(self):
        """
        Close the connection if a request is not being sent or received
        :return: boolean - True if closed, false if staying open
        """
        if not self.parser:
            self.transport.close()


def serve(host, port, request_handler, after_start=None, before_stop=None,
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

    server = partial(
        HttpProtocol,
        loop=loop,
        request_handler=request_handler,
        request_timeout=request_timeout,
        request_max_size=request_max_size,
    )
    server_coroutine = loop.create_server(
        server,
        host,
        port,
        reuse_port=reuse_port,
        sock=sock
    )
    try:
        http_server = loop.run_until_complete(server_coroutine)
    except Exception as e:
        log.exception("Unable to start server")
        return

    # Run the on_start function if provided
    if after_start:
        result = after_start(loop)
        if isawaitable(result):
            loop.run_until_complete(result)

    # Register signals for graceful termination
    for _signal in (SIGINT, SIGTERM):
        loop.add_signal_handler(_signal, loop.stop)

    try:
        loop.run_forever()
    finally:
        log.info("Stop requested, draining connections...")

        # Run the on_stop function if provided
        if before_stop:
            result = before_stop(loop)
            if isawaitable(result):
                loop.run_until_complete(result)

        # Wait for event loop to finish and all connections to drain
        http_server.close()
        loop.run_until_complete(http_server.wait_closed())

        # Complete all tasks on the loop
        STATUS.running = False
        for connection in CONNECTIONS:
            connection.close_if_idle()

        while CONNECTIONS:
            loop.run_until_complete(asyncio.sleep(0.1))

        loop.close()
