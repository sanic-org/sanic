import argparse
import sys
import asyncio
import signal
import functools
import httptools
import logging

import httptools
try:
    import uvloop as async_loop
except:
    async_loop = asyncio

from socket import *

from .log import log
from .config import LOGO

PRINT = 0

class Request:
    __slots__ = ('protocol', 'url', 'headers', 'version', 'method')

    def __init__(self, protocol, url, headers, version, method):
        self.protocol = protocol
        self.url = url
        self.headers = headers
        self.version = version
        self.method = method

STATUS_CODES = {
    200: 'OK',
    404: 'Not Found'
}
class Response:
    __slots__ = ('body', 'status', 'content_type')

    def __init__(self, body='', status=200, content_type='text/plain'):
        self.content_type = 'text/plain'
        self.body = body
        self.status = status

    @property
    def body_bytes(self):
        body_type = type(self.body)
        if body_type is str:
            body = self.body.encode('utf-8')
        elif body_type is bytes:
            body = self.body
        else:
            body = b'Unable to interpret body'

        return body

    def output(self, version):
        body = self.body_bytes
        return b''.join([
            'HTTP/{} {} {}\r\n'.format(version, self.status, STATUS_CODES.get(self.status, 'FAIL')).encode('latin-1'),
            'Content-Type: {}\r\n'.format(self.content_type).encode('latin-1'),
            'Content-Length: {}\r\n'.format(len(body)).encode('latin-1'),
            b'\r\n',
            body
        ])


class HttpProtocol(asyncio.Protocol):

    __slots__ = ('loop',
                 'transport', 'request', 'parser',
                 'url', 'headers', 'router')

    def __init__(self, *, router, loop):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.router = router

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.transport = transport
        # TCP Nodelay
        # I have no evidence to support this makes anything faster
        # So I'll leave it commented out for now
        
        # sock = transport.get_extra_info('socket')
        # try:
        #     sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        # except (OSError, NameError):
        #     pass

    def connection_lost(self, exc):
        self.request = self.parser = None

    # -------------------------------------------- #
    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = httptools.HttpRequestParser(self)

        self.parser.feed_data(data)

    def on_url(self, url):
        self.url = url

    def on_header(self, name, value):
        self.headers.append((name, value))

    def on_headers_complete(self):
        self.request = Request(
            protocol=self, 
            url=self.url, 
            headers=dict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method()
        )
        self.loop.call_soon(self.handle, self.request)

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    def handle(self, request):
        handler = self.router.get(request.url)
        if handler.is_async:
            future = asyncio.Future()
            self.loop.create_task(self.handle_response(future, handler, request))
            future.add_done_callback(self.handle_result)
        else:
            response = handler(request)
            self.write_response(response)

    def write_response(self, response):
        self.transport.write(response.output(request.version))

        if not self.parser.should_keep_alive():
            self.transport.close()
        self.parser = None
        self.request = None

    # -------------------------------------------- #
    # Async
    # -------------------------------------------- #

    async def handle_response(self, future, handler, request):
        result = await handler(request)
        future.set_result(result)

    def handle_result(self, future):
        response = future.result()
        self.write_response(response)


def abort(msg):
    log.info(msg, file=sys.stderr)
    sys.exit(1)


def serve(router, host, port, debug=False):
    # Create Event Loop
    loop = async_loop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(debug)

    # Add signal handlers
    def ask_exit(signame):
        log.debug("Exiting, received signal %s" % signame)
        loop.stop()

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), functools.partial(ask_exit, signame))

    if debug:
        log.setLevel(logging.DEBUG)
    log.debug(LOGO)

    # Serve
    log.info('Goin\' Fast @ {}:{}'.format(host, port))

    server_coroutine = loop.create_server(lambda: HttpProtocol(loop=loop, router=router), host, port)
    server_loop = loop.run_until_complete(server_coroutine)
    try:
        loop.run_forever()
    finally:
        server_loop.close()
        loop.close()