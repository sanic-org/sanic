from __future__ import annotations

import re

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
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
_param = re.compile(fr";\s*{_token}=(?:{_token}|{_quoted})", re.ASCII)
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
        if not isinstance(other, Accept) and other:
            other = Accept.parse(other)
        return f(self, other, *args, **kwargs)

    return func


class MediaType(str):
    def __new__(cls, value: str):
        return str.__new__(cls, value)

    def __init__(self, value: str) -> None:
        self.value = value
        self.is_wildcard = self.check_if_wildcard(value)

    def __eq__(self, other):
        if self.is_wildcard:
            return True

        if self.match(other):
            return True

        other_is_wildcard = (
            other.is_wildcard
            if isinstance(other, MediaType)
            else self.check_if_wildcard(other)
        )

        return other_is_wildcard

    def match(self, other):
        other_value = other.value if isinstance(other, MediaType) else other
        return self.value == other_value

    @staticmethod
    def check_if_wildcard(value):
        return value == "*"


class Accept(str):
    def __new__(cls, value: str, *args, **kwargs):
        return str.__new__(cls, value)

    def __init__(
        self,
        value: str,
        type_: MediaType,
        subtype: MediaType,
        *,
        q: str = "1.0",
        **kwargs: str,
    ):
        qvalue = float(q)
        if qvalue > 1 or qvalue < 0:
            raise InvalidHeader(
                f"Accept header qvalue must be between 0 and 1, not: {qvalue}"
            )
        self.value = value
        self.type_ = type_
        self.subtype = subtype
        self.qvalue = qvalue
        self.params = kwargs

    def _compare(self, other, method):
        try:
            return method(self.qvalue, other.qvalue)
        except (AttributeError, TypeError):
            return NotImplemented

    @parse_arg_as_accept
    def __lt__(self, other: Union[str, Accept]):
        return self._compare(other, lambda s, o: s < o)

    @parse_arg_as_accept
    def __le__(self, other: Union[str, Accept]):
        return self._compare(other, lambda s, o: s <= o)

    @parse_arg_as_accept
    def __eq__(self, other: Union[str, Accept]):  # type: ignore
        return self._compare(other, lambda s, o: s == o)

    @parse_arg_as_accept
    def __ge__(self, other: Union[str, Accept]):
        return self._compare(other, lambda s, o: s >= o)

    @parse_arg_as_accept
    def __gt__(self, other: Union[str, Accept]):
        return self._compare(other, lambda s, o: s > o)

    @parse_arg_as_accept
    def __ne__(self, other: Union[str, Accept]):  # type: ignore
        return self._compare(other, lambda s, o: s != o)

    @parse_arg_as_accept
    def match(
        self,
        other,
        *,
        allow_type_wildcard: bool = True,
        allow_subtype_wildcard: bool = True,
    ) -> bool:
        type_match = (
            self.type_ == other.type_
            if allow_type_wildcard
            else (
                self.type_.match(other.type_)
                and not self.type_.is_wildcard
                and not other.type_.is_wildcard
            )
        )
        subtype_match = (
            self.subtype == other.subtype
            if allow_subtype_wildcard
            else (
                self.subtype.match(other.subtype)
                and not self.subtype.is_wildcard
                and not other.subtype.is_wildcard
            )
        )

        return type_match and subtype_match

    @classmethod
    def parse(cls, raw: str) -> Accept:
        invalid = False
        mtype = raw.strip()

        try:
            media, *raw_params = mtype.split(";")
            type_, subtype = media.split("/")
        except ValueError:
            invalid = True

        if invalid or not type_ or not subtype:
            raise InvalidHeader(f"Header contains invalid Accept value: {raw}")

        params = dict(
            [
                (key.strip(), value.strip())
                for key, value in (param.split("=", 1) for param in raw_params)
            ]
        )

        return cls(mtype, MediaType(type_), MediaType(subtype), **params)


class AcceptContainer(list):
    def __contains__(self, o: object) -> bool:
        return any(item.match(o) for item in self)

    def match(
        self,
        o: object,
        *,
        allow_type_wildcard: bool = True,
        allow_subtype_wildcard: bool = True,
    ) -> bool:
        return any(
            item.match(
                o,
                allow_type_wildcard=allow_type_wildcard,
                allow_subtype_wildcard=allow_subtype_wildcard,
            )
            for item in self
        )


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


def _sort_accept_value(accept: Accept):
    return (
        accept.qvalue,
        len(accept.params),
        accept.subtype != "*",
        accept.type_ != "*",
    )


def parse_accept(accept: str) -> AcceptContainer:
    """Parse an Accept header and order the acceptable media types in
    accorsing to RFC 7231, s. 5.3.2
    https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.2
    """
    media_types = accept.split(",")
    accept_list: List[Accept] = []

    for mtype in media_types:
        if not mtype:
            continue

        accept_list.append(Accept.parse(mtype))

    return AcceptContainer(
        sorted(accept_list, key=_sort_accept_value, reverse=True)
    )
