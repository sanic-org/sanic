from __future__ import annotations

from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from sanic.request import Request
    from sanic.response import BaseHTTPResponse

from asyncio import CancelledError, sleep
from enum import Enum

from sanic.compat import Header
from sanic.exceptions import (
    HeaderExpectationFailed,
    InvalidUsage,
    PayloadTooLarge,
    ServerError,
    ServiceUnavailable,
)
from sanic.headers import format_http1_response
from sanic.helpers import has_message_body
from sanic.log import access_logger, logger


class Stage(Enum):
    """
    Enum for representing the stage of the request/response cycle

    | ``IDLE``  Waiting for request
    | ``REQUEST``  Request headers being received
    | ``HANDLER``  Headers done, handler running
    | ``RESPONSE``  Response headers sent, body in progress
    | ``FAILED``  Unrecoverable state (error while sending response)
    |
    """

    IDLE = 0  # Waiting for request
    REQUEST = 1  # Request headers being received
    HANDLER = 3  # Headers done, handler running
    RESPONSE = 4  # Response headers sent, body in progress
    FAILED = 100  # Unrecoverable state (error while sending response)


HTTP_CONTINUE = b"HTTP/1.1 100 Continue\r\n\r\n"


class Http:
    """
    Internal helper for managing the HTTP request/response cycle

    :raises ServerError:
    :raises PayloadTooLarge:
    :raises Exception:
    :raises InvalidUsage:
    :raises HeaderExpectationFailed:
    :raises RuntimeError:
    :raises ServerError:
    :raises ServerError:
    :raises InvalidUsage:
    :raises InvalidUsage:
    :raises InvalidUsage:
    :raises PayloadTooLarge:
    :raises RuntimeError:
    """

    __slots__ = [
        "_send",
        "_receive_more",
        "recv_buffer",
        "protocol",
        "expecting_continue",
        "stage",
        "keep_alive",
        "head_only",
        "request",
        "exception",
        "url",
        "request_body",
        "request_bytes",
        "request_bytes_left",
        "request_max_size",
        "response",
        "response_func",
        "response_bytes_left",
        "upgrade_websocket",
    ]

    def __init__(self, protocol):
        self._send = protocol.send
        self._receive_more = protocol.receive_more
        self.recv_buffer = protocol.recv_buffer
        self.protocol = protocol
        self.expecting_continue: bool = False
        self.stage: Stage = Stage.IDLE
        self.request_body = None
        self.request_bytes = None
        self.request_bytes_left = None
        self.request_max_size = protocol.request_max_size
        self.keep_alive = True
        self.head_only = None
        self.request: Request = None
        self.response: BaseHTTPResponse = None
        self.exception = None
        self.url = None
        self.upgrade_websocket = False

    def __bool__(self):
        """Test if request handling is in progress"""
        return self.stage in (Stage.HANDLER, Stage.RESPONSE)

    async def http1(self):
        """
        HTTP 1.1 connection handler
        """
        while True:  # As long as connection stays keep-alive
            try:
                # Receive and handle a request
                self.stage = Stage.REQUEST
                self.response_func = self.http1_response_header

                await self.http1_request_header()

                self.request.conn_info = self.protocol.conn_info
                await self.protocol.request_handler(self.request)

                # Handler finished, response should've been sent
                if self.stage is Stage.HANDLER and not self.upgrade_websocket:
                    raise ServerError("Handler produced no response")

                if self.stage is Stage.RESPONSE:
                    await self.response.send(end_stream=True)
            except CancelledError:
                # Write an appropriate response before exiting
                e = self.exception or ServiceUnavailable("Cancelled")
                self.exception = None
                self.keep_alive = False
                await self.error_response(e)
            except Exception as e:
                # Write an error response
                await self.error_response(e)

            # Try to consume any remaining request body
            if self.request_body:
                if self.response and 200 <= self.response.status < 300:
                    logger.error(f"{self.request} body not consumed.")

                try:
                    async for _ in self:
                        pass
                except PayloadTooLarge:
                    # We won't read the body and that may cause httpx and
                    # tests to fail. This little delay allows clients to push
                    # a small request into network buffers before we close the
                    # socket, so that they are then able to read the response.
                    await sleep(0.001)
                    self.keep_alive = False

            # Exit and disconnect if no more requests can be taken
            if self.stage is not Stage.IDLE or not self.keep_alive:
                break

            # Wait for next request
            if not self.recv_buffer:
                await self._receive_more()

    async def http1_request_header(self):
        """
        Receive and parse request header into self.request.
        """
        HEADER_MAX_SIZE = min(8192, self.request_max_size)
        # Receive until full header is in buffer
        buf = self.recv_buffer
        pos = 0

        while True:
            pos = buf.find(b"\r\n\r\n", pos)
            if pos != -1:
                break

            pos = max(0, len(buf) - 3)
            if pos >= HEADER_MAX_SIZE:
                break

            await self._receive_more()

        if pos >= HEADER_MAX_SIZE:
            raise PayloadTooLarge("Request header exceeds the size limit")

        # Parse header content
        try:
            head = buf[:pos]
            raw_headers = head.decode(errors="surrogateescape")
            reqline, *split_headers = raw_headers.split("\r\n")
            method, self.url, protocol = reqline.split(" ")

            if protocol == "HTTP/1.1":
                self.keep_alive = True
            elif protocol == "HTTP/1.0":
                self.keep_alive = False
            else:
                raise Exception  # Raise a Bad Request on try-except

            self.head_only = method.upper() == "HEAD"
            request_body = False
            headers = []

            for name, value in (h.split(":", 1) for h in split_headers):
                name, value = h = name.lower(), value.lstrip()

                if name in ("content-length", "transfer-encoding"):
                    request_body = True
                elif name == "connection":
                    self.keep_alive = value.lower() == "keep-alive"

                headers.append(h)
        except Exception:
            raise InvalidUsage("Bad Request")

        headers_instance = Header(headers)
        self.upgrade_websocket = headers_instance.get("upgrade") == "websocket"

        # Prepare a Request object
        request = self.protocol.request_class(
            url_bytes=self.url.encode(),
            headers=headers_instance,
            head=bytes(head),
            version=protocol[5:],
            method=method,
            transport=self.protocol.transport,
            app=self.protocol.app,
        )

        # Prepare for request body
        self.request_bytes_left = self.request_bytes = 0
        if request_body:
            headers = request.headers
            expect = headers.get("expect")

            if expect is not None:
                if expect.lower() == "100-continue":
                    self.expecting_continue = True
                else:
                    raise HeaderExpectationFailed(f"Unknown Expect: {expect}")

            if headers.get("transfer-encoding") == "chunked":
                self.request_body = "chunked"
                pos -= 2  # One CRLF stays in buffer
            else:
                self.request_body = True
                self.request_bytes_left = self.request_bytes = int(
                    headers["content-length"]
                )

        # Remove header and its trailing CRLF
        del buf[: pos + 4]
        self.stage = Stage.HANDLER
        self.request, request.stream = request, self
        self.protocol.state["requests_count"] += 1

    async def http1_response_header(
        self, data: bytes, end_stream: bool
    ) -> None:
        res = self.response

        # Compatibility with simple response body
        if not data and getattr(res, "body", None):
            data, end_stream = res.body, True  # type: ignore

        size = len(data)
        headers = res.headers
        status = res.status

        if not isinstance(status, int) or status < 200:
            raise RuntimeError(f"Invalid response status {status!r}")

        if not has_message_body(status):
            # Header-only response status
            self.response_func = None
            if (
                data
                or not end_stream
                or "content-length" in headers
                or "transfer-encoding" in headers
            ):
                data, size, end_stream = b"", 0, True
                headers.pop("content-length", None)
                headers.pop("transfer-encoding", None)
                logger.warning(
                    f"Message body set in response on {self.request.path}. "
                    f"A {status} response may only have headers, no body."
                )
        elif self.head_only and "content-length" in headers:
            self.response_func = None
        elif end_stream:
            # Non-streaming response (all in one block)
            headers["content-length"] = size
            self.response_func = None
        elif "content-length" in headers:
            # Streaming response with size known in advance
            self.response_bytes_left = int(headers["content-length"]) - size
            self.response_func = self.http1_response_normal
        else:
            # Length not known, use chunked encoding
            headers["transfer-encoding"] = "chunked"
            data = b"%x\r\n%b\r\n" % (size, data) if size else b""
            self.response_func = self.http1_response_chunked

        if self.head_only:
            # Head request: don't send body
            data = b""
            self.response_func = self.head_response_ignored

        headers["connection"] = "keep-alive" if self.keep_alive else "close"
        ret = format_http1_response(status, res.processed_headers)
        if data:
            ret += data

        # Send a 100-continue if expected and not Expectation Failed
        if self.expecting_continue:
            self.expecting_continue = False
            if status != 417:
                ret = HTTP_CONTINUE + ret

        # Send response
        if self.protocol.access_log:
            self.log_response()

        await self._send(ret)
        self.stage = Stage.IDLE if end_stream else Stage.RESPONSE

    def head_response_ignored(self, data: bytes, end_stream: bool) -> None:
        """
        HEAD response: body data silently ignored.
        """
        if end_stream:
            self.response_func = None
            self.stage = Stage.IDLE

    async def http1_response_chunked(
        self, data: bytes, end_stream: bool
    ) -> None:
        """
        Format a part of response body in chunked encoding.
        """
        # Chunked encoding
        size = len(data)
        if end_stream:
            await self._send(
                b"%x\r\n%b\r\n0\r\n\r\n" % (size, data)
                if size
                else b"0\r\n\r\n"
            )
            self.response_func = None
            self.stage = Stage.IDLE
        elif size:
            await self._send(b"%x\r\n%b\r\n" % (size, data))

    async def http1_response_normal(
        self, data: bytes, end_stream: bool
    ) -> None:
        """
        Format / keep track of non-chunked response.
        """
        bytes_left = self.response_bytes_left - len(data)
        if bytes_left <= 0:
            if bytes_left < 0:
                raise ServerError("Response was bigger than content-length")

            await self._send(data)
            self.response_func = None
            self.stage = Stage.IDLE
        else:
            if end_stream:
                raise ServerError("Response was smaller than content-length")

            await self._send(data)
        self.response_bytes_left = bytes_left

    async def error_response(self, exception: Exception) -> None:
        """
        Handle response when exception encountered
        """
        # Disconnect after an error if in any other state than handler
        if self.stage is not Stage.HANDLER:
            self.keep_alive = False

        # Request failure? Respond but then disconnect
        if self.stage is Stage.REQUEST:
            self.stage = Stage.HANDLER

        # From request and handler states we can respond, otherwise be silent
        if self.stage is Stage.HANDLER:
            app = self.protocol.app

            if self.request is None:
                self.create_empty_request()

            await app.handle_exception(self.request, exception)

    def create_empty_request(self) -> None:
        """
        Current error handling code needs a request object that won't exist
        if an error occurred during before a request was received. Create a
        bogus response for error handling use.
        """

        # FIXME: Avoid this by refactoring error handling and response code
        self.request = self.protocol.request_class(
            url_bytes=self.url.encode() if self.url else b"*",
            headers=Header({}),
            version="1.1",
            method="NONE",
            transport=self.protocol.transport,
            app=self.protocol.app,
        )
        self.request.stream = self

    def log_response(self) -> None:
        """
        Helper method provided to enable the logging of responses in case if
        the :attr:`HttpProtocol.access_log` is enabled.
        """
        req, res = self.request, self.response
        extra = {
            "status": getattr(res, "status", 0),
            "byte": getattr(self, "response_bytes_left", -1),
            "host": "UNKNOWN",
            "request": "nil",
        }
        if req is not None:
            if req.ip:
                extra["host"] = f"{req.ip}:{req.port}"
            extra["request"] = f"{req.method} {req.url}"
        access_logger.info("", extra=extra)

    # Request methods

    async def __aiter__(self):
        """
        Async iterate over request body.
        """
        while self.request_body:
            data = await self.read()

            if data:
                yield data

    async def read(self) -> Optional[bytes]:
        """
        Read some bytes of request body.
        """

        # Send a 100-continue if needed
        if self.expecting_continue:
            self.expecting_continue = False
            await self._send(HTTP_CONTINUE)

        # Receive request body chunk
        buf = self.recv_buffer
        if self.request_bytes_left == 0 and self.request_body == "chunked":
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
            except Exception:
                self.keep_alive = False
                raise InvalidUsage("Bad chunked encoding")

            del buf[: pos + 2]

            if size <= 0:
                self.request_body = None

                if size < 0:
                    self.keep_alive = False
                    raise InvalidUsage("Bad chunked encoding")

                return None

            self.request_bytes_left = size
            self.request_bytes += size

        # Request size limit
        if self.request_bytes > self.request_max_size:
            self.keep_alive = False
            raise PayloadTooLarge("Request body exceeds the size limit")

        # End of request body?
        if not self.request_bytes_left:
            self.request_body = None
            return None

        # At this point we are good to read/return up to request_bytes_left
        if not buf:
            await self._receive_more()

        data = bytes(buf[: self.request_bytes_left])
        size = len(data)

        del buf[:size]

        self.request_bytes_left -= size

        return data

    # Response methods

    def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        """
        Initiate new streaming response.

        Nothing is sent until the first send() call on the returned object, and
        calling this function multiple times will just alter the response to be
        given.
        """
        if self.stage is not Stage.HANDLER:
            self.stage = Stage.FAILED
            raise RuntimeError("Response already started")

        self.response, response.stream = response, self
        return response

    @property
    def send(self):
        return self.response_func
