from sanic.headers import format_http1, format_http1_response
from sanic.helpers import has_message_body, remove_entity_headers


# FIXME: Put somewhere before response:
if False:
    # Middleware has a chance to replace or modify the response
    response = await self.app._run_response_middleware(
        request, response
    )

class H1Stream:
    __slots__ = ("stream", "length", "pos", "set_timeout", "response_state", "status", "headers", "bytes_left")

    def __init__(self, headers, stream, need_continue):
        self.length = int(headers.get("content-length", "0"))
        assert self.length >= 0
        self.pos = None if need_continue else 0
        self.stream = stream
        self.status = self.bytes_left = None
        self.response_state = 0

    async def aclose(self):
        # Finish sending a response (if no error)
        if self.response_state < 2:
            await self.send(end_stream=True)
        # Response fully sent, request fully read?
        if self.pos != self.length or self.response_state != 2:
            await self.stream.aclose()  # If not, must disconnect :(

    # Request methods

    def dont_continue(self):
        """Prevent a pending 100 Continue response being sent, and avoid
        receiving the request body. Does not by itself send a 417 response."""
        if self.pos is None:
            self.pos = self.length = 0

    async def trigger_continue(self):
        if self.pos is None:
            self.pos = 0
            await self.stream.send_all(b"HTTP/1.1 100 Continue\r\n\r\n")

    async def __aiter__(self):
        while True:
            data = await self.read()
            if not data:
                return
            yield data

    async def read(self):
        await self.trigger_continue()
        if self.pos == self.length:
            return None
        buf = await self.stream.receive_some()
        if len(buf) > self.length:
            self.stream.push_back(buf[self.length :])
            buf = buf[: self.length]
        self.pos += len(buf)
        return buf

    # Response methods

    def respond(self, status, headers):
        if self.response_state > 0:
            self.response_state = 3  # FAIL mode
            raise RuntimeError("Response already started")
        self.status = status
        self.headers = headers
        return self

    async def send(self, data=None, data_bytes=None, end_stream=False):
        """Send any pending response headers and the given data as body.
         :param data: str-convertible data to be written
         :param data_bytes: bytes-ish data to be written (used if data is None)
         :end_stream: whether to close the stream after this block
        """
        data = self.data_to_send(data, data_bytes, end_stream)
        if data is None:
            return
        # Check if the request expects a 100-continue first
        if self.pos is None:
            if self.status == 417:
                self.dont_continue()
            else:
                await self.trigger_continue()
        # Send response
        await self.stream.send_all(data)

    def data_to_send(self, data, data_bytes, end_stream):
        """Format output data bytes for given body data.
        Headers are prepended to the first output block and then cleared.
         :param data: str-convertible data to be written
         :param data_bytes: bytes-ish data to be written (used if data is None)
         :return: bytes to send, or None if there is nothing to send
        """
        data = data_bytes if data is None else f"{data}".encode()
        size = len(data) if data is not None else 0

        # Headers not yet sent?
        if self.response_state == 0:
            status, headers = self.status, self.headers
            if status in (304, 412):
                headers = remove_entity_headers(headers)
            if not has_message_body(status):
                # Header-only response status
                assert (
                    size == 0 and end_stream
                ), f"A {status} response may only have headers, no body."
                assert "content-length" not in self.headers
                assert "transfer-encoding" not in self.headers
            elif end_stream:
                # Non-streaming response (all in one block)
                headers["content-length"] = size
            elif "content-length" in headers:
                # Streaming response with size known in advance
                self.bytes_left = int(headers["content-length"]) - size
                assert self.bytes_left >= 0
            else:
                # Length not known, use chunked encoding
                headers["transfer-encoding"] = "chunked"
                data = b"%x\r\n%b\r\n" % (size, data) if size else None
                self.bytes_left = ...
            self.status = self.headers = None
            self.response_state = 2 if end_stream else 1
            return format_http1_response(status, headers.items(), data)

        if self.response_state == 2:
            if size:
                raise RuntimeError("Cannot send data to a closed stream")
            return

        self.response_state = 2 if end_stream else 1

        # Chunked encoding
        if self.bytes_left is ...:
            if end_stream:
                self.bytes_left = None
                if size:
                    return b"%x\r\n%b\r\n0\r\n\r\n" % (size, data)
                return b"0\r\n\r\n"
            return b"%x\r\n%b\r\n" % (size, data) if size else None

        # Normal encoding
        if isinstance(self.bytes_left, int):
            self.bytes_left -= size
            assert self.bytes_left >= 0
            return data if size else None
