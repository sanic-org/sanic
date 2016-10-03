import argparse
import sys
import asyncio
import signal
import functools
import httptools
import logging
from ujson import loads as json_loads
from urllib.parse import parse_qs

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
    __slots__ = ('protocol', 'url', 'headers', 'version', 'method', 'query_string', 'body', 'parsed_json', 'parsed_args')

    def __init__(self, protocol, url, headers, version, method):
        self.protocol = protocol
        self.url = url
        self.headers = headers
        self.version = version
        self.method = method

        # Capture query string
        query_string_position = self.url.find(b"?")
        if query_string_position != -1:
            self.query_string = self.url[query_string_position+1:]
            self.url = self.url[:query_string_position]
        else:
            self.query_string = None

        # Init but do not inhale
        self.body = None
        self.parsed_json = None
        self.parsed_args = None

    @property
    def json(self):
        if not self.parsed_json:
            if not self.body:
                raise ValueError("No body to parse")
            self.parsed_json = json_loads(self.body)

        return self.parsed_json 

    @property
    def args(self):
        if not self.parsed_args and self.query_string:
            self.parsed_args = {k:v if len(v)>1 else v[0] for k,v in parse_qs(self.query_string).items()}

        return self.parsed_args 

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
        except httptools.parser.errors.HttpParserError as e:
            log.error("Invalid request data, connection closed ({})".format(e))
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
        #print("res {} - {}".format(n, self.request))

    def on_body(self, body):
        self.request.body = body
    def on_message_complete(self):
        self.loop.create_task(self.get_response(self.request))

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    async def get_response(self, request):
        handler = self.router.get(request.url)
        try:
            if handler.is_async:
                response = await handler(request)
            else:
                response = handler(request)
        except Exception as e:
            response = HTTPResponse("Error: {}".format(e))
        
        self.write_response(request, response)

    def write_response(self, request, response):
        #print("response - {} - {}".format(self.n, self.request))
        try:
            keep_alive = self.parser.should_keep_alive()
            self.transport.write(response.output(request.version, keep_alive))
            #print("KA - {}".format(self.parser.should_keep_alive()))
            if not keep_alive:
                self.transport.close()
        except Exception as e:
            log.error("Writing request failed, connection closed {}".format(e))
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