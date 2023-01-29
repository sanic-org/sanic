from __future__ import annotations

import re

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union
from urllib.parse import unquote

from sanic.exceptions import InvalidHeader
from sanic.helpers import STATUS_CODES


# TODO:
# - the Options object should be a typed object to allow for less casting
#   across the application (in request.py for example)
HeaderIterable = Iterable[Tuple[str, Any]]  # Values convertible to str
HeaderBytesIterable = Iterable[Tuple[bytes, bytes]]
Options = Dict[str, Union[int, str]]  # key=value fields in various headers
OptionsIterable = Iterable[Tuple[str, str]]  # May contain duplicate keys

_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
_param = re.compile(rf";\s*{_token}=(?:{_token}|{_quoted})", re.ASCII)
_firefox_quote_escape = re.compile(r'\\"(?!; |\s*$)')
_ipv6 = "(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}"
_ipv6_re = re.compile(_ipv6)
_host_re = re.compile(
    r"((?:\[" + _ipv6 + r"\])|[a-zA-Z0-9.\-]{1,253})(?::(\d{1,5}))?"
)

# RFC's quoted-pair escapes are mostly ignored by browsers. Chrome, Firefox and
# curl all have different escaping, that we try to handle as well as possible,
# even though no client escapes in a way that would allow perfect handling.

# For more information, consult ../tests/test_requests.py


def parse_arg_as_accept(f):
    def func(self, other, *args, **kwargs):
        if not isinstance(other, MediaType) and other:
            other = MediaType._parse(other)
        return f(self, other, *args, **kwargs)

    return func


class MediaType:
    """A media type, as used in the Accept header."""
    def __init__(
        self,
        type_: str,
        subtype: str,
        **params: str,
    ):
        self.type_ = type_
        self.subtype = subtype
        self.q = float(params.get("q", "1.0"))
        self.params = params
        self.str = f"{type_}/{subtype}"

    def __repr__(self):
        return self.str + "".join(f";{k}={v}" for k, v in self.params.items())

    def __eq__(self, media_type: str):
        """Check if the type and subtype match exactly."""
        return self.str == media_type

    def match(
        self,
        media_type: str,
    ) -> Optional[MediaType]:
        """Check if this media type matches the given media type.

        Wildcards are supported both ways on both type and subtype.

        Note:  Use the `==` operator instead to check for literal matches
        without expanding wildcards.

        @param media_type: A type/subtype string to match.
        @return `self` if the media types are compatible, else `None`
        """
        mt = MediaType._parse(media_type)
        return self if (
            # Subtype match
            (self.subtype in (mt.subtype, "*") or mt.subtype == "*")
            # Type match
            and (self.type_ in (mt.type_, "*") or mt.type_ == "*")
        ) else None

    @property
    def has_wildcard(self) -> bool:
        """Return True if this media type has a wildcard in it."""
        return "*" in (self.subtype, self.type_)

    @property
    def is_wildcard(self) -> bool:
        """Return True if this is the wildcard `*/*`"""
        return self.type_ == "*" and self.subtype == "*"

    @classmethod
    def _parse(cls, raw: AcceptLike) -> MediaType:
        mtype = raw.strip()

        media, *raw_params = mtype.split(";")
        type_, subtype = media.split("/", 1)

        params = dict(
            [
                (key.strip(), value.strip())
                for key, value in (param.split("=", 1) for param in raw_params)
            ]
        )

        return cls(type_.lstrip(), subtype.rstrip(), **params)


