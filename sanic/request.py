import asyncio
import email.utils

from collections import defaultdict, namedtuple
from http.cookies import SimpleCookie
from types import SimpleNamespace
from urllib.parse import parse_qs, parse_qsl, unquote, urlunparse

from httptools import parse_url  # type: ignore

from sanic.exceptions import InvalidUsage
from sanic.headers import (
    parse_content_header,
    parse_forwarded,
    parse_host,
    parse_xforwarded,
)
from sanic.log import error_logger, logger


try:
    from ujson import loads as json_loads  # type: ignore
except ImportError:
    from json import loads as json_loads  # type: ignore

DEFAULT_HTTP_CONTENT_TYPE = "application/octet-stream"
EXPECT_HEADER = "EXPECT"

# HTTP/1.1: https://www.w3.org/Protocols/rfc2616/rfc2616-sec7.html#sec7.2.1
# > If the media type remains unknown, the recipient SHOULD treat it
# > as type "application/octet-stream"


class RequestParameters(dict):
    """Hosts a dict with lists as values where get returns the first
    value of the list and getlist returns the whole shebang
    """

    def get(self, name, default=None):
        """Return the first value, either the default or actual"""
        return super().get(name, [default])[0]

    def getlist(self, name, default=None):
        """Return the entire list"""
        return super().get(name, default)


class StreamBuffer:
    def __init__(self, buffer_size=100):
        self._queue = asyncio.Queue(buffer_size)

    async def read(self):
        """Stop reading when gets None"""
        payload = await self._queue.get()
        self._queue.task_done()
        return payload

    async def __aiter__(self):
        """Support `async for data in request.stream`"""
        while True:
            data = await self.read()
            if not data:
                break
            yield data

    async def put(self, payload):
        await self._queue.put(payload)

    def is_full(self):
        return self._queue.full()

    @property
    def buffer_size(self):
        return self._queue.maxsize


