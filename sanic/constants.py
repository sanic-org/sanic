from enum import Enum, auto


class HTTPMethod(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    def __eq__(self, value: object) -> bool:
        value = str(value).upper()
        return super().__eq__(value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value

    GET = auto()
    POST = auto()
    PUT = auto()
    HEAD = auto()
    OPTIONS = auto()
    PATCH = auto()
    DELETE = auto()


class LocalCertCreator(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    AUTO = auto()
    TRUSTME = auto()
    MKCERT = auto()


HTTP_METHODS = tuple(HTTPMethod.__members__.values())
SAFE_HTTP_METHODS = (HTTPMethod.GET, HTTPMethod.HEAD, HTTPMethod.OPTIONS)
IDEMPOTENT_HTTP_METHODS = (
    HTTPMethod.GET,
    HTTPMethod.HEAD,
    HTTPMethod.PUT,
    HTTPMethod.DELETE,
    HTTPMethod.OPTIONS,
)
CACHEABLE_HTTP_METHODS = (HTTPMethod.GET, HTTPMethod.HEAD)
DEFAULT_HTTP_CONTENT_TYPE = "application/octet-stream"
DEFAULT_LOCAL_TLS_KEY = "key.pem"
DEFAULT_LOCAL_TLS_CERT = "cert.pem"
