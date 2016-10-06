from urllib.parse import parse_qs
from ujson import loads as json_loads

class Request:
    __slots__ = ('protocol', 'url', 'headers', 'version', 'method', 'query_string', 'body', 'parsed_json', 'parsed_args')

    def __init__(self, protocol, url, headers, version, method):
        self.protocol = protocol
        self.url = url
        self.headers = headers
        self.version = version
        self.method = method

        # Capture query string
        query_string_position = self.url.find("?")
        if query_string_position != -1:
            self.query_string = self.url[query_string_position+1:]
            self.url = self.url[:query_string_position]
        else:
            self.query_string = None

        # Init but do not inhale
        self.body = None
        self.parsed_json = None
        self.parsed_args = None

    @property
    def json(self):
        if not self.parsed_json:
            if not self.body:
                raise ValueError("No body to parse")
            self.parsed_json = json_loads(self.body)

        return self.parsed_json 

    @property
    def args(self):
        if self.parsed_args is None:
            if self.query_string:
                parsed_query_string = parse_qs(self.query_string).items()
                self.parsed_args = {k:[_v for _v in v] if len(v)>1 else v[0] for k,v in parsed_query_string}
                print(self.parsed_args)
            else:
                self.parsed_args = {}

        return self.parsed_args 