from __future__ import annotations

from contextvars import ContextVar
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

from sanic_routing.route import Route

from sanic.http.constants import HTTP  # type: ignore
from sanic.http.stream import Stream
from sanic.models.asgi import ASGIScope
from sanic.models.http_types import Credentials


if TYPE_CHECKING:
    from sanic.server import ConnInfo
    from sanic.app import Sanic

import email.utils
import unicodedata
import uuid

from collections import defaultdict
from http.cookies import SimpleCookie
from types import SimpleNamespace
from urllib.parse import parse_qs, parse_qsl, unquote, urlunparse

from httptools import parse_url
from httptools.parser.errors import HttpParserInvalidURLError

from sanic.compat import CancelledErrors, Header
from sanic.constants import (
    CACHEABLE_HTTP_METHODS,
    DEFAULT_HTTP_CONTENT_TYPE,
    IDEMPOTENT_HTTP_METHODS,
    SAFE_HTTP_METHODS,
)
from sanic.exceptions import BadRequest, BadURL, ServerError
from sanic.headers import (
    AcceptContainer,
    Options,
    parse_accept,
    parse_content_header,
    parse_credentials,
    parse_forwarded,
    parse_host,
    parse_xforwarded,
)
from sanic.http import Stage
from sanic.log import deprecation, error_logger, logger
from sanic.models.protocol_types import TransportProtocol
from sanic.response import BaseHTTPResponse, HTTPResponse


try:
    from ujson import loads as json_loads  # type: ignore
except ImportError:
    from json import loads as json_loads  # type: ignore


