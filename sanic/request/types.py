from __future__ import annotations

from asyncio import BaseProtocol
from contextvars import ContextVar
from inspect import isawaitable
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Generic,
    Optional,
    Union,
    cast,
)

from sanic_routing.route import Route
from typing_extensions import TypeVar

from sanic.http.constants import HTTP  # type: ignore
from sanic.http.stream import Stream
from sanic.models.asgi import ASGIScope
from sanic.models.http_types import Credentials


if TYPE_CHECKING:
    from sanic.app import Sanic
    from sanic.config import Config
    from sanic.server import ConnInfo

import uuid

from collections import defaultdict
from urllib.parse import parse_qs, parse_qsl, urlunparse

from httptools import parse_url
from httptools.parser.errors import HttpParserInvalidURLError

from sanic.compat import CancelledErrors, Header
from sanic.constants import (
    CACHEABLE_HTTP_METHODS,
    DEFAULT_HTTP_CONTENT_TYPE,
    IDEMPOTENT_HTTP_METHODS,
    SAFE_HTTP_METHODS,
)
from sanic.cookies.request import CookieRequestParameters, parse_cookie
from sanic.exceptions import BadRequest, BadURL, ServerError
from sanic.headers import (
    AcceptList,
    Options,
    parse_accept,
    parse_content_header,
    parse_credentials,
    parse_forwarded,
    parse_host,
    parse_xforwarded,
)
from sanic.http import Stage
from sanic.log import error_logger
from sanic.models.protocol_types import TransportProtocol
from sanic.response import BaseHTTPResponse, HTTPResponse

from .form import parse_multipart_form
from .parameters import RequestParameters


try:
    from ujson import loads as json_loads  # type: ignore
except ImportError:
    from json import loads as json_loads  # type: ignore

if TYPE_CHECKING:
    # The default argument of TypeVar is proposed to be added in Python 3.13
    # by PEP 696 (https://www.python.org/dev/peps/pep-0696/).
    # Therefore, we use typing_extensions.TypeVar for compatibility.
    # For more information, see:
    # https://discuss.python.org/t/pep-696-type-defaults-for-typevarlikes
    sanic_type = TypeVar(
        "sanic_type", bound=Sanic, default=Sanic[Config, SimpleNamespace]
    )
    ctx_type = TypeVar(
        "ctx_type", bound=SimpleNamespace, default=SimpleNamespace
    )
else:
    sanic_type = TypeVar("sanic_type")
    ctx_type = TypeVar("ctx_type")


