import asyncio
import email.utils
import json
import sys
import warnings

from cgi import parse_header
from collections import defaultdict, namedtuple
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, parse_qsl, unquote, urlunparse

from httptools import parse_url

from sanic.exceptions import InvalidUsage
from sanic.log import error_logger, logger


try:
    from ujson import loads as json_loads
except ImportError:
    if sys.version_info[:2] == (3, 5):

        def json_loads(data):
            # on Python 3.5 json.loads only supports str not bytes
            return json.loads(data.decode())

    else:
        json_loads = json.loads

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
        """ Stop reading when gets None """
        payload = await self._queue.get()
        self._queue.task_done()
        return payload

    async def put(self, payload):
        await self._queue.put(payload)

    def is_full(self):
        return self._queue.full()


class Request(dict):
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
        "endpoint",
        "headers",
        "method",
        "parsed_args",
        "parsed_not_grouped_args",
        "parsed_files",
        "parsed_form",
        "parsed_json",
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
        return "<{0}: {1} {2}>".format(
            self.__class__.__name__, self.method, self.path
        )

    def __bool__(self):
        if self.transport:
            return True
        return False

    def body_init(self):
        self.body = []

    def body_push(self, data):
        self.body.append(data)

    def body_finish(self):
        self.body = b"".join(self.body)

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
            content_type, parameters = parse_header(content_type)
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
        if not self.parsed_args[
            (keep_blank_values, strict_parsing, encoding, errors)
        ]:
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

    @property
    def raw_args(self) -> dict:
        if self.app.debug:  # pragma: no cover
            warnings.simplefilter("default")
        warnings.warn(
            "Use of raw_args will be deprecated in "
            "the future versions. Please use args or query_args "
            "properties instead",
            DeprecationWarning,
        )
        return {k: v[0] for k, v in self.args.items()}

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
        if not self.parsed_not_grouped_args[
            (keep_blank_values, strict_parsing, encoding, errors)
        ]:
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
    def ip(self):
        """
        :return: peer ip of the socket
        """
        if not hasattr(self, "_socket"):
            self._get_address()
        return self._ip

    @property
    def port(self):
        """
        :return: peer port of the socket
        """
        if not hasattr(self, "_socket"):
            self._get_address()
        return self._port

    @property
    def socket(self):
        if not hasattr(self, "_socket"):
            self._get_address()
        return self._socket

    def _get_address(self):
        self._socket = self.transport.get_extra_info("peername") or (
            None,
            None,
        )
        self._ip = self._socket[0]
        self._port = self._socket[1]

    @property
    def server_name(self):
        """
        Attempt to get the server's hostname in this order:
        `config.SERVER_NAME`, `x-forwarded-host` header, :func:`Request.host`

        :return: the server name without port number
        :rtype: str
        """
        return (
            self.app.config.get("SERVER_NAME")
            or self.headers.get("x-forwarded-host")
            or self.host.split(":")[0]
        )

    @property
    def server_port(self):
        """
        Attempt to get the server's port in this order:
        `x-forwarded-port` header, :func:`Request.host`, actual port used by
        the transport layer socket.
        :return: server port
        :rtype: int
        """
        forwarded_port = self.headers.get("x-forwarded-port") or (
            self.host.split(":")[1] if ":" in self.host else None
        )
        if forwarded_port:
            return int(forwarded_port)
        else:
            port = self.transport.get_extra_info("sockname")[1]
            return port

    @property
    def remote_addr(self):
        """Attempt to return the original client ip based on X-Forwarded-For
        or X-Real-IP. If HTTP headers are unavailable or untrusted, returns
        an empty string.

        :return: original client ip.
        """
        if not hasattr(self, "_remote_addr"):
            if self.app.config.PROXIES_COUNT == 0:
                self._remote_addr = ""
            elif self.app.config.REAL_IP_HEADER and self.headers.get(
                self.app.config.REAL_IP_HEADER
            ):
                self._remote_addr = self.headers[
                    self.app.config.REAL_IP_HEADER
                ]
            elif self.app.config.FORWARDED_FOR_HEADER:
                forwarded_for = self.headers.get(
                    self.app.config.FORWARDED_FOR_HEADER, ""
                ).split(",")
                remote_addrs = [
                    addr
                    for addr in [addr.strip() for addr in forwarded_for]
                    if addr
                ]
                if self.app.config.PROXIES_COUNT == -1:
                    self._remote_addr = remote_addrs[0]
                elif len(remote_addrs) >= self.app.config.PROXIES_COUNT:
                    self._remote_addr = remote_addrs[
                        -self.app.config.PROXIES_COUNT
                    ]
                else:
                    self._remote_addr = ""
            else:
                self._remote_addr = ""
        return self._remote_addr

    @property
    def scheme(self):
        """
        Attempt to get the request scheme.
        Seeking the value in this order:
        `x-forwarded-proto` header, `x-scheme` header, the sanic app itself.

        :return: http|https|ws|wss or arbitrary value given by the headers.
        :rtype: str
        """
        forwarded_proto = self.headers.get(
            "x-forwarded-proto"
        ) or self.headers.get("x-scheme")
        if forwarded_proto:
            return forwarded_proto

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
    def host(self):
        """
        :return: the Host specified in the header, may contains port number.
        """
        # it appears that httptools doesn't return the host
        # so pull it from the headers

        return self.headers.get("Host", "")

    @property
    def content_type(self):
        return self.headers.get("Content-Type", DEFAULT_HTTP_CONTENT_TYPE)

    @property
    def match_info(self):
        """return matched info after resolving route"""
        return self.app.router.get(self)[2]

    @property
    def path(self):
        return self._parsed_url.path.decode("utf-8")

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
        scheme = self.scheme
        host = self.server_name
        port = self.server_port

        if (scheme.lower() in ("http", "ws") and port == 80) or (
            scheme.lower() in ("https", "wss") and port == 443
        ):
            netloc = host
        else:
            netloc = "{}:{}".format(host, port)

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
            form_header_value, form_parameters = parse_header(
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
