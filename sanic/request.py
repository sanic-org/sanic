from cgi import parse_header
from collections import namedtuple
from httptools import parse_url
from urllib.parse import parse_qs
from ujson import loads as json_loads

from .log import log


class RequestParameters(dict):
    """
    Hosts a dict with lists as values where get returns the first
    value of the list and getlist returns the whole shebang
    """

    def __init__(self, *args, **kwargs):
        self.super = super()
        self.super.__init__(*args, **kwargs)

    def get(self, name, default=None):
        values = self.super.get(name)
        return values[0] if values else default

    def getlist(self, name, default=None):
        return self.super.get(name, default)


class Request:
    __slots__ = (
        'url', 'headers', 'version', 'method',
        'query_string', 'body',
        'parsed_json', 'parsed_args', 'parsed_form', 'parsed_files',
    )

    def __init__(self, url_bytes, headers, version, method):
        # TODO: Content-Encoding detection
        url_parsed = parse_url(url_bytes)
        self.url = url_parsed.path.decode('utf-8')
        self.headers = headers
        self.version = version
        self.method = method
        self.query_string = url_parsed.query.decode('utf-8') if url_parsed.query else None

        # Init but do not inhale
        self.body = None
        self.parsed_json = None
        self.parsed_form = None
        self.parsed_files = None
        self.parsed_args = None

    @property
    def json(self):
        if not self.parsed_json:
            try:
                self.parsed_json = json_loads(self.body)
            except:
                pass

        return self.parsed_json

    @property
    def form(self):
        if self.parsed_form is None:
            self.parsed_form = {}
            self.parsed_files = {}
            content_type, parameters = parse_header(self.headers.get('Content-Type'))
            try:
                if content_type is None or content_type == 'application/x-www-form-urlencoded':
                    self.parsed_form = RequestParameters(parse_qs(self.body.decode('utf-8')))
                elif content_type == 'multipart/form-data':
                    # TODO: Stream this instead of reading to/from memory
                    boundary = parameters['boundary'].encode('utf-8')
                    self.parsed_form, self.parsed_files = parse_multipart_form(self.body, boundary)
            except Exception as e:
                log.exception(e)
                pass

        return self.parsed_form

    @property
    def files(self):
        if self.parsed_files is None:
            _ = self.form  # compute form to get files

        return self.parsed_files

    @property
    def args(self):
        if self.parsed_args is None:
            if self.query_string:
                self.parsed_args = RequestParameters(parse_qs(self.query_string))
            else:
                self.parsed_args = {}

        return self.parsed_args


File = namedtuple('File', ['type', 'body', 'name'])


def parse_multipart_form(body, boundary):
    """
    Parses a request body and returns fields and files
    :param body: Bytes request body
    :param boundary: Bytes multipart boundary
    :return: fields (dict), files (dict)
    """
    files = {}
    fields = {}

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
            form_header_value, form_parameters = parse_header(form_line[colon_index + 2:])

            if form_header_field == 'Content-Disposition':
                if 'filename' in form_parameters:
                    file_name = form_parameters['filename']
                field_name = form_parameters.get('name')
            elif form_header_field == 'Content-Type':
                file_type = form_header_value

        post_data = form_part[line_index:-4]
        if file_name or file_type:
            files[field_name] = File(type=file_type, name=file_name, body=post_data)
        else:
            fields[field_name] = post_data.decode('utf-8')

    return fields, files
