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
from .response import HTTPResponse

PRINT = 0

class Request:
    __slots__ = ('protocol', 'url', 'headers', 'version', 'method')

    def __init__(self, protocol, url, headers, version, method):
        self.protocol = protocol
        self.url = url
        self.headers = headers
        self.version = version
        self.method = method

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
        #TODO: handle keep-alive/connection timeout

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

        try:
            #print(data)
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError:
            #log.error("Invalid request data, connection closed")
            self.transport.close()

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
        global n
        n += 1
        self.n = n
        #print("res {} - {}".format(n, self.request))
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
            self.write_response(request, response)

    def write_response(self, request, response):
        #print("response - {} - {}".format(self.n, self.request))
        try:
            keep_alive = self.parser.should_keep_alive()
            self.transport.write(response.output(request.version, keep_alive))
            #print("KA - {}".format(self.parser.should_keep_alive()))
            if not keep_alive:
                self.transport.close()
        except:
            log.error("Writing request failed, connection closed")
            self.transport.close()

        self.parser = None
        self.request = None

    # -------------------------------------------- #
    # Async
    # -------------------------------------------- #

    async def handle_response(self, future, handler, request):
        response = await handler(request)
        future.set_result((request, response))

    def handle_result(self, future):
        request, response = future.result()
        self.write_response(request, response)


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