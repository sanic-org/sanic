import asyncio
import io
import collections
from functools import partial
from typing import List, Tuple

from h2.connection import H2Connection
from h2.events import (
    ConnectionTerminated, DataReceived, RequestReceived, StreamEnded
)
from h2.errors import ErrorCodes
from h2.exceptions import ProtocolError

from sanic.request import Request
from sanic.log import log

RequestData = collections.namedtuple('RequestData', ['headers', 'data'])


def HTTP2Protocol(ssl, parent_class):
    ssl.set_ciphers("ECDHE+AESGCM")
    ssl.set_alpn_protocols(["h2", "http/1.1"])

    _HTTP2Protocol = type("HTTP2Protocol", (HTTP2Checker, parent_class), {})
    _HTTP2Protocol.protocol_class = type("H2Protocol", (H2Protocol, parent_class), {})

    return _HTTP2Protocol


class HTTP2Checker:
    def connection_made(self, transport):
        ssl_object = transport.get_extra_info('ssl_object')
        protocol = ssl_object.selected_alpn_protocol()

        if protocol == 'h2':
            self.__class__ = self.protocol_class
            self.connection_made(transport)
        else:
            super().connection_made(transport)


class H2Protocol(asyncio.Protocol):

    def connection_made(self, transport):
        # TODO: Request timeouts
        self.h2_connection = H2Connection(client_side=False)
        self.stream_data = {}
        self.h2_connection.initiate_connection()
        self.transport = transport
        self.transport.write(self.h2_connection.data_to_send())

    def data_received(self, data: bytes):
        try:
            events = self.h2_connection.receive_data(data)
        except ProtocolError as e:
            self.transport.write(self.h2_connection.data_to_send())
            self.transport.close()
        else:
            self.transport.write(self.h2_connection.data_to_send())
            for event in events:
                if isinstance(event, RequestReceived):
                    self.receive_headers(event.headers, event.stream_id)
                elif isinstance(event, DataReceived):
                    self.receive_data(event.data, event.stream_id)
                elif isinstance(event, StreamEnded):
                    self.stream_complete(event.stream_id)
                elif isinstance(event, ConnectionTerminated):
                    self.transport.close()

                self.transport.write(self.h2_connection.data_to_send())

    def receive_headers(self, headers: List[Tuple[str, str]], stream_id: int):
        # Store off the request data.
        request_data = RequestData(dict(headers), io.BytesIO())
        self.stream_data[stream_id] = request_data

    def receive_data(self, data: bytes, stream_id: int):
        """
        We've received some data on a stream. If that stream is one we're
        expecting data on, save it off. Otherwise, reset the stream.
        """
        try:
            stream_data = self.stream_data[stream_id]
        except KeyError:
            self.h2_connection.reset_stream(
                stream_id, error_code=ErrorCodes.PROTOCOL_ERROR
            )
        else:
            stream_data.data.write(data)

    def stream_complete(self, stream_id: int):
        """
        When a stream is complete, we can send our response.
        """
        try:
            request_data = self.stream_data[stream_id]
        except KeyError:
            # Just return, we probably 405'd this already
            return

        # Build request object from h2 data
        headers = {header: value for header, value in
                   request_data.headers.items() if not header.startswith(':')}
        request = Request(request_data.headers[':path'].encode(), headers,
                          '2', request_data.headers[':method'], None)
        request.body = request_data.data.getvalue().decode('utf-8')

        body = partial(self.write_response, stream_id, request)
        self.loop.create_task(self.request_handler(request, body))

    def write_response(self, stream_id, request, response):
        try:
            headers = response.headers
            headers[':status'] = str(response.status)
            headers['content-type'] = response.content_type
            headers['content-length'] = str(len(response.body))

            self.h2_connection.send_headers(stream_id, headers)
            self.h2_connection.send_data(stream_id, response.body,
                                         end_stream=True)
        except AttributeError:
            log.error(
                ('Invalid response object for url {}, '
                 'Expected Type: HTTPResponse, Actual Type: {}').format(
                    request.url, type(response)))
        except RuntimeError:
            log.error(
                'Connection lost before response written @ {}'.format(
                    request.ip))
        except Exception as e:
            # TODO: not sure how to handle
            pass
        finally:
            self.transport.write(self.h2_connection.data_to_send())