class AcceptList(list):
    """A list of media types, as used in the Accept header.

    The Accept header entries are listed in order of preference, starting
    with the most preferred. This class is a list of `MediaType` objects,
    that encapsulate also the q value or any other parameters.

    Three separate methods are provided for searching the list, for
    different use cases. The first two match wildcards with anything,
    while `in` and other operators handle wildcards as literal values.

    -  `choose` for choosing one of its arguments to use in response.
    -  'match' for the best MediaType of the accept header, or None.
    -   operator 'in' for checking explicit matches (wildcards as is).
    """

    def match(self, *media_types: List[str]) -> Optional[MediaType]:
        """Find a media type accepted by the client.

        This method can be used to find which of the media types requested by
        the client is most preferred while matching any of the arguments.

        Wildcards are supported. Most clients include */* as the last item in
        their Accept header, so this method will always return a match unless
        a custom header is used, but it may return a more specific match if
        the client has requested any suitable types explicitly.

        @param media_types: Any type/subtype strings to find.
        @return A matching `MediaType` or `None` if nothing matches.
        """
        for accepted in self:
            if any(accepted.match(mt) for mt in media_types):
                return accepted


    def choose(self, *media_types: List[str], omit_wildcard=True) -> str:
        """Choose a most suitable media type based on the Accept header.

        This is the recommended way to choose a response format based on the
        Accept header. The q values and the order of the Accept header are
        respected, and if due to wildcards multiple arguments match the same
        accept header entry, the first one matching is returned.

        Should none of the arguments be acceptable, the first argument is
        returned with the q value of 0.0 (i.e. the lowest possible).

        @param media_types: Any type/subtype strings to find.
        @param omit_wildcard: Ignore full wildcard */* in the Accept header.
        @return A tuple of one of the arguments and the q value of the match.
        """
        # Find the preferred MediaType if any match
        for accepted in self:
            if omit_wildcard and accepted.is_wildcard:
                continue
            for mt in media_types:
                if accepted.match(mt):
                    return mt, accepted.q
        # Fall back to the first argument
        return media_types[0], 0.0


def parse_accept(accept: str) -> AcceptList:
    """Parse an Accept header and order the acceptable media types in
    accorsing to RFC 7231, s. 5.3.2
    https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.2
    """
    if not accept:
        return AcceptList()
    try:
        a = [MediaType._parse(mtype) for mtype in accept.split(",")]
        return AcceptList(sorted(a, key=lambda mtype: -mtype.q))
    except ValueError:
        raise InvalidHeader(f"Invalid header value in Accept: {accept}")



def parse_content_header(value: str) -> Tuple[str, Options]:
    """Parse content-type and content-disposition header values.

    E.g. 'form-data; name=upload; filename=\"file.txt\"' to
    ('form-data', {'name': 'upload', 'filename': 'file.txt'})

    Mostly identical to cgi.parse_header and werkzeug.parse_options_header
    but runs faster and handles special characters better. Unescapes quotes.
    """
    value = _firefox_quote_escape.sub("%22", value)
    pos = value.find(";")
    if pos == -1:
        options: Dict[str, Union[int, str]] = {}
    else:
        options = {
            m.group(1).lower(): m.group(2) or m.group(3).replace("%22", '"')
            for m in _param.finditer(value[pos:])
        }
        value = value[:pos]
    return value.strip().lower(), options


# https://tools.ietf.org/html/rfc7230#section-3.2.6 and
# https://tools.ietf.org/html/rfc7239#section-4
# This regex is for *reversed* strings because that works much faster for
# right-to-left matching than the other way around. Be wary that all things are
# a bit backwards! _rparam matches forwarded pairs alike ";key=value"
_rparam = re.compile(f"(?:{_token}|{_quoted})={_token}\\s*($|[;,])", re.ASCII)


def parse_forwarded(headers, config) -> Optional[Options]:
    """Parse RFC 7239 Forwarded headers.
    The value of `by` or `secret` must match `config.FORWARDED_SECRET`
    :return: dict with keys and values, or None if nothing matched
    """
    header = headers.getall("forwarded", None)
    secret = config.FORWARDED_SECRET
    if header is None or not secret:
        return None
    header = ",".join(header)  # Join multiple header lines
    if secret not in header:
        return None
    # Loop over <separator><key>=<value> elements from right to left
    sep = pos = None
    options: List[Tuple[str, str]] = []
    found = False
    for m in _rparam.finditer(header[::-1]):
        # Start of new element? (on parser skips and non-semicolon right sep)
        if m.start() != pos or sep != ";":
            # Was the previous element (from right) what we wanted?
            if found:
                break
            # Clear values and parse as new element
            del options[:]
        pos = m.end()
        val_token, val_quoted, key, sep = m.groups()
        key = key.lower()[::-1]
        val = (val_token or val_quoted.replace('"\\', '"'))[::-1]
        options.append((key, val))
        if key in ("secret", "by") and val == secret:
            found = True
        # Check if we would return on next round, to avoid useless parse
        if found and sep != ";":
            break
    # If secret was found, return the matching options in left-to-right order
    return fwd_normalize(reversed(options)) if found else None


