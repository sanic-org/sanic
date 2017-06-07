import sys
import json
from cgi import parse_header
from collections import namedtuple
from http.cookies import SimpleCookie
from httptools import parse_url
from urllib.parse import parse_qs, urlunparse

try:
    from ujson import loads as json_loads
except ImportError:
    if sys.version_info[:2] == (3, 5):
        def json_loads(data):
            # on Python 3.5 json.loads only supports str not bytes
            return json.loads(data.decode())
    else:
        json_loads = json.loads

from sanic.exceptions import InvalidUsage
from sanic.log import log


DEFAULT_HTTP_CONTENT_TYPE = "application/octet-stream"
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


class Request(dict):
    """Properties of an HTTP request such as URL, headers, etc."""
    __slots__ = (
        'app', 'headers', 'version', 'method', '_cookies', 'transport',
        'body', 'parsed_json', 'parsed_args', 'parsed_form', 'parsed_files',
        '_ip', '_parsed_url', 'uri_template', 'stream', 'streamable'
    )

    def __init__(self, url_bytes, headers, version, method, transport):
        # TODO: Content-Encoding detection
        self._parsed_url = parse_url(url_bytes)
        self.app = None

        self.headers = headers
        self.version = version
        self.method = method
        self.transport = transport

        # Init but do not inhale
        self.body = []
        self.parsed_json = None
        self.parsed_form = None
        self.parsed_files = None
        self.parsed_args = None
        self.uri_template = None
        self._cookies = None
        self.stream = None
        self.streamable = True

    @property
    def json(self):
        if self.parsed_json is None:
            try:
                self.parsed_json = json_loads(self.body)
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
        auth_header = self.headers.get('Authorization')
        if auth_header is not None and 'Token ' in auth_header:
            return auth_header.partition('Token ')[-1]
        else:
            return auth_header

    @property
    def form(self):
        if self.parsed_form is None:
            self.parsed_form = RequestParameters()
            self.parsed_files = RequestParameters()
            content_type = self.headers.get(
                'Content-Type', DEFAULT_HTTP_CONTENT_TYPE)
            content_type, parameters = parse_header(content_type)
            try:
                if content_type == 'application/x-www-form-urlencoded':
                    self.parsed_form = RequestParameters(
                        parse_qs(self.body.decode('utf-8')))
                elif content_type == 'multipart/form-data':
                    # TODO: Stream this instead of reading to/from memory
                    boundary = parameters['boundary'].encode('utf-8')
                    self.parsed_form, self.parsed_files = (
                        parse_multipart_form(self.body, boundary))
            except Exception:
                log.exception("Failed when parsing form")

        return self.parsed_form

    @property
    def files(self):
        if self.parsed_files is None:
            self.form  # compute form to get files

        return self.parsed_files

    @property
    def args(self):
        if self.parsed_args is None:
            if self.query_string:
                self.parsed_args = RequestParameters(
                    parse_qs(self.query_string))
            else:
                self.parsed_args = RequestParameters()
        return self.parsed_args

    @property
    def raw_args(self):
        return {k: v[0] for k, v in self.args.items()}

    @property
    def cookies(self):
        if self._cookies is None:
            cookie = self.headers.get('Cookie') or self.headers.get('cookie')
            if cookie is not None:
                cookies = SimpleCookie()
                cookies.load(cookie)
                self._cookies = {name: cookie.value
                                 for name, cookie in cookies.items()}
            else:
                self._cookies = {}
        return self._cookies

    @property
    def ip(self):
        if not hasattr(self, '_ip'):
            self._ip = (self.transport.get_extra_info('peername') or
                        (None, None))
        return self._ip

    @property
    def scheme(self):
        if self.app.websocket_enabled \
                and self.headers.get('upgrade') == 'websocket':
            scheme = 'ws'
        else:
            scheme = 'http'

        if self.transport.get_extra_info('sslcontext'):
            scheme += 's'

        return scheme

    @property
    def host(self):
        # it appears that httptools doesn't return the host
        # so pull it from the headers
        return self.headers.get('Host', '')

    @property
    def path(self):
        return self._parsed_url.path.decode('utf-8')

    @property
    def query_string(self):
        if self._parsed_url.query:
            return self._parsed_url.query.decode('utf-8')
        else:
            return ''

    @property
    def url(self):
        return urlunparse((
            self.scheme,
            self.host,
            self.path,
            None,
            self.query_string,
            None))

    def cancel_stream(self):
        self.streamable = False


File = namedtuple('File', ['type', 'body', 'name'])


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
        file_type = None
        field_name = None
        line_index = 2
        line_end_index = 0
        while not line_end_index == -1:
            line_end_index = form_part.find(b'\r\n', line_index)
            form_line = form_part[line_index:line_end_index].decode('utf-8')
            line_index = line_end_index + 2

            if not form_line:
                break

            colon_index = form_line.index(':')
            form_header_field = form_line[0:colon_index]
            form_header_value, form_parameters = parse_header(
                form_line[colon_index + 2:])

            if form_header_field == 'Content-Disposition':
                if 'filename' in form_parameters:
                    file_name = form_parameters['filename']
                field_name = form_parameters.get('name')
            elif form_header_field == 'Content-Type':
                file_type = form_header_value

        post_data = form_part[line_index:-4]
        if file_name or file_type:
            file = File(type=file_type, name=file_name, body=post_data)
            if field_name in files:
                files[field_name].append(file)
            else:
                files[field_name] = [file]
        else:
            value = post_data.decode('utf-8')
            if field_name in fields:
                fields[field_name].append(value)
            else:
                fields[field_name] = [value]

    return fields, files