class Request(Generic[sanic_type, ctx_type]):
    """State of HTTP request.

    Args:
        url_bytes (bytes): Raw URL bytes.
        headers (Header): Request headers.
        version (str): HTTP version.
        method (str): HTTP method.
        transport (TransportProtocol): Transport protocol.
        app (Sanic): Sanic instance.
        head (bytes, optional): Request head. Defaults to `b""`.
        stream_id (int, optional): HTTP/3 stream ID. Defaults to `0`.
    """

    _current: ContextVar[Request] = ContextVar("request")
    _loads = json_loads

    __slots__ = (
        "__weakref__",
        "_cookies",
        "_ctx",
        "_id",
        "_ip",
        "_parsed_url",
        "_port",
        "_protocol",
        "_remote_addr",
        "_request_middleware_started",
        "_response_middleware_started",
        "_scheme",
        "_socket",
        "_stream_id",
        "_match_info",
        "_name",
        "app",
        "body",
        "conn_info",
        "head",
        "headers",
        "method",
        "parsed_accept",
        "parsed_args",
        "parsed_cookies",
        "parsed_credentials",
        "parsed_files",
        "parsed_form",
        "parsed_forwarded",
        "parsed_json",
        "parsed_not_grouped_args",
        "parsed_token",
        "raw_url",
        "responded",
        "route",
        "stream",
        "transport",
        "version",
    )

    def __init__(
        self,
        url_bytes: bytes,
        headers: Header,
        version: str,
        method: str,
        transport: TransportProtocol,
        app: sanic_type,
        head: bytes = b"",
        stream_id: int = 0,
    ):
        self.raw_url = url_bytes
        try:
            self._parsed_url = parse_url(url_bytes)
        except HttpParserInvalidURLError:
            url = url_bytes.decode(errors="backslashreplace")
            raise BadURL(f"Bad URL: {url}")
        self._id: Optional[Union[uuid.UUID, str, int]] = None
        self._name: Optional[str] = None
        self._stream_id = stream_id
        self.app = app

        self.headers = Header(headers)
        self.version = version
        self.method = method
        self.transport = transport
        self.head = head

        # Init but do not inhale
        self.body = b""
        self.conn_info: Optional[ConnInfo] = None
        self._ctx: Optional[ctx_type] = None
        self.parsed_accept: Optional[AcceptList] = None
        self.parsed_args: DefaultDict[
            tuple[bool, bool, str, str], RequestParameters
        ] = defaultdict(RequestParameters)
        self.parsed_cookies: Optional[RequestParameters] = None
        self.parsed_credentials: Optional[Credentials] = None
        self.parsed_files: Optional[RequestParameters] = None
        self.parsed_form: Optional[RequestParameters] = None
        self.parsed_forwarded: Optional[Options] = None
        self.parsed_json = None
        self.parsed_not_grouped_args: DefaultDict[
            tuple[bool, bool, str, str], list[tuple[str, str]]
        ] = defaultdict(list)
        self.parsed_token: Optional[str] = None
        self._request_middleware_started = False
        self._response_middleware_started = False
        self.responded: bool = False
        self.route: Optional[Route] = None
        self.stream: Optional[Stream] = None
        self._match_info: dict[str, Any] = {}
        self._protocol: Optional[BaseProtocol] = None

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"<{class_name}: {self.method} {self.path}>"

    @staticmethod
    def make_context() -> ctx_type:
        """Create a new context object.

        This method is called when a new request context is pushed. It is
        a great candidate for overriding in a subclass if you want to
        control the type of context object that is created.

        By default, it returns a `types.SimpleNamespace` instance.

        Returns:
            ctx_type: A new context object.
        """
        return cast(ctx_type, SimpleNamespace())

    @classmethod
    def get_current(cls) -> Request:
        """Retrieve the current request object

        This implements [Context Variables](https://docs.python.org/3/library/contextvars.html)
        to allow for accessing the current request from anywhere.

        A typical usecase is when you want to access the current request
        from a function that is not a handler, such as a logging function:

        ```python
        import logging

        class LoggingFormater(logging.Formatter):
            def format(self, record):
                request = Request.get_current()
                record.url = request.url
                record.ip = request.ip
                return super().format(record)
        ```

        Returns:
            Request: The current request object

        Raises:
            sanic.exceptions.ServerError: If it is outside of a request
                lifecycle.
        """  # noqa: E501
        request = cls._current.get(None)
        if not request:
            raise ServerError("No current request")
        return request

    @classmethod
    def generate_id(*_) -> Union[uuid.UUID, str, int]:
        """Generate a unique ID for the request.

        This method is called to generate a unique ID for each request.
        By default, it returns a `uuid.UUID` instance.

        Returns:
            Union[uuid.UUID, str, int]: A unique ID for the request.
        """
        return uuid.uuid4()

    @property
    def ctx(self) -> ctx_type:
        """The current request context.

        This is a context object for the current request. It is created
        by `Request.make_context` and is a great place to store data
        that you want to be accessible during the request lifecycle.

        Returns:
            ctx_type: The current request context.
        """
        if not self._ctx:
            self._ctx = self.make_context()
        return self._ctx

    @property
    def stream_id(self) -> int:
        """Access the HTTP/3 stream ID.

        Raises:
            sanic.exceptions.ServerError: If the request is not HTTP/3.

        Returns:
            int: The HTTP/3 stream ID.
        """
        if self.protocol.version is not HTTP.VERSION_3:
            raise ServerError(
                "Stream ID is only a property of a HTTP/3 request"
            )
        return self._stream_id

    def reset_response(self) -> None:
        """Reset the response object.

        This clears much of the state of the object. It should
        generally not be called directly, but is called automatically as
        part of the request lifecycle.

        Raises:
            sanic.exceptions.ServerError: If the response has already been
                sent.
        """
        try:
            if (
                self.stream is not None
                and self.stream.stage is not Stage.HANDLER
            ):
                raise ServerError(
                    "Cannot reset response because previous response was sent."
                )
            self.stream.response.stream = None  # type: ignore
            self.stream.response = None  # type: ignore
            self.responded = False
        except AttributeError:
            pass

    async def respond(
        self,
        response: Optional[BaseHTTPResponse] = None,
        *,
        status: int = 200,
        headers: Optional[Union[Header, dict[str, str]]] = None,
        content_type: Optional[str] = None,
    ):
        """Respond to the request without returning.

        This method can only be called once, as you can only respond once.
        If no ``response`` argument is passed, one will be created from the
        ``status``, ``headers`` and ``content_type`` arguments.

        **The first typical usecase** is if you wish to respond to the
        request without returning from the handler:

        ```python
        @app.get("/")
        async def handler(request: Request):
            data = ...  # Process something

            json_response = json({"data": data})
            await request.respond(json_response)

        @app.on_response
        async def add_header(_, response: HTTPResponse):
            # Middlewares still get executed as expected
            response.headers["one"] = "two"
        ```

        **The second possible usecase** is for when you want to directly
        respond to the request:

        ```python
        response = await request.respond(content_type="text/csv")
        await response.send("foo,")
        await response.send("bar")

        # You can control the completion of the response by calling
        # the 'eof()' method:
        await response.eof()
        ```

        Args:
            response (ResponseType): Response instance to send.
            status (int): Status code to return in the response.
            headers (Optional[Dict[str, str]]): Headers to return in the response, defaults to None.
            content_type (Optional[str]): Content-Type header of the response, defaults to None.

        Returns:
            FinalResponseType: Final response being sent (may be different from the
                "response" parameter because of middlewares), which can be
                used to manually send data.
        """  # noqa: E501
        try:
            if self.stream is not None and self.stream.response:
                raise ServerError("Second respond call is not allowed.")
        except AttributeError:
            pass
        # This logic of determining which response to use is subject to change
        if response is None:
            response = HTTPResponse(
                status=status,
                headers=headers,
                content_type=content_type,
            )

        # Connect the response
        if isinstance(response, BaseHTTPResponse) and self.stream:
            response = self.stream.respond(response)

            if isawaitable(response):
                response = await response  # type: ignore
        # Run response middleware
        try:
            middleware = (
                self.route and self.route.extra.response_middleware
            ) or self.app.response_middleware
            if middleware and not self._response_middleware_started:
                self._response_middleware_started = True
                response = await self.app._run_response_middleware(
                    self, response, middleware
                )
        except CancelledErrors:
            raise
        except Exception:
            error_logger.exception(
                "Exception occurred in one of response middleware handlers"
            )
        self.responded = True
        return response

    async def receive_body(self):
        """Receive request.body, if not already received.

        Streaming handlers may call this to receive the full body. Sanic calls
        this function before running any handlers of non-streaming routes.

        Custom request classes can override this for custom handling of both
        streaming and non-streaming routes.
        """
        if not self.body:
            self.body = b"".join([data async for data in self.stream])

    @property
    def name(self) -> Optional[str]:
        """The route name

        In the following pattern:

        ```
        <AppName>.[<BlueprintName>.]<HandlerName>
        ```

        Returns:
            Optional[str]: The route name
        """
        if self._name:
            return self._name
        elif self.route:
            return self.route.name
        return None

    @property
    def endpoint(self) -> Optional[str]:
        """Alias of `sanic.request.Request.name`

        Returns:
            Optional[str]: The route name
        """
        return self.name

    @property
    def uri_template(self) -> Optional[str]:
        """The defined URI template

        Returns:
            Optional[str]: The defined URI template
        """
        if self.route:
            return f"/{self.route.path}"
        return None

    @property
    def protocol(self) -> TransportProtocol:
        """The HTTP protocol instance

        Returns:
            Protocol: The HTTP protocol instance
        """
        if not self._protocol:
            self._protocol = self.transport.get_protocol()
        return self._protocol  # type: ignore

    @property
    def raw_headers(self) -> bytes:
        """The unparsed HTTP headers

        Returns:
            bytes: The unparsed HTTP headers
        """
        _, headers = self.head.split(b"\r\n", 1)
        return bytes(headers)

    @property
    def request_line(self) -> bytes:
        """The first line of a HTTP request

        Returns:
            bytes: The first line of a HTTP request
        """
        reqline, _ = self.head.split(b"\r\n", 1)
        return bytes(reqline)

    @property
    def id(self) -> Optional[Union[uuid.UUID, str, int]]:
        """A request ID passed from the client, or generated from the backend.

        By default, this will look in a request header defined at:
        `self.app.config.REQUEST_ID_HEADER`. It defaults to
        `X-Request-ID`. Sanic will try to cast the ID into a `UUID` or an
        `int`.

        If there is not a UUID from the client, then Sanic will try
        to generate an ID by calling `Request.generate_id()`. The default
        behavior is to generate a `UUID`. You can customize this behavior
        by subclassing `Request` and overwriting that method.

        ```python
        from sanic import Request, Sanic
        from itertools import count

        class IntRequest(Request):
            counter = count()

            def generate_id(self):
                return next(self.counter)

        app = Sanic("MyApp", request_class=IntRequest)
        ```

        Returns:
            Optional[Union[uuid.UUID, str, int]]: A request ID passed from the
                client, or generated from the backend.
        """
        if not self._id:
            self._id = self.headers.getone(
                self.app.config.REQUEST_ID_HEADER,
                self.__class__.generate_id(self),  # type: ignore
            )

            # Try casting to a UUID or an integer
            if isinstance(self._id, str):
                try:
                    self._id = uuid.UUID(self._id)
                except ValueError:
                    try:
                        self._id = int(self._id)  # type: ignore
                    except ValueError:
                        ...

        return self._id  # type: ignore

    @property
    def json(self) -> Any:
        """The request body parsed as JSON

        Returns:
            Any: The request body parsed as JSON
        """
        if self.parsed_json is None:
            self.load_json()

        return self.parsed_json

    def load_json(self, loads=None) -> Any:
        """Load the request body as JSON

        Args:
            loads (Callable, optional): A custom JSON loader. Defaults to None.

        Raises:
            BadRequest: If the request body cannot be parsed as JSON

        Returns:
            Any: The request body parsed as JSON
        """
        try:
            if not loads:
                loads = self.__class__._loads

            self.parsed_json = loads(self.body)
        except Exception:
            if not self.body:
                return None
            raise BadRequest("Failed when parsing body as json")

        return self.parsed_json

    @property
    def accept(self) -> AcceptList:
        """Accepted response content types.

        A convenience handler for easier RFC-compliant matching of MIME types,
        parsed as a list that can match wildcards and includes */* by default.

        Returns:
            AcceptList: Accepted response content types
        """
        if self.parsed_accept is None:
            self.parsed_accept = parse_accept(self.headers.get("accept"))
        return self.parsed_accept

    @property
    def token(self) -> Optional[str]:
        """Attempt to return the auth header token.

        Returns:
            Optional[str]: The auth header token
        """
        if self.parsed_token is None:
            prefixes = ("Bearer", "Token")
            _, token = parse_credentials(
                self.headers.getone("authorization", None), prefixes
            )
            self.parsed_token = token
        return self.parsed_token

    @property
    def credentials(self) -> Optional[Credentials]:
        """Attempt to return the auth header value.

        Covers NoAuth, Basic Auth, Bearer Token, Api Token authentication
        schemas.

        Returns:
            Optional[Credentials]: A Credentials object with token, or username
                and password related to the request
        """
        if self.parsed_credentials is None:
            try:
                prefix, credentials = parse_credentials(
                    self.headers.getone("authorization", None)
                )
                if credentials:
                    self.parsed_credentials = Credentials(
                        auth_type=prefix, token=credentials
                    )
            except ValueError:
                pass
        return self.parsed_credentials

    def get_form(
        self, keep_blank_values: bool = False
    ) -> Optional[RequestParameters]:
        """Method to extract and parse the form data from a request.

        Args:
            keep_blank_values (bool): Whether to discard blank values from the form data.

        Returns:
            Optional[RequestParameters]: The parsed form data.
        """  # noqa: E501
        self.parsed_form = RequestParameters()
        self.parsed_files = RequestParameters()
        content_type = self.headers.getone(
            "content-type", DEFAULT_HTTP_CONTENT_TYPE
        )
        content_type, parameters = parse_content_header(content_type)
        try:
            if content_type == "application/x-www-form-urlencoded":
                self.parsed_form = RequestParameters(
                    parse_qs(
                        self.body.decode("utf-8"),
                        keep_blank_values=keep_blank_values,
                    )
                )
            elif content_type == "multipart/form-data":
                # TODO: Stream this instead of reading to/from memory
                boundary = parameters["boundary"].encode(  # type: ignore
                    "utf-8"
                )  # type: ignore
                self.parsed_form, self.parsed_files = parse_multipart_form(
                    self.body, boundary
                )
        except Exception:
            error_logger.exception("Failed when parsing form")

        return self.parsed_form

    @property
    def form(self) -> Optional[RequestParameters]:
        """The request body parsed as form data

        Returns:
            Optional[RequestParameters]: The request body parsed as form data
        """
        if self.parsed_form is None:
            self.get_form()

        return self.parsed_form

    @property
    def files(self) -> Optional[RequestParameters]:
        """The request body parsed as uploaded files

        Returns:
            Optional[RequestParameters]: The request body parsed as uploaded files
        """  # noqa: E501
        if self.parsed_files is None:
            self.form  # compute form to get files

        return self.parsed_files

    def get_args(
        self,
        keep_blank_values: bool = False,
        strict_parsing: bool = False,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> RequestParameters:
        """Parse `query_string` using `urllib.parse.parse_qs`.

        This methods is used by the `args` property, but it also
        can be used directly if you need to change default parameters.

        Args:
            keep_blank_values (bool): Flag indicating whether blank values in
                percent-encoded queries should be treated as blank strings.
                A `True` value indicates that blanks should be retained as
                blank strings. The default `False` value indicates that
                blank values are to be ignored and treated as if they were
                not included.
            strict_parsing (bool): Flag indicating what to do with parsing
                errors. If `False` (the default), errors are silently ignored.
                If `True`, errors raise a `ValueError` exception.
            encoding (str): Specify how to decode percent-encoded sequences
                into Unicode characters, as accepted by the
                `bytes.decode()` method.
            errors (str): Specify how to decode percent-encoded sequences
                into Unicode characters, as accepted by the
                `bytes.decode()` method.

        Returns:
            RequestParameters: A dictionary containing the parsed arguments.
        """
        if (
            keep_blank_values,
            strict_parsing,
            encoding,
            errors,
        ) not in self.parsed_args:
            if self.query_string:
                self.parsed_args[
                    (keep_blank_values, strict_parsing, encoding, errors)
                ] = RequestParameters(
                    parse_qs(
                        qs=self.query_string,
                        keep_blank_values=keep_blank_values,
                        strict_parsing=strict_parsing,
                        encoding=encoding,
                        errors=errors,
                    )
                )

        return self.parsed_args[
            (keep_blank_values, strict_parsing, encoding, errors)
        ]

    args = property(get_args)
    """Convenience property to access `Request.get_args` with default values.
    """

    def get_query_args(
        self,
        keep_blank_values: bool = False,
        strict_parsing: bool = False,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> list:
        """Parse `query_string` using `urllib.parse.parse_qsl`.

        This methods is used by `query_args` propertyn but can be used
        directly if you need to change default parameters.

        Args:
            keep_blank_values (bool): Flag indicating whether blank values in
                percent-encoded queries should be treated as blank strings.
                A `True` value indicates that blanks should be retained as
                blank strings. The default `False` value indicates that
                blank values are to be ignored and treated as if they were
                not included.
            strict_parsing (bool): Flag indicating what to do with
                parsing errors. If `False` (the default), errors are
                silently ignored. If `True`, errors raise a
                `ValueError` exception.
            encoding (str): Specify how to decode percent-encoded sequences
                into Unicode characters, as accepted by the
                `bytes.decode()` method.
            errors (str): Specify how to decode percent-encoded sequences
                into Unicode characters, as accepted by the
                `bytes.decode()` method.

        Returns:
            list: A list of tuples containing the parsed arguments.
        """
        if (
            keep_blank_values,
            strict_parsing,
            encoding,
            errors,
        ) not in self.parsed_not_grouped_args:
            if self.query_string:
                self.parsed_not_grouped_args[
                    (keep_blank_values, strict_parsing, encoding, errors)
                ] = parse_qsl(
                    qs=self.query_string,
                    keep_blank_values=keep_blank_values,
                    strict_parsing=strict_parsing,
                    encoding=encoding,
                    errors=errors,
                )
        return self.parsed_not_grouped_args[
            (keep_blank_values, strict_parsing, encoding, errors)
        ]

    query_args = property(get_query_args)
    """Convenience property to access `Request.get_query_args` with default values.
    """  # noqa: E501

    def get_cookies(self) -> RequestParameters:
        cookie = self.headers.getone("cookie", "")
        self.parsed_cookies = CookieRequestParameters(parse_cookie(cookie))
        return self.parsed_cookies

    @property
    def cookies(self) -> RequestParameters:
        """Incoming cookies on the request

        Returns:
            RequestParameters: Incoming cookies on the request
        """

        if self.parsed_cookies is None:
            self.get_cookies()
        return cast(CookieRequestParameters, self.parsed_cookies)

    @property
    def content_type(self) -> str:
        """Content-Type header form the request

        Returns:
            str: Content-Type header form the request
        """
        return self.headers.getone("content-type", DEFAULT_HTTP_CONTENT_TYPE)

    @property
    def match_info(self) -> dict[str, Any]:
        """Matched path parameters after resolving route

        Returns:
            Dict[str, Any]: Matched path parameters after resolving route
        """
        return self._match_info

    @match_info.setter
    def match_info(self, value):
        self._match_info = value

    @property
    def ip(self) -> str:
        """Peer ip of the socket

        Returns:
            str: Peer ip of the socket
        """
        return self.conn_info.client_ip if self.conn_info else ""

    @property
    def port(self) -> int:
        """Peer port of the socket

        Returns:
            int: Peer port of the socket
        """
        return self.conn_info.client_port if self.conn_info else 0

    @property
    def socket(self) -> Union[tuple[str, int], tuple[None, None]]:
        """Information about the connected socket if available

        Returns:
            Tuple[Optional[str], Optional[int]]: Information about the
                connected socket if available, in the form of a tuple of
                (ip, port)
        """
        return (
            self.conn_info.peername
            if self.conn_info and self.conn_info.peername
            else (None, None)
        )

    @property
    def path(self) -> str:
        """Path of the local HTTP request

        Returns:
            str: Path of the local HTTP request
        """
        return self._parsed_url.path.decode("utf-8")

    @property
    def network_paths(self) -> Optional[list[Any]]:
        """Access the network paths if available

        Returns:
            Optional[List[Any]]: Access the network paths if available
        """
        if self.conn_info is None:
            return None
        return self.conn_info.network_paths

    # Proxy properties (using SERVER_NAME/forwarded/request/transport info)

    @property
    def forwarded(self) -> Options:
        """Active proxy information obtained from request headers, as specified in Sanic configuration.

        Field names by, for, proto, host, port and path are normalized.
        - for and by IPv6 addresses are bracketed
        - port (int) is only set by port headers, not from host.
        - path is url-unencoded

        Additional values may be available from new style Forwarded headers.

        Returns:
            Options: proxy information from request headers
        """  # noqa: E501
        if self.parsed_forwarded is None:
            self.parsed_forwarded = (
                parse_forwarded(self.headers, self.app.config)
                or parse_xforwarded(self.headers, self.app.config)
                or {}
            )
        return self.parsed_forwarded

    @property
    def remote_addr(self) -> str:
        """Client IP address, if available from proxy.

        Returns:
            str: IPv4, bracketed IPv6, UNIX socket name or arbitrary string
        """
        if not hasattr(self, "_remote_addr"):
            self._remote_addr = str(self.forwarded.get("for", ""))
        return self._remote_addr

    @property
    def client_ip(self) -> str:
        """
        Client IP address.
        1. proxied remote address `self.forwarded['for']`
        2. local peer address `self.ip`

        New in Sanic 23.6. Prefer this over `remote_addr` for determining the
        client address regardless of whether the service runs behind a proxy
        or not (proxy deployment needs separate configuration).

        Returns:
            str: IPv4, bracketed IPv6, UNIX socket name or arbitrary string
        """
        return self.remote_addr or self.ip

    @property
    def scheme(self) -> str:
        """Determine request scheme.

        1. `config.SERVER_NAME` if in full URL format
        2. proxied proto/scheme
        3. local connection protocol

        Returns:
            str: http|https|ws|wss or arbitrary value given by the headers.
        """
        if not hasattr(self, "_scheme"):
            if (
                self.app.websocket_enabled
                and self.headers.upgrade.lower() == "websocket"
            ):
                scheme = "ws"
            else:
                scheme = "http"
            proto = None
            sp = self.app.config.get("SERVER_NAME", "").split("://", 1)
            if len(sp) == 2:
                proto = sp[0]
            elif "proto" in self.forwarded:
                proto = str(self.forwarded["proto"])
            if proto:
                # Give ws/wss if websocket, otherwise keep the same
                scheme = proto.replace("http", scheme)
            elif self.conn_info and self.conn_info.ssl:
                scheme += "s"
            self._scheme = scheme

        return self._scheme

    @property
    def host(self) -> str:
        """The currently effective server 'host' (hostname or hostname:port).

        1. `config.SERVER_NAME` overrides any client headers
        2. proxied host of original request
        3. request host header
        hostname and port may be separated by
        `sanic.headers.parse_host(request.host)`.

        Returns:
            str: the first matching host found, or empty string
        """
        server_name = self.app.config.get("SERVER_NAME")
        if server_name:
            return server_name.split("//", 1)[-1].split("/", 1)[0]
        return str(
            self.forwarded.get("host") or self.headers.getone("host", "")
        )

    @property
    def server_name(self) -> str:
        """hostname the client connected to, by `request.host`

        Returns:
            str: hostname the client connected to, by `request.host`
        """
        return parse_host(self.host)[0] or ""

    @property
    def server_port(self) -> int:
        """The port the client connected to, by forwarded `port` or `request.host`.

        Default port is returned as 80 and 443 based on `request.scheme`.

        Returns:
            int: The port the client connected to, by forwarded `port` or `request.host`.
        """  # noqa: E501
        port = self.forwarded.get("port") or parse_host(self.host)[1]
        return int(port or (80 if self.scheme in ("http", "ws") else 443))

    @property
    def server_path(self) -> str:
        """Full path of current URL; uses proxied or local path

        Returns:
            str: Full path of current URL; uses proxied or local path
        """
        return str(self.forwarded.get("path") or self.path)

    @property
    def query_string(self) -> str:
        """Representation of the requested query

        Returns:
            str: Representation of the requested query
        """
        if self._parsed_url.query:
            return self._parsed_url.query.decode("utf-8")
        else:
            return ""

    @property
    def url(self) -> str:
        """The URL

        Returns:
            str: The URL
        """
        return urlunparse(
            (self.scheme, self.host, self.path, None, self.query_string, None)
        )

    def url_for(self, view_name: str, **kwargs) -> str:
        """Retrieve a URL for a given view name.

        Same as `sanic.Sanic.url_for`, but automatically determine `scheme`
        and `netloc` base on the request. Since this method is aiming
        to generate correct schema & netloc, `_external` is implied.

        Args:
            view_name (str): The view name to generate URL for.
            **kwargs: Arbitrary keyword arguments to build URL query string.

        Returns:
            str: The generated URL.
        """
        # Full URL SERVER_NAME can only be handled in app.url_for
        try:
            sp = self.app.config.get("SERVER_NAME", "").split("://", 1)
            if len(sp) == 2:
                return self.app.url_for(view_name, _external=True, **kwargs)
        except AttributeError:
            pass

        scheme = self.scheme
        host = self.server_name
        port = self.server_port

        if (scheme.lower() in ("http", "ws") and port == 80) or (
            scheme.lower() in ("https", "wss") and port == 443
        ):
            netloc = host
        else:
            netloc = f"{host}:{port}"

        return self.app.url_for(
            view_name, _external=True, _scheme=scheme, _server=netloc, **kwargs
        )

    @property
    def scope(self) -> ASGIScope:
        """The ASGI scope of the request.

        Returns:
            ASGIScope: The ASGI scope of the request.

        Raises:
            NotImplementedError: If the app isn't an ASGI app.
        """
        if not self.app.asgi:
            raise NotImplementedError(
                "App isn't running in ASGI mode. "
                "Scope is only available for ASGI apps."
            )

        return self.transport.scope

    @property
    def is_safe(self) -> bool:
        """Whether the HTTP method is safe.

        See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.1

        Returns:
            bool: Whether the HTTP method is safe.
        """
        return self.method in SAFE_HTTP_METHODS

    @property
    def is_idempotent(self) -> bool:
        """Whether the HTTP method is iempotent.

        See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2

        Returns:
            bool: Whether the HTTP method is iempotent.
        """
        return self.method in IDEMPOTENT_HTTP_METHODS

    @property
    def is_cacheable(self) -> bool:
        """Whether the HTTP method is cacheable.

        See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.3

        Returns:
            bool: Whether the HTTP method is cacheable.
        """
        return self.method in CACHEABLE_HTTP_METHODS
