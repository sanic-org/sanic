from httptools import parse_url
from urllib.parse import parse_qs
from ujson import loads as json_loads

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
        'parsed_json', 'parsed_args', 'parsed_form',
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
        if not self.parsed_form:
            content_type = self.headers.get('Content-Type')
            try:
                # TODO: form-data
                if content_type is None or content_type == 'application/x-www-form-urlencoded':
                    self.parsed_form = RequestParameters(parse_qs(self.body.decode('utf-8')))
            except:
                pass

        return self.parsed_form

    @property
    def args(self):
        if self.parsed_args is None:
            if self.query_string:
                self.parsed_args = RequestParameters(parse_qs(self.query_string))
            else:
                self.parsed_args = {}

        return self.parsed_args
