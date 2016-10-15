import asyncio
from inspect import isawaitable
from signal import SIGINT, SIGTERM

import httptools

try:
    import uvloop as async_loop
except:
    async_loop = asyncio

from .log import log
from .request import Request


class Signal:
    stopped = False


class HttpProtocol(asyncio.Protocol):
    __slots__ = ('loop', 'transport', 'connections', 'signal',  # event loop, connection
                 'parser', 'request', 'url', 'headers',  # request params
                 'request_handler', 'request_timeout', 'request_max_size',  # request config
                 '_total_request_size', '_timeout_handler')  # connection management

    def __init__(self, *, loop, request_handler, signal=Signal(), connections={}, request_timeout=60,
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

        # -------------------------------------------- #

    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections[self] = True
        self._timeout_handler = self.loop.call_later(self.request_timeout, self.connection_timeout)
        self.transport = transport

    def connection_lost(self, exc):
        del self.connections[self]
        self._timeout_handler.cancel()
        self.cleanup()

    def connection_timeout(self):
        self.bail_out("Request timed out, connection closed")

        # -------------------------------------------- #

    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            return self.bail_out("Request too large ({}), connection closed".format(self._total_request_size))

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = httptools.HttpRequestParser(self)

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            self.bail_out("Invalid request data, connection closed ({})".format(e))

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        if name == b'Content-Length' and int(value) > self.request_max_size:
            return self.bail_out("Request body too large ({}), connection closed".format(value))

        self.headers.append((name.decode(), value.decode('utf-8')))

    def on_headers_complete(self):
        self.request = Request(
            url_bytes=self.url,
            headers=dict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode()
        )

    def on_body(self, body):
        self.request.body = body

    def on_message_complete(self):
        self.loop.create_task(self.request_handler(self.request, self.write_response))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    def write_response(self, response):
        try:
            keep_alive = self.parser.should_keep_alive() and not self.signal.stopped
            self.transport.write(response.output(self.request.version, keep_alive, self.request_timeout))
            if not keep_alive:
                self.transport.close()
            else:
                self.cleanup()
        except Exception as e:
            self.bail_out("Writing request failed, connection closed {}".format(e))

    def bail_out(self, message):
        log.error(message)
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


def serve(host, port, request_handler, after_start=None, before_stop=None, debug=False, request_timeout=60,
          request_max_size=None):
    # Create Event Loop
    loop = async_loop.new_event_loop()
    asyncio.set_event_loop(loop)
    # I don't think we take advantage of this
    # And it slows everything waaayyy down
    # loop.set_debug(debug)

    connections = {}
    signal = Signal()
    server_coroutine = loop.create_server(lambda: HttpProtocol(
        loop=loop,
        connections=connections,
        signal=signal,
        request_handler=request_handler,
        request_timeout=request_timeout,
        request_max_size=request_max_size,
    ), host, port)
    try:
        http_server = loop.run_until_complete(server_coroutine)
    except OSError as e:
        log.error("Unable to start server: {}".format(e))
        return
    except:
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
        signal.stopped = True
        for connection in connections.keys():
            connection.close_if_idle()

        while connections:
            loop.run_until_complete(asyncio.sleep(0.1))

        loop.close()
        log.info("Server Stopped")
