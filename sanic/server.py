import argparse
import sys
import asyncio
import signal
import functools
import httptools
import logging
from inspect import isawaitable
from ujson import loads as json_loads
from traceback import format_exc
from time import time

import httptools
try:
    import uvloop as async_loop
except:
    async_loop = asyncio

from socket import *

from .log import log
from .exceptions import ServerError
from .response import HTTPResponse
from .request import Request

class HttpProtocol(asyncio.Protocol):

    __slots__ = ('loop', 'transport', # event loop, connection
                 'parser', 'request', 'url', 'headers', # request params
                 'sanic', # router and config object
                 '_total_body_size',  '_timeout_handler') # connection management

    def __init__(self, *, sanic, loop):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.sanic = sanic
        self._total_request_size = 0

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self._timeout_handler = self.loop.call_later(self.sanic.config.KEEP_ALIVE_TIMEOUT, self.connection_timeout)
        self.transport = transport
        #TODO: handle connection timeout

    def connection_lost(self, exc):
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
        if self._total_request_size > self.sanic.config.REQUEST_MAX_SIZE:
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
        if name == 'Content-Length' and int(value) > self.sanic.config.REQUEST_MAX_SIZE:
            return self.bail_out("Request body too large ({}), connection closed".format(value))

        self.headers.append((name, value.decode('utf-8')))

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
        self.loop.create_task(self.get_response())

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #

    async def get_response(self):
        try:
            handler = self.sanic.router.get(self.request)
            if handler is None:
                raise ServerError("'None' was returned while requesting a handler from the router")

            response = handler(self.request)

            # Check if the handler is asynchronous
            if isawaitable(response):
                response = await response

        except Exception as e:
            try:
                response = self.sanic.error_handler.response(self.request, e)
            except Exception as e:
                if self.sanic.debug:
                    response = HTTPResponse("Error while handling error: {}\nStack: {}".format(e, format_exc()))
                else:
                    response = HTTPResponse("An error occured while handling an error")
        
        self.write_response(response)

    def write_response(self, response):
        #print("response - {} - {}".format(self.n, self.request))
        try:
            keep_alive = self.parser.should_keep_alive()
            self.transport.write(response.output(self.request.version, keep_alive, self.sanic.config.KEEP_ALIVE_TIMEOUT))
            #print("KA - {}".format(self.parser.should_keep_alive()))
            if not keep_alive:
                self.transport.close()
            else:
                self.cleanup()
        except Exception as e:
            self.bail_out("Writing request failed, connection closed {}".format(e))

    def bail_out(self, error):
        log.error(error)
        self.transport.close()

    def cleanup(self):
        self.parser = None
        self.request = None
        self.url = None
        self.headers = None
        self._total_body_size = 0

def serve(sanic, host, port, debug=False, on_start=None, on_stop=None):
    # Create Event Loop
    loop = async_loop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(debug)

    if debug:
        log.setLevel(logging.DEBUG)
    log.debug(sanic.config.LOGO)

    # Serve
    log.info('Goin\' Fast @ {}:{}'.format(host, port))

    # Run the on_start function if provided
    if on_start:
        result = on_start(sanic, loop)
        if isawaitable(result):
            loop.run_until_complete(result)

    server_coroutine = loop.create_server(lambda: HttpProtocol(loop=loop, sanic=sanic), host, port)
    #connection_timeout_coroutine = 
    server_loop = loop.run_until_complete(server_coroutine)
    try:
        loop.run_forever()
    finally:
        # Run the on_stop function if provided
        if on_stop:
            result = on_stop(sanic, loop)
            if isawaitable(result):
                loop.run_until_complete(result)

        # Wait for event loop to finish and all connections to drain
        server_loop.close()
        loop.close()