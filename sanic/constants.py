from enum import auto

from sanic.compat import UpperStrEnum


class HTTPMethod(UpperStrEnum):

    GET = auto()
    POST = auto()
    PUT = auto()
    HEAD = auto()
    OPTIONS = auto()
    PATCH = auto()
    DELETE = auto()


class LocalCertCreator(UpperStrEnum):

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