class Request:
    """Properties of an HTTP request such as URL, headers, etc."""

    __slots__ = (
        "__weakref__",
        "_cookies",
        "_ip",
        "_parsed_url",
        "_port",
        "_remote_addr",
        "_socket",
        "app",
        "body",
        "conn_info",
        "ctx",
        "endpoint",
        "headers",
        "method",
        "parsed_args",
        "parsed_not_grouped_args",
        "parsed_files",
        "parsed_form",
        "parsed_json",
        "parsed_forwarded",
        "raw_url",
        "stream",
        "transport",
        "uri_template",
        "version",
    )

    def __init__(self, url_bytes, headers, version, method, transport, app):
        self.raw_url = url_bytes
        # TODO: Content-Encoding detection
        self._parsed_url = parse_url(url_bytes)
        self.app = app

        self.headers = headers
        self.version = version
        self.method = method
        self.transport = transport

        # Init but do not inhale
        self.body_init()
        self.conn_info = None
        self.ctx = SimpleNamespace()
        self.parsed_forwarded = None
        self.parsed_json = None
        self.parsed_form = None
        self.parsed_files = None
        self.parsed_args = defaultdict(RequestParameters)
        self.parsed_not_grouped_args = defaultdict(list)
        self.uri_template = None
        self._cookies = None
        self.stream = None
        self.endpoint = None

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"<{class_name}: {self.method} {self.path}>"

    def body_init(self):
        """.. deprecated:: 20.3
        To be removed in 21.3"""
        self.body = []

    def body_push(self, data):
        """.. deprecated:: 20.3
        To be removed in 21.3"""
        self.body.append(data)

    def body_finish(self):
        """.. deprecated:: 20.3
        To be removed in 21.3"""
        self.body = b"".join(self.body)

    async def receive_body(self):
        """Receive request.body, if not already received.

        Streaming handlers may call this to receive the full body.

        This is added as a compatibility shim in Sanic 20.3 because future
        versions of Sanic will make all requests streaming and will use this
        function instead of the non-async body_init/push/finish functions.

        Please make an issue if your code depends on the old functionality and
        cannot be upgraded to the new API.
        """
        if not self.stream:
            return
        self.body = b"".join([data async for data in self.stream])

    @property
    def json(self):
        if self.parsed_json is None:
            self.load_json()

        return self.parsed_json

    def load_json(self, loads=json_loads):
        try:
            self.parsed_json = loads(self.body)
        except Exception:
            if not self.body:
                return None
            raise InvalidUsage("Failed when parsing body as json")

        return self.parsed_json

    @property
    def token(self):
        """Attempt to return the auth header token.

        :return: token related to request
        """
        prefixes = ("Bearer", "Token")
        auth_header = self.headers.get("Authorization")

        if auth_header is not None:
            for prefix in prefixes:
                if prefix in auth_header:
                    return auth_header.partition(prefix)[-1].strip()

        return auth_header

    @property
    def form(self):
        if self.parsed_form is None:
            self.parsed_form = RequestParameters()
            self.parsed_files = RequestParameters()
            content_type = self.headers.get(
                "Content-Type", DEFAULT_HTTP_CONTENT_TYPE
            )
            content_type, parameters = parse_content_header(content_type)
            try:
                if content_type == "application/x-www-form-urlencoded":
                    self.parsed_form = RequestParameters(
                        parse_qs(self.body.decode("utf-8"))
                    )
                elif content_type == "multipart/form-data":
                    # TODO: Stream this instead of reading to/from memory
                    boundary = parameters["boundary"].encode("utf-8")
                    self.parsed_form, self.parsed_files = parse_multipart_form(
                        self.body, boundary
                    )
            except Exception:
                error_logger.exception("Failed when parsing form")

        return self.parsed_form

    @property
    def files(self):
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
        Method to parse `query_string` using `urllib.parse.parse_qs`.
        This methods is used by `args` property.
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

    @property
    def cookies(self):
        if self._cookies is None:
            cookie = self.headers.get("Cookie")
            if cookie is not None:
                cookies = SimpleCookie()
                cookies.load(cookie)
                self._cookies = {
                    name: cookie.value for name, cookie in cookies.items()
                }
            else:
                self._cookies = {}
        return self._cookies

    @property
    def content_type(self):
        return self.headers.get("Content-Type", DEFAULT_HTTP_CONTENT_TYPE)

    @property
    def match_info(self):
        """return matched info after resolving route"""
        return self.app.router.get(self)[2]

    # Transport properties (obtained from local interface only)

    @property
    def ip(self):
        """
        :return: peer ip of the socket
        """
        return self.conn_info.client if self.conn_info else ""

    @property
    def port(self):
        """
        :return: peer port of the socket
        """
        return self.conn_info.client_port if self.conn_info else 0

    @property
    def socket(self):
        return self.conn_info.peername if self.conn_info else (None, None)

    @property
    def path(self) -> str:
        """Path of the local HTTP request."""
        return self._parsed_url.path.decode("utf-8")

    # Proxy properties (using SERVER_NAME/forwarded/request/transport info)

    @property
    def forwarded(self):
        """
        Active proxy information obtained from request headers, as specified in
        Sanic configuration.

        Field names by, for, proto, host, port and path are normalized.
        - for and by IPv6 addresses are bracketed
        - port (int) is only set by port headers, not from host.
        - path is url-unencoded

        Additional values may be available from new style Forwarded headers.
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
        """
        if not hasattr(self, "_remote_addr"):
            self._remote_addr = self.forwarded.get("for", "")  # or self.ip
        return self._remote_addr

    @property
    def scheme(self) -> str:
        """
        Determine request scheme.
        1. `config.SERVER_NAME` if in full URL format
        2. proxied proto/scheme
        3. local connection protocol
        :return: http|https|ws|wss or arbitrary value given by the headers.
        """
        if "//" in self.app.config.get("SERVER_NAME", ""):
            return self.app.config.SERVER_NAME.split("//")[0]
        if "proto" in self.forwarded:
            return self.forwarded["proto"]

        if (
            self.app.websocket_enabled
            and self.headers.get("upgrade") == "websocket"
        ):
            scheme = "ws"
        else:
            scheme = "http"

        if self.transport.get_extra_info("sslcontext"):
            scheme += "s"

        return scheme

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
        """
        server_name = self.app.config.get("SERVER_NAME")
        if server_name:
            return server_name.split("//", 1)[-1].split("/", 1)[0]
        return self.forwarded.get("host") or self.headers.get("host", "")

    @property
    def server_name(self) -> str:
        """The hostname the client connected to, by `request.host`."""
        return parse_host(self.host)[0] or ""

    @property
    def server_port(self) -> int:
        """
        The port the client connected to, by forwarded `port` or
        `request.host`.

        Default port is returned as 80 and 443 based on `request.scheme`.
        """
        port = self.forwarded.get("port") or parse_host(self.host)[1]
        return port or (80 if self.scheme in ("http", "ws") else 443)

    @property
    def server_path(self) -> str:
        """Full path of current URL. Uses proxied or local path."""
        return self.forwarded.get("path") or self.path

    @property
    def query_string(self):
        if self._parsed_url.query:
            return self._parsed_url.query.decode("utf-8")
        else:
            return ""

    @property
    def url(self):
        return urlunparse(
            (self.scheme, self.host, self.path, None, self.query_string, None)
        )

    def url_for(self, view_name, **kwargs):
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


File = namedtuple("File", ["type", "body", "name"])


def parse_multipart_form(body, boundary):
    """Parse a request body and returns fields and files

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
            form_header_field = form_line[0:colon_index].lower()
            form_header_value, form_parameters = parse_content_header(
                form_line[colon_index + 2 :]
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