def parse_xforwarded(headers, config) -> Optional[Options]:
    """Parse traditional proxy headers."""
    real_ip_header = config.REAL_IP_HEADER
    proxies_count = config.PROXIES_COUNT
    addr = real_ip_header and headers.getone(real_ip_header, None)
    if not addr and proxies_count:
        assert proxies_count > 0
        try:
            # Combine, split and filter multiple headers' entries
            forwarded_for = headers.getall(config.FORWARDED_FOR_HEADER)
            proxies = [
                p
                for p in (
                    p.strip() for h in forwarded_for for p in h.split(",")
                )
                if p
            ]
            addr = proxies[-proxies_count]
        except (KeyError, IndexError):
            pass
    # No processing of other headers if no address is found
    if not addr:
        return None

    def options():
        yield "for", addr
        for key, header in (
            ("proto", "x-scheme"),
            ("proto", "x-forwarded-proto"),  # Overrides X-Scheme if present
            ("host", "x-forwarded-host"),
            ("port", "x-forwarded-port"),
            ("path", "x-forwarded-path"),
        ):
            yield key, headers.getone(header, None)

    return fwd_normalize(options())


def fwd_normalize(fwd: OptionsIterable) -> Options:
    """Normalize and convert values extracted from forwarded headers."""
    ret: Dict[str, Union[int, str]] = {}
    for key, val in fwd:
        if val is not None:
            try:
                if key in ("by", "for"):
                    ret[key] = fwd_normalize_address(val)
                elif key in ("host", "proto"):
                    ret[key] = val.lower()
                elif key == "port":
                    ret[key] = int(val)
                elif key == "path":
                    ret[key] = unquote(val)
                else:
                    ret[key] = val
            except ValueError:
                pass
    return ret


def fwd_normalize_address(addr: str) -> str:
    """Normalize address fields of proxy headers."""
    if addr == "unknown":
        raise ValueError()  # omit unknown value identifiers
    if addr.startswith("_"):
        return addr  # do not lower-case obfuscated strings
    if _ipv6_re.fullmatch(addr):
        addr = f"[{addr}]"  # bracket IPv6
    return addr.lower()


def parse_host(host: str) -> Tuple[Optional[str], Optional[int]]:
    """Split host:port into hostname and port.
    :return: None in place of missing elements
    """
    m = _host_re.fullmatch(host)
    if not m:
        return None, None
    host, port = m.groups()
    return host.lower(), int(port) if port is not None else None


_HTTP1_STATUSLINES = [
    b"HTTP/1.1 %d %b\r\n" % (status, STATUS_CODES.get(status, b"UNKNOWN"))
    for status in range(1000)
]


def format_http1_response(status: int, headers: HeaderBytesIterable) -> bytes:
    """Format a HTTP/1.1 response header."""
    # Note: benchmarks show that here bytes concat is faster than bytearray,
    # b"".join() or %-formatting. %timeit any changes you make.
    ret = _HTTP1_STATUSLINES[status]
    for h in headers:
        ret += b"%b: %b\r\n" % h
    ret += b"\r\n"
    return ret


def parse_credentials(
    header: Optional[str],
    prefixes: Union[List, Tuple, Set] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Parses any header with the aim to retrieve any credentials from it."""
    if not prefixes or not isinstance(prefixes, (list, tuple, set)):
        prefixes = ("Basic", "Bearer", "Token")
    if header is not None:
        for prefix in prefixes:
            if prefix in header:
                return prefix, header.partition(prefix)[-1].strip()
    return None, header
