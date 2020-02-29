from asyncio import CancelledError
from enum import Enum

from sanic.compat import Header
from sanic.exceptions import (
    HeaderExpectationFailed,
    InvalidUsage,
    PayloadTooLarge,
    RequestTimeout,
    SanicException,
    ServerError,
    ServiceUnavailable,
)
from sanic.headers import format_http1, format_http1_response
from sanic.helpers import has_message_body, remove_entity_headers
from sanic.log import access_logger, logger
from sanic.request import Request
from sanic.response import HTTPResponse


class Stage(Enum):
    IDLE = 0  # Waiting for request
    REQUEST = 1  # Request headers being received
    HANDLER = 3  # Headers done, handler running
    RESPONSE = 4  # Response headers sent, body in progress
    FAILED = 100  # Unrecoverable state (error while sending response)


HTTP_CONTINUE = b"HTTP/1.1 100 Continue\r\n\r\n"

class Http:
    def __init__(self, protocol):
        self._send = protocol.send
        self._receive_more = protocol.receive_more
        self.recv_buffer = protocol.recv_buffer
        self.protocol = protocol
        self.expecting_continue = False
        self.stage = Stage.IDLE
        self.keep_alive = True
        self.head_only = None
        self.request = None
        self.exception = None

    async def http1_receive_request(self):
        buf = self.recv_buffer
        pos = 0
        while len(buf) < self.protocol.request_max_size:
            if buf:
                pos = buf.find(b"\r\n\r\n", pos)
                if pos >= 0:
                    break
                pos = max(0, len(buf) - 3)
            await self._receive_more()
            if self.stage is Stage.IDLE:
                self.stage = Stage.REQUEST
        else:
            raise PayloadTooLarge("Payload Too Large")

        self.protocol._total_request_size = pos + 4

        try:
            reqline, *headers = buf[:pos].decode().split("\r\n")
            method, self.url, protocol = reqline.split(" ")
            if protocol not in ("HTTP/1.0", "HTTP/1.1"):
                raise Exception
            self.head_only = method.upper() == "HEAD"
            headers = Header(
                (name.lower(), value.lstrip())
                for name, value in (h.split(":", 1) for h in headers)
            )
        except:
            raise InvalidUsage("Bad Request")
        request = self.protocol.request_class(
            url_bytes=self.url.encode(),
            headers=headers,
            version=protocol[-3:],
            method=method,
            transport=self.protocol.transport,
            app=self.protocol.app,
        )

        # Prepare a request object from the header received
        request.stream = self
        self.protocol.state["requests_count"] += 1
        self.keep_alive = (
            protocol == "HTTP/1.1"
            or headers.get("connection", "").lower() == "keep-alive"
        )
        # Prepare for request body
        body = headers.get("transfer-encoding") == "chunked" or int(
            headers.get("content-length", 0)
        )
        self.request_chunked = False
        self.request_bytes_left = 0
        if body:
            expect = headers.get("expect")
            if expect:
                if expect.lower() == "100-continue":
                    self.expecting_continue = True
                else:
                    raise HeaderExpectationFailed(
                        f"Unknown Expect: {expect}")
            request.stream = self
            if body is True:
                self.request_chunked = True
                pos -= 2  # One CRLF stays in buffer
            else:
                self.request_bytes_left = body
        # Remove header and its trailing CRLF
        del buf[: pos + 4]
        self.stage = Stage.HANDLER
        self.request = request

    async def http1(self):
        """HTTP 1.1 connection handler"""
        while self.stage is Stage.IDLE and self.keep_alive:
            try:
                # Receive request header and call handler
                await self.http1_receive_request()
                await self.protocol.request_handler(self.request)
                if self.stage is Stage.HANDLER:
                    raise ServerError("Handler produced no response")
                # Finish sending a response (if no error)
                if self.stage is Stage.RESPONSE:
                    await self.send(end_stream=True)
                # Consume any remaining request body
                if self.request_bytes_left or self.request_chunked:
                    logger.error(f"{self.request} body not consumed.")
                    async for _ in self:
                        pass
            except Exception as e:
                self.exception = e
            except BaseException:
                # Exit after trying to finish a response
                self.keep_alive = False
                if self.exception is None:
                    self.exception = ServiceUnavailable(f"Cancelled")
            if self.exception:
                e, self.exception = self.exception, None
                # Exception while idle? Probably best to close connection
                if self.stage is Stage.IDLE:
                    return
                # Request failure? Try to respond but then disconnect
                if self.stage is Stage.REQUEST:
                    self.keep_alive = False
                    self.stage = Stage.HANDLER
                # Return an error page if possible
                if self.stage is Stage.HANDLER:
                    app = self.protocol.app
                    response = await app.handle_exception(self.request, e)
                    await self.respond(response).send(end_stream=True)


    # Request methods

    async def __aiter__(self):
        while True:
            data = await self.read()
            if not data:
                return
            yield data

    async def read(self):
        # Send a 100-continue if needed
        if self.expecting_continue:
            self.expecting_continue = False
            await self._send(HTTP_CONTINUE)
        # Receive request body chunk
        buf = self.recv_buffer
        if self.request_chunked and self.request_bytes_left == 0:
            # Process a chunk header: \r\n<size>[;<chunk extensions>]\r\n
            while True:
                pos = buf.find(b"\r\n", 3)
                if pos != -1:
                    break
                if len(buf) > 64:
                    self.keep_alive = False
                    raise InvalidUsage("Bad chunked encoding")
                await self._receive_more()
            try:
                size = int(buf[2:pos].split(b";", 1)[0].decode(), 16)
            except:
                self.keep_alive = False
                raise InvalidUsage("Bad chunked encoding")
            self.request_bytes_left = size
            self.protocol._total_request_size += pos + 2
            del buf[: pos + 2]
            if self.request_bytes_left <= 0:
                self.request_chunked = False
                return None
        # At this point we are good to read/return _request_bytes_left
        if self.request_bytes_left:
            if not buf:
                await self._receive_more()
            data = bytes(buf[: self.request_bytes_left])
            size = len(data)
            del buf[:size]
            self.request_bytes_left -= size
            self.protocol._total_request_size += size
            if self.protocol._total_request_size > self.protocol.request_max_size:
                self.keep_alive = False
                raise PayloadTooLarge("Payload Too Large")
            return data
        return None


    # Response methods

    def respond(self, response):
        """Initiate new streaming response.

        Nothing is sent until the first send() call on the returned object, and
        calling this function multiple times will just alter the response to be
        given."""
        if self.stage is not Stage.HANDLER:
            self.stage = Stage.FAILED
            raise RuntimeError("Response already started")
        if not isinstance(response.status, int) or response.status < 200:
            raise RuntimeError(f"Invalid response status {response.status!r}")
        self.response = response
        return self

    async def send(self, data=None, end_stream=None):
        """Send any pending response headers and the given data as body.
         :param data: str or bytes to be written
         :end_stream: whether to close the stream after this block
        """
        if data is None and end_stream is None:
            end_stream = True
        data = self.data_to_send(data, end_stream)
        if data is None:
            return
        await self._send(data)

    def data_to_send(self, data, end_stream):
        """Format output data bytes for given body data.
        Headers are prepended to the first output block and then cleared.
         :param data: str or bytes to be written
         :return: bytes to send, or None if there is nothing to send
        """
        data = data.encode() if hasattr(data, "encode") else data
        size = len(data) if data is not None else 0

        # Headers not yet sent?
        if self.stage is Stage.HANDLER:
            if self.response.body:
                data = self.response.body + data if data else self.response.body
                size = len(data)
            r = self.response
            status = r.status
            headers = r.headers
            if r.content_type and "content-type" not in headers:
                headers["content-type"] = r.content_type
            # Not Modified, Precondition Failed
            if status in (304, 412):
                headers = remove_entity_headers(headers)
            if not has_message_body(status):
                # Header-only response status
                if (
                    size > 0
                    or not end_stream
                    or "content-length" in headers
                    or "transfer-encoding" in headers
                ):
                    # TODO: This matches old Sanic operation but possibly
                    # an exception would be more appropriate?
                    data = None
                    size = 0
                    end_stream = True
                    #raise ServerError(
                    #    f"A {status} response may only have headers, no body."
                    #)
            elif self.head_only and "content-length" in headers:
                pass
            elif end_stream:
                # Non-streaming response (all in one block)
                headers["content-length"] = size
            elif "content-length" in headers:
                # Streaming response with size known in advance
                self.response_bytes_left = int(headers["content-length"]) - size
            else:
                # Length not known, use chunked encoding
                headers["transfer-encoding"] = "chunked"
                data = b"%x\r\n%b\r\n" % (size, data) if size else None
                self.response_bytes_left = True
            self.headers = None
            if self.head_only:
                data = None
                self.response_bytes_left = None
            if self.keep_alive:
                headers["connection"] = "keep-alive"
                headers["keep-alive"] = self.protocol.keep_alive_timeout
            else:
                headers["connection"] = "close"
            ret = format_http1_response(status, headers.items(), data or b"")
            # Send a 100-continue if expected and not Expectation Failed
            if self.expecting_continue:
                self.expecting_continue = False
                if status != 417:
                    ret = HTTP_CONTINUE + ret
            # Send response
            self.stage = Stage.IDLE if end_stream else Stage.RESPONSE
            return ret

        # HEAD request: don't send body
        if self.head_only:
            return None

        if self.stage is not Stage.RESPONSE:
            if size:
                raise RuntimeError("Cannot send data to a closed stream")
            return

        # Chunked encoding
        if self.response_bytes_left is True:
            if end_stream:
                self.response_bytes_left = None
                self.stage = Stage.IDLE
                if size:
                    return b"%x\r\n%b\r\n0\r\n\r\n" % (size, data)
                return b"0\r\n\r\n"
            return b"%x\r\n%b\r\n" % (size, data) if size else None

        # Normal encoding
        else:
            self.response_bytes_left -= size
            if self.response_bytes_left <= 0:
                if self.response_bytes_left < 0:
                    raise ServerError("Response was bigger than content-length")
                self.stage = Stage.IDLE
            return data if size else None
