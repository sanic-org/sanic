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

from .config import Config
from .log import log
from .request import Request

CONNECTIONS = set()


class STATUS:
    running = True  # sanic runs!


class HttpProtocol(asyncio.Protocol):
    __slots__ = (
        # event loop, connection
        'loop', 'close', 'write',
        # request params
        'parser', 'request', 'url', 'headers',
        # request config
        'request_handler',
        # connection management
        '_total_request_size', '_timeout_handler')

    def __init__(self, *, loop, request_handler):
        self.loop = loop
        self.close = None
        self.write = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = {}
        self.request_handler = request_handler
        self._total_request_size = 0
        self._timeout_handler = None

        # -------------------------------------------- #

    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        CONNECTIONS.add(self)
        self._timeout_handler = self.loop.call_later(
            Config.REQUEST_TIMEOUT, self.connection_timeout)
        self.close = transport.close
        self.write = transport.write

    def connection_lost(self, _):
        CONNECTIONS.discard(self)
        self._timeout_handler.cancel()

    def connection_timeout(self):
        log.error('Request timed out, connection closed')
        self.close()

        # -------------------------------------------- #

    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > Config.REQUEST_MAX_SIZE:
            log.error(
                'Request too large (%s), connection closed',
                self._total_request_size
            )
            self.close()
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
            self.close()

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        if name == b'Content-Length' and int(value) > Config.REQUEST_MAX_SIZE:
            log.error('Request body too large (%s), connection closed', value)
            self.close()
            return

        self.headers[name.decode()] = value.decode('utf-8')

    def on_headers_complete(self):
        self.request = Request(
            url_bytes=self.url,
            headers=self.headers,
            version=self.parser.get_http_version,
            method=self.parser.get_method
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
            self.write(
                response.output(
                    self.request.version, keep_alive, Config.REQUEST_TIMEOUT))
            if keep_alive:
                self.parser = None
                self.request = None
                self.url = None
                self.headers = {}
                self._total_request_size = 0
            else:
                self.close()
        except Exception as e:
            log.error('Writing request failed, connection closed %s', e)
            self.close()


def serve(host, port, request_handler, after_start=None, before_stop=None,
          debug=False, sock=None,
          reuse_port=False, loop=None):
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
    :param sock: Socket for the server to accept connections from
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
        request_handler=request_handler
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
            if connection.parser is None:
                connection.close()

        while CONNECTIONS:
            loop.run_until_complete(asyncio.sleep(0.1))

        loop.close()