class RequestParameters(dict):
    """
    Hosts a dict with lists as values where get returns the first
    value of the list and getlist returns the whole shebang
    """

    def get(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        """Return the first value, either the default or actual"""
        return super().get(name, [default])[0]

    def getlist(
        self, name: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Return the entire list
        """
        return super().get(name, default)


class Request:
    """
    Properties of an HTTP request such as URL, headers, etc.
    """

    _current: ContextVar[Request] = ContextVar("request")
    _loads = json_loads

    __slots__ = (
        "__weakref__",
        "_cookies",
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
        "ctx",
        "head",
        "headers",
        "method",
        "parsed_accept",
        "parsed_args",
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
        app: Sanic,
        head: bytes = b"",
        stream_id: int = 0,
    ):

        self.raw_url = url_bytes
        try:
            self._parsed_url = parse_url(url_bytes)
        except HttpParserInvalidURLError:
            raise BadURL(f"Bad URL: {url_bytes.decode()}")
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
        self.ctx = SimpleNamespace()
        self.parsed_forwarded: Optional[Options] = None
        self.parsed_accept: Optional[AcceptContainer] = None
        self.parsed_credentials: Optional[Credentials] = None
        self.parsed_json = None
        self.parsed_form: Optional[RequestParameters] = None
        self.parsed_files: Optional[RequestParameters] = None
        self.parsed_token: Optional[str] = None
        self.parsed_args: DefaultDict[
            Tuple[bool, bool, str, str], RequestParameters
        ] = defaultdict(RequestParameters)
        self.parsed_not_grouped_args: DefaultDict[
            Tuple[bool, bool, str, str], List[Tuple[str, str]]
        ] = defaultdict(list)
        self._request_middleware_started = False
        self._response_middleware_started = False
        self.responded: bool = False
        self.route: Optional[Route] = None
        self.stream: Optional[Stream] = None
        self._cookies: Optional[Dict[str, str]] = None
        self._match_info: Dict[str, Any] = {}
        self._protocol = None

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"<{class_name}: {self.method} {self.path}>"

    @classmethod
    def get_current(cls) -> Request:
        """
        Retrieve the current request object

        This implements `Context Variables
        <https://docs.python.org/3/library/contextvars.html>`_
        to allow for accessing the current request from anywhere.

        Raises :exc:`sanic.exceptions.ServerError` if it is outside of
        a request lifecycle.

        .. code-block:: python

            from sanic import Request

            current_request = Request.get_current()

        :return: the current :class:`sanic.request.Request`
        """
        request = cls._current.get(None)
        if not request:
            raise ServerError("No current request")
        return request

    @classmethod
    def generate_id(*_):
        return uuid.uuid4()

    @property
    def request_middleware_started(self):
        deprecation(
            "Request.request_middleware_started has been deprecated and will"
            "be removed. You should set a flag on the request context using"
            "either middleware or signals if you need this feature.",
            23.3,
        )
        return self._request_middleware_started

    @property
    def stream_id(self):
        """
        Access the HTTP/3 stream ID.

        Raises :exc:`sanic.exceptions.ServerError` if it is not an
        HTTP/3 request.
        """
        if self.protocol.version is not HTTP.VERSION_3:
            raise ServerError(
                "Stream ID is only a property of a HTTP/3 request"
            )
        return self._stream_id

    def reset_response(self):
        try:
            if (
                self.stream is not None
                and self.stream.stage is not Stage.HANDLER
            ):
                raise ServerError(
                    "Cannot reset response because previous response was sent."
                )
            self.stream.response.stream = None
            self.stream.response = None
            self.responded = False
        except AttributeError:
            pass

    async def respond(
        self,
        response: Optional[BaseHTTPResponse] = None,
        *,
        status: int = 200,
        headers: Optional[Union[Header, Dict[str, str]]] = None,
        content_type: Optional[str] = None,
    ):
        """Respond to the request without returning.

        This method can only be called once, as you can only respond once.
        If no ``response`` argument is passed, one will be created from the
        ``status``, ``headers`` and ``content_type`` arguments.

        **The first typical usecase** is if you wish to respond to the
        request without returning from the handler:

        .. code-block:: python

            @app.get("/")
            async def handler(request: Request):
                data = ...  # Process something

                json_response = json({"data": data})
                await request.respond(json_response)

                # You are now free to continue executing other code
                ...

            @app.on_response
            async def add_header(_, response: HTTPResponse):
                # Middlewares still get executed as expected
                response.headers["one"] = "two"

        **The second possible usecase** is for when you want to directly
        respond to the request:

        .. code-block:: python

            response = await request.respond(content_type="text/csv")
            await response.send("foo,")
            await response.send("bar")

            # You can control the completion of the response by calling
            # the 'eof()' method:
            await response.eof()

        :param response: response instance to send
        :param status: status code to return in the response
        :param headers: headers to return in the response
        :param content_type: Content-Type header of the response
        :return: final response being sent (may be different from the
            ``response`` parameter because of middlewares) which can be
            used to manually send data
        """
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
        """
        The route name

        In the following pattern:

        .. code-block::

            <AppName>.[<BlueprintName>.]<HandlerName>

        :return: Route name
        :rtype: Optional[str]
        """
        if self._name:
            return self._name
        elif self.route:
            return self.route.name
        return None

    @property
    def endpoint(self) -> Optional[str]:
        """
        :return: Alias of :attr:`sanic.request.Request.name`
        :rtype: Optional[str]
        """
        return self.name

    @property
    def uri_template(self) -> Optional[str]:
        """
        :return: The defined URI template
        :rtype: Optional[str]
        """
        if self.route:
            return f"/{self.route.path}"
        return None

    @property
    def protocol(self):
        """
        :return: The HTTP protocol instance
        """
        if not self._protocol:
            self._protocol = self.transport.get_protocol()
        return self._protocol

    @property
    def raw_headers(self) -> bytes:
        """
        :return: The unparsed HTTP headers
        :rtype: bytes
        """
        _, headers = self.head.split(b"\r\n", 1)
        return bytes(headers)

    @property
    def request_line(self) -> bytes:
        """
        :return: The first line of a HTTP request
        :rtype: bytes
        """
        reqline, _ = self.head.split(b"\r\n", 1)
        return bytes(reqline)

    @property
    def id(self) -> Optional[Union[uuid.UUID, str, int]]:
        """
        A request ID passed from the client, or generated from the backend.

        By default, this will look in a request header defined at:
        ``self.app.config.REQUEST_ID_HEADER``. It defaults to
        ``X-Request-ID``. Sanic will try to cast the ID into a ``UUID`` or an
        ``int``. If there is not a UUID from the client, then Sanic will try
        to generate an ID by calling ``Request.generate_id()``. The default
        behavior is to generate a ``UUID``. You can customize this behavior
        by subclassing ``Request``.

        .. code-block:: python

            from sanic import Request, Sanic
            from itertools import count

            class IntRequest(Request):
                counter = count()

                def generate_id(self):
                    return next(self.counter)

            app = Sanic("MyApp", request_class=IntRequest)
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
        """
        :return: The request body parsed as JSON
        :rtype: Any
        """
        if self.parsed_json is None:
            self.load_json()

        return self.parsed_json

    def load_json(self, loads=None):
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
    def accept(self) -> AcceptContainer:
        """
        :return: The ``Accept`` header parsed
        :rtype: AcceptContainer
        """
        if self.parsed_accept is None:
            accept_header = self.headers.getone("accept", "")
            self.parsed_accept = parse_accept(accept_header)
        return self.parsed_accept

    @property
    def token(self) -> Optional[str]:
        """Attempt to return the auth header token.

        :return: token related to request
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

        :return: A Credentials object with token, or username and password
                 related to the request
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
        """
        Method to extract and parse the form data from a request.

        :param keep_blank_values:
            Whether to discard blank values from the form data
        :type keep_blank_values: bool
        :return: the parsed form data
        :rtype: Optional[RequestParameters]
        """
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
    def form(self):
        """
        :return: The request body parsed as form data
        """
        if self.parsed_form is None:
            self.get_form()

        return self.parsed_form

    @property
    def files(self):
        """
        :return: The request body parsed as uploaded files
        """
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
        """
        Method to parse ``query_string`` using ``urllib.parse.parse_qs``.
        This methods is used by ``args`` property.
        Can be used directly if you need to change default parameters.

        :param keep_blank_values:
            flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as blank
            strings.  The default false value indicates that blank values
            are to be ignored and treated as if they were  not included.
        :type keep_blank_values: bool
        :param strict_parsing:
            flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored. If true,
            errors raise a ValueError exception.
        :type strict_parsing: bool
        :param encoding:
            specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.
        :type encoding: str
        :param errors:
            specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.
        :type errors: str
        :return: RequestParameters
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
    """
    Convenience property to access :meth:`Request.get_args` with
    default values.
    """

    def get_query_args(
        self,
        keep_blank_values: bool = False,
        strict_parsing: bool = False,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> list:
        """
        Method to parse `query_string` using `urllib.parse.parse_qsl`.
        This methods is used by `query_args` property.
        Can be used directly if you need to change default parameters.

        :param keep_blank_values:
            flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as blank
            strings.  The default false value indicates that blank values
            are to be ignored and treated as if they were  not included.
        :type keep_blank_values: bool
        :param strict_parsing:
            flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored. If true,
            errors raise a ValueError exception.
        :type strict_parsing: bool
        :param encoding:
            specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.
        :type encoding: str
        :param errors:
            specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.
        :type errors: str
        :return: list
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
    """
    Convenience property to access :meth:`Request.get_query_args` with
    default values.
    """

    @property
    def cookies(self) -> Dict[str, str]:
        """
        :return: Incoming cookies on the request
        :rtype: Dict[str, str]
        """

        if self._cookies is None:
            cookie = self.headers.getone("cookie", None)
            if cookie is not None:
                cookies: SimpleCookie = SimpleCookie()
                cookies.load(cookie)
                self._cookies = {
                    name: cookie.value for name, cookie in cookies.items()
                }
            else:
                self._cookies = {}
        return self._cookies

    @property
    def content_type(self) -> str:
        """
        :return: Content-Type header form the request
        :rtype: str
        """
        return self.headers.getone("content-type", DEFAULT_HTTP_CONTENT_TYPE)

    @property
    def match_info(self):
        """
        :return: matched info after resolving route
        """
        return self._match_info

    @match_info.setter
    def match_info(self, value):
        self._match_info = value

    # Transport properties (obtained from local interface only)

    @property
    def ip(self) -> str:
        """
        :return: peer ip of the socket
        :rtype: str
        """
        return self.conn_info.client_ip if self.conn_info else ""

    @property
    def port(self) -> int:
        """
        :return: peer port of the socket
        :rtype: int
        """
        return self.conn_info.client_port if self.conn_info else 0

    @property
    def socket(self):
        """
        :return: Information about the connected socket if available
        """
        return self.conn_info.peername if self.conn_info else (None, None)

    @property
    def path(self) -> str:
        """
        :return: path of the local HTTP request
        :rtype: str
        """
        return self._parsed_url.path.decode("utf-8")

    @property
    def network_paths(self):
        """
        Access the network paths if available
        """
        return self.conn_info.network_paths

    # Proxy properties (using SERVER_NAME/forwarded/request/transport info)

    @property
    def forwarded(self) -> Options:
        """
        Active proxy information obtained from request headers, as specified in
        Sanic configuration.

        Field names by, for, proto, host, port and path are normalized.
        - for and by IPv6 addresses are bracketed
        - port (int) is only set by port headers, not from host.
        - path is url-unencoded

        Additional values may be available from new style Forwarded headers.

        :return: forwarded address info
        :rtype: Dict[str, str]
        """
        if self.parsed_forwarded is None:
            self.parsed_forwarded = (
                parse_forwarded(self.headers, self.app.config)
                or parse_xforwarded(self.headers, self.app.config)
                or {}
            )
        return self.parsed_forwarded

    @property
    def remote_addr(self) -> str:
        """
        Client IP address, if available.
        1. proxied remote address `self.forwarded['for']`
        2. local remote address `self.ip`

        :return: IPv4, bracketed IPv6, UNIX socket name or arbitrary string
        :rtype: str
        """
        if not hasattr(self, "_remote_addr"):
            self._remote_addr = str(
                self.forwarded.get("for", "")
            )  # or self.ip
        return self._remote_addr

    @property
    def scheme(self) -> str:
        """
        Determine request scheme.
        1. `config.SERVER_NAME` if in full URL format
        2. proxied proto/scheme
        3. local connection protocol

        :return: http|https|ws|wss or arbitrary value given by the headers.
        :rtype: str
        """
        if not hasattr(self, "_scheme"):
            if "//" in self.app.config.get("SERVER_NAME", ""):
                return self.app.config.SERVER_NAME.split("//")[0]
            if "proto" in self.forwarded:
                return str(self.forwarded["proto"])

            if (
                self.app.websocket_enabled
                and self.headers.getone("upgrade", "").lower() == "websocket"
            ):
                scheme = "ws"
            else:
                scheme = "http"

            if self.transport.get_extra_info("sslcontext"):
                scheme += "s"
            self._scheme = scheme

        return self._scheme

    @property
    def host(self) -> str:
        """
        The currently effective server 'host' (hostname or hostname:port).
        1. `config.SERVER_NAME` overrides any client headers
        2. proxied host of original request
        3. request host header
        hostname and port may be separated by
        `sanic.headers.parse_host(request.host)`.

        :return: the first matching host found, or empty string
        :rtype: str
        """
        server_name = self.app.config.get("SERVER_NAME")
        if server_name:
            return server_name.split("//", 1)[-1].split("/", 1)[0]
        return str(
            self.forwarded.get("host") or self.headers.getone("host", "")
        )

    @property
    def server_name(self) -> str:
        """
        :return: hostname the client connected to, by ``request.host``
        :rtype: str
        """
        return parse_host(self.host)[0] or ""

    @property
    def server_port(self) -> int:
        """
        The port the client connected to, by forwarded ``port`` or
        ``request.host``.

        Default port is returned as 80 and 443 based on ``request.scheme``.

        :return: port number
        :rtype: int
        """
        port = self.forwarded.get("port") or parse_host(self.host)[1]
        return int(port or (80 if self.scheme in ("http", "ws") else 443))

    @property
    def server_path(self) -> str:
        """
        :return: full path of current URL; uses proxied or local path
        :rtype: str
        """
        return str(self.forwarded.get("path") or self.path)

    @property
    def query_string(self) -> str:
        """
        :return: representation of the requested query
        :rtype: str
        """
        if self._parsed_url.query:
            return self._parsed_url.query.decode("utf-8")
        else:
            return ""

    @property
    def url(self) -> str:
        """
        :return: the URL
        :rtype: str
        """
        return urlunparse(
            (self.scheme, self.host, self.path, None, self.query_string, None)
        )

    def url_for(self, view_name: str, **kwargs) -> str:
        """
        Same as :func:`sanic.Sanic.url_for`, but automatically determine
        `scheme` and `netloc` base on the request. Since this method is aiming
        to generate correct schema & netloc, `_external` is implied.

        :param kwargs: takes same parameters as in :func:`sanic.Sanic.url_for`
        :return: an absolute url to the given view
        :rtype: str
        """
        # Full URL SERVER_NAME can only be handled in app.url_for
        try:
            if "//" in self.app.config.SERVER_NAME:
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
        """
        :return: The ASGI scope of the request.
                 If the app isn't an ASGI app, then raises an exception.
        :rtype: Optional[ASGIScope]
        """
        if not self.app.asgi:
            raise NotImplementedError(
                "App isn't running in ASGI mode. "
                "Scope is only available for ASGI apps."
            )

        return self.transport.scope

    @property
    def is_safe(self) -> bool:
        """
        :return: Whether the HTTP method is safe.
            See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.1
        :rtype: bool
        """
        return self.method in SAFE_HTTP_METHODS

    @property
    def is_idempotent(self) -> bool:
        """
        :return: Whether the HTTP method is iempotent.
            See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2
        :rtype: bool
        """
        return self.method in IDEMPOTENT_HTTP_METHODS

    @property
    def is_cacheable(self) -> bool:
        """
        :return: Whether the HTTP method is cacheable.
            See https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.3
        :rtype: bool
        """
        return self.method in CACHEABLE_HTTP_METHODS


class File(NamedTuple):
    """
    Model for defining a file. It is a ``namedtuple``, therefore you can
    iterate over the object, or access the parameters by name.

    :param type: The mimetype, defaults to text/plain
    :param body: Bytes of the file
    :param name: The filename
    """

    type: str
    body: bytes
    name: str


def parse_multipart_form(body, boundary):
    """
    Parse a request body and returns fields and files

    :param body: bytes request body
    :param boundary: bytes multipart boundary
    :return: fields (RequestParameters), files (RequestParameters)
    """
    files = RequestParameters()
    fields = RequestParameters()

    form_parts = body.split(boundary)
    for form_part in form_parts[1:-1]:
        file_name = None
        content_type = "text/plain"
        content_charset = "utf-8"
        field_name = None
        line_index = 2
        line_end_index = 0
        while not line_end_index == -1:
            line_end_index = form_part.find(b"\r\n", line_index)
            form_line = form_part[line_index:line_end_index].decode("utf-8")
            line_index = line_end_index + 2

            if not form_line:
                break

            colon_index = form_line.index(":")
            idx = colon_index + 2
            form_header_field = form_line[0:colon_index].lower()
            form_header_value, form_parameters = parse_content_header(
                form_line[idx:]
            )

            if form_header_field == "content-disposition":
                field_name = form_parameters.get("name")
                file_name = form_parameters.get("filename")

                # non-ASCII filenames in RFC2231, "filename*" format
                if file_name is None and form_parameters.get("filename*"):
                    encoding, _, value = email.utils.decode_rfc2231(
                        form_parameters["filename*"]
                    )
                    file_name = unquote(value, encoding=encoding)

                # Normalize to NFC (Apple MacOS/iOS send NFD)
                # Notes:
                # - No effect for Windows, Linux or Android clients which
                #   already send NFC
                # - Python open() is tricky (creates files in NFC no matter
                #   which form you use)
                if file_name is not None:
                    file_name = unicodedata.normalize("NFC", file_name)

            elif form_header_field == "content-type":
                content_type = form_header_value
                content_charset = form_parameters.get("charset", "utf-8")

        if field_name:
            post_data = form_part[line_index:-4]
            if file_name is None:
                value = post_data.decode(content_charset)
                if field_name in fields:
                    fields[field_name].append(value)
                else:
                    fields[field_name] = [value]
            else:
                form_file = File(
                    type=content_type, name=file_name, body=post_data
                )
                if field_name in files:
                    files[field_name].append(form_file)
                else:
                    files[field_name] = [form_file]
        else:
            logger.debug(
                "Form-data field does not have a 'name' parameter "
                "in the Content-Disposition header"
            )

    return fields, files
