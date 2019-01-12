import asyncio
import traceback

from httptools import HttpRequestParser
from httptools.parser.errors import HttpParserError
from multidict import CIMultiDict

from sanic.exceptions import (
    InvalidUsage,
    PayloadTooLarge,
    RequestTimeout,
    ServerError,
    ServiceUnavailable,
)
from sanic.log import access_logger, logger
from sanic.request import Request, StreamBuffer
from sanic.response import HTTPResponse


try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


current_time = None


class Signal:
    stopped = False


class HttpProtocol(asyncio.Protocol):
    """
    This class provides a basic HTTP implementation of the sanic framework.
    """

    __slots__ = (
        # event loop, connection
        "loop",
        "transport",
        "connections",
        "signal",
        # request params
        "parser",
        "request",
        "url",
        "headers",
        # request config
        "request_handler",
        "request_timeout",
        "response_timeout",
        "keep_alive_timeout",
        "request_max_size",
        "request_buffer_queue_size",
        "request_class",
        "is_request_stream",
        "router",
        "error_handler",
        # enable or disable access log purpose
        "access_log",
        # connection management
        "_total_request_size",
        "_request_timeout_handler",
        "_response_timeout_handler",
        "_keep_alive_timeout_handler",
        "_last_request_time",
        "_last_response_time",
        "_is_stream_handler",
        "_not_paused",
        "_request_handler_task",
        "_request_stream_task",
        "_keep_alive",
        "_header_fragment",
        "state",
        "_debug",
    )

    def __init__(
        self,
        *,
        loop,
        request_handler,
        error_handler,
        signal=Signal(),
        connections=None,
        request_timeout=60,
        response_timeout=60,
        keep_alive_timeout=5,
        request_max_size=None,
        request_buffer_queue_size=100,
        request_class=None,
        access_log=True,
        keep_alive=True,
        is_request_stream=False,
        router=None,
        state=None,
        debug=False,
        **kwargs
    ):
        self.loop = loop
        self.transport = None
        self.request = None
        self.parser = None
        self.url = None
        self.headers = None
        self.router = router
        self.signal = signal
        self.access_log = access_log
        self.connections = connections or set()
        self.request_handler = request_handler
        self.error_handler = error_handler
        self.request_timeout = request_timeout
        self.request_buffer_queue_size = request_buffer_queue_size
        self.response_timeout = response_timeout
        self.keep_alive_timeout = keep_alive_timeout
        self.request_max_size = request_max_size
        self.request_class = request_class or Request
        self.is_request_stream = is_request_stream
        self._is_stream_handler = False
        self._not_paused = asyncio.Event(loop=loop)
        self._total_request_size = 0
        self._request_timeout_handler = None
        self._response_timeout_handler = None
        self._keep_alive_timeout_handler = None
        self._last_request_time = None
        self._last_response_time = None
        self._request_handler_task = None
        self._request_stream_task = None
        self._keep_alive = keep_alive
        self._header_fragment = b""
        self.state = state if state else {}
        if "requests_count" not in self.state:
            self.state["requests_count"] = 0
        self._debug = debug
        self._not_paused.set()

    @property
    def keep_alive(self):
        """
        Check if the connection needs to be kept alive based on the params
        attached to the `_keep_alive` attribute, :attr:`Signal.stopped`
        and :func:`HttpProtocol.parser.should_keep_alive`

        :return: ``True`` if connection is to be kept alive ``False`` else
        """
        return (
            self._keep_alive
            and not self.signal.stopped
            and self.parser.should_keep_alive()
        )

    # -------------------------------------------- #
    # Connection
    # -------------------------------------------- #

    def connection_made(self, transport):
        self.connections.add(self)
        self._request_timeout_handler = self.loop.call_later(
            self.request_timeout, self.request_timeout_callback
        )
        self.transport = transport
        self._last_request_time = current_time

    def connection_lost(self, exc):
        self.connections.discard(self)
        if self._request_handler_task:
            self._request_handler_task.cancel()
        if self._request_stream_task:
            self._request_stream_task.cancel()
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()

    def pause_writing(self):
        self._not_paused.clear()

    def resume_writing(self):
        self._not_paused.set()

    def request_timeout_callback(self):
        # See the docstring in the RequestTimeout exception, to see
        # exactly what this timeout is checking for.
        # Check if elapsed time since request initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.request_timeout:
            time_left = self.request_timeout - time_elapsed
            self._request_timeout_handler = self.loop.call_later(
                time_left, self.request_timeout_callback
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            self.write_error(RequestTimeout("Request Timeout"))

    def response_timeout_callback(self):
        # Check if elapsed time since response was initiated exceeds our
        # configured maximum request timeout value
        time_elapsed = current_time - self._last_request_time
        if time_elapsed < self.response_timeout:
            time_left = self.response_timeout - time_elapsed
            self._response_timeout_handler = self.loop.call_later(
                time_left, self.response_timeout_callback
            )
        else:
            if self._request_stream_task:
                self._request_stream_task.cancel()
            if self._request_handler_task:
                self._request_handler_task.cancel()
            self.write_error(ServiceUnavailable("Response Timeout"))

    def keep_alive_timeout_callback(self):
        """
        Check if elapsed time since last response exceeds our configured
        maximum keep alive timeout value and if so, close the transport
        pipe and let the response writer handle the error.

        :return: None
        """
        time_elapsed = current_time - self._last_response_time
        if time_elapsed < self.keep_alive_timeout:
            time_left = self.keep_alive_timeout - time_elapsed
            self._keep_alive_timeout_handler = self.loop.call_later(
                time_left, self.keep_alive_timeout_callback
            )
        else:
            logger.debug("KeepAlive Timeout. Closing connection.")
            self.transport.close()
            self.transport = None

    # -------------------------------------------- #
    # Parsing
    # -------------------------------------------- #

    def data_received(self, data):
        # Check for the request itself getting too large and exceeding
        # memory limits
        self._total_request_size += len(data)
        if self._total_request_size > self.request_max_size:
            self.write_error(PayloadTooLarge("Payload Too Large"))

        # Create parser if this is the first time we're receiving data
        if self.parser is None:
            assert self.request is None
            self.headers = []
            self.parser = HttpRequestParser(self)

        # requests count
        self.state["requests_count"] = self.state["requests_count"] + 1

        # Parse request chunk or close connection
        try:
            self.parser.feed_data(data)
        except HttpParserError:
            message = "Bad Request"
            if self._debug:
                message += "\n" + traceback.format_exc()
            self.write_error(InvalidUsage(message))

    def on_url(self, url):
        if not self.url:
            self.url = url
        else:
            self.url += url

    def on_header(self, name, value):
        self._header_fragment += name

        if value is not None:
            if (
                self._header_fragment == b"Content-Length"
                and int(value) > self.request_max_size
            ):
                self.write_error(PayloadTooLarge("Payload Too Large"))
            try:
                value = value.decode()
            except UnicodeDecodeError:
                value = value.decode("latin_1")
            self.headers.append(
                (self._header_fragment.decode().casefold(), value)
            )

            self._header_fragment = b""

    def on_headers_complete(self):
        self.request = self.request_class(
            url_bytes=self.url,
            headers=CIMultiDict(self.headers),
            version=self.parser.get_http_version(),
            method=self.parser.get_method().decode(),
            transport=self.transport,
        )
        # Remove any existing KeepAlive handler here,
        # It will be recreated if required on the new request.
        if self._keep_alive_timeout_handler:
            self._keep_alive_timeout_handler.cancel()
            self._keep_alive_timeout_handler = None
        if self.is_request_stream:
            self._is_stream_handler = self.router.is_stream_handler(
                self.request
            )
            if self._is_stream_handler:
                self.request.stream = StreamBuffer(
                    self.request_buffer_queue_size
                )
                self.execute_request_handler()

    def on_body(self, body):
        if self.is_request_stream and self._is_stream_handler:
            self._request_stream_task = self.loop.create_task(
                self.body_append(body)
            )
        else:
            self.request.body_push(body)

    async def body_append(self, body):
        if self.request.stream.is_full():
            self.transport.pause_reading()
            await self.request.stream.put(body)
            self.transport.resume_reading()
        else:
            await self.request.stream.put(body)

    def on_message_complete(self):
        # Entire request (headers and whole body) is received.
        # We can cancel and remove the request timeout handler now.
        if self._request_timeout_handler:
            self._request_timeout_handler.cancel()
            self._request_timeout_handler = None
        if self.is_request_stream and self._is_stream_handler:
            self._request_stream_task = self.loop.create_task(
                self.request.stream.put(None)
            )
            return
        self.request.body_finish()
        self.execute_request_handler()

    def execute_request_handler(self):
        """
        Invoke the request handler defined by the
        :func:`sanic.app.Sanic.handle_request` method

        :return: None
        """
        self._response_timeout_handler = self.loop.call_later(
            self.response_timeout, self.response_timeout_callback
        )
        self._last_request_time = current_time
        self._request_handler_task = self.loop.create_task(
            self.request_handler(
                self.request, self.write_response, self.stream_response
            )
        )

    # -------------------------------------------- #
    # Responding
    # -------------------------------------------- #
    def log_response(self, response):
        """
        Helper method provided to enable the logging of responses in case if
        the :attr:`HttpProtocol.access_log` is enabled.

        :param response: Response generated for the current request

        :type response: :class:`sanic.response.HTTPResponse` or
            :class:`sanic.response.StreamingHTTPResponse`

        :return: None
        """
        if self.access_log:
            extra = {"status": getattr(response, "status", 0)}

            if isinstance(response, HTTPResponse):
                extra["byte"] = len(response.body)
            else:
                extra["byte"] = -1

            extra["host"] = "UNKNOWN"
            if self.request is not None:
                if self.request.ip:
                    extra["host"] = "{0}:{1}".format(
                        self.request.ip, self.request.port
                    )

                extra["request"] = "{0} {1}".format(
                    self.request.method, self.request.url
                )
            else:
                extra["request"] = "nil"

            access_logger.info("", extra=extra)

    def write_response(self, response):
        """
        Writes response content synchronously to the transport.
        """
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None
        try:
            keep_alive = self.keep_alive
            self.transport.write(
                response.output(
                    self.request.version, keep_alive, self.keep_alive_timeout
                )
            )
            self.log_response(response)
        except AttributeError:
            logger.error(
                "Invalid response object for url %s, "
                "Expected Type: HTTPResponse, Actual Type: %s",
                self.url,
                type(response),
            )
            self.write_error(ServerError("Invalid response type"))
        except RuntimeError:
            if self._debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(repr(e))
            )
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout, self.keep_alive_timeout_callback
                )
                self._last_response_time = current_time
                self.cleanup()

    async def drain(self):
        await self._not_paused.wait()

    def push_data(self, data):
        self.transport.write(data)

    async def stream_response(self, response):
        """
        Streams a response to the client asynchronously. Attaches
        the transport to the response so the response consumer can
        write to the response as needed.
        """
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None

        try:
            keep_alive = self.keep_alive
            response.protocol = self
            await response.stream(
                self.request.version, keep_alive, self.keep_alive_timeout
            )
            self.log_response(response)
        except AttributeError:
            logger.error(
                "Invalid response object for url %s, "
                "Expected Type: HTTPResponse, Actual Type: %s",
                self.url,
                type(response),
            )
            self.write_error(ServerError("Invalid response type"))
        except RuntimeError:
            if self._debug:
                logger.error(
                    "Connection lost before response written @ %s",
                    self.request.ip,
                )
            keep_alive = False
        except Exception as e:
            self.bail_out(
                "Writing response failed, connection closed {}".format(repr(e))
            )
        finally:
            if not keep_alive:
                self.transport.close()
                self.transport = None
            else:
                self._keep_alive_timeout_handler = self.loop.call_later(
                    self.keep_alive_timeout, self.keep_alive_timeout_callback
                )
                self._last_response_time = current_time
                self.cleanup()

    def write_error(self, exception):
        # An error _is_ a response.
        # Don't throw a response timeout, when a response _is_ given.
        if self._response_timeout_handler:
            self._response_timeout_handler.cancel()
            self._response_timeout_handler = None
        response = None
        try:
            response = self.error_handler.response(self.request, exception)
            version = self.request.version if self.request else "1.1"
            self.transport.write(response.output(version))
        except RuntimeError:
            if self._debug:
                logger.error(
                    "Connection lost before error written @ %s",
                    self.request.ip if self.request else "Unknown",
                )
        except Exception as e:
            self.bail_out(
                "Writing error failed, connection closed {}".format(repr(e)),
                from_error=True,
            )
        finally:
            if self.parser and (
                self.keep_alive or getattr(response, "status", 0) == 408
            ):
                self.log_response(response)
            try:
                self.transport.close()
            except AttributeError:
                logger.debug("Connection lost before server could close it.")

    def bail_out(self, message, from_error=False):
        """
        In case if the transport pipes are closed and the sanic app encounters
        an error while writing data to the transport pipe, we log the error
        with proper details.

        :param message: Error message to display
        :param from_error: If the bail out was invoked while handling an
            exception scenario.

        :type message: str
        :type from_error: bool

        :return: None
        """
        if from_error or self.transport.is_closing():
            logger.error(
                "Transport closed @ %s and exception "
                "experienced during error handling",
                self.transport.get_extra_info("peername"),
            )
            logger.debug("Exception:", exc_info=True)
        else:
            self.write_error(ServerError(message))
            logger.error(message)

    def cleanup(self):
        """This is called when KeepAlive feature is used,
        it resets the connection in order for it to be able
        to handle receiving another request on the same connection."""
        self.parser = None
        self.request = None
        self.url = None
        self.headers = None
        self._request_handler_task = None
        self._request_stream_task = None
        self._total_request_size = 0
        self._is_stream_handler = False

    def close_if_idle(self):
        """Close the connection if a request is not being sent or received

        :return: boolean - True if closed, false if staying open
        """
        if not self.parser:
            self.transport.close()
            return True
        return False

    def close(self):
        """
        Force close the connection.
        """
        if self.transport is not None:
            self.transport.close()
            self.transport = None
