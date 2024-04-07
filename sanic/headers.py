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
_ipv6 = "(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}"
_ipv6_re = re.compile(_ipv6)
_host_re = re.compile(
    r"((?:\[" + _ipv6 + r"\])|[a-zA-Z0-9.\-]{1,253})(?::(\d{1,5}))?"
)

# RFC's quoted-pair escapes are mostly ignored by browsers. Chrome, Firefox and
# curl all have different escaping, that we try to handle as well as possible,
# even though no client escapes in a way that would allow perfect handling.

# For more information, consult ../tests/test_requests.py


class MediaType:
    """A media type, as used in the Accept header.

    This class is a representation of a media type, as used in the Accept
    header. It encapsulates the type, subtype and any parameters, and
    provides methods for matching against other media types.

    Two separate methods are provided for searching the list:
    - 'match' for finding the most preferred match (wildcards supported)
    -  operator 'in' for checking explicit matches (wildcards as literals)

    Args:
        type_ (str): The type of the media type.
        subtype (str): The subtype of the media type.
        **params (str): Any parameters for the media type.
    """

    def __init__(
        self,
        type_: str,
        subtype: str,
        **params: str,
    ):
        self.type = type_
        self.subtype = subtype
        self.q = float(params.get("q", "1.0"))
        self.params = params
        self.mime = f"{type_}/{subtype}"
        self.key = (
            -1 * self.q,
            -1 * len(self.params),
            self.subtype == "*",
            self.type == "*",
        )

    def __repr__(self):
        return self.mime + "".join(f";{k}={v}" for k, v in self.params.items())

    def __eq__(self, other):
        """Check for mime (str or MediaType) identical type/subtype.
        Parameters such as q are not considered."""
        if isinstance(other, str):
            # Give a friendly reminder if str contains parameters
            if ";" in other:
                raise ValueError("Use match() to compare with parameters")
            return self.mime == other
        if isinstance(other, MediaType):
            # Ignore parameters silently with MediaType objects
            return self.mime == other.mime
        return NotImplemented

    def match(
        self,
        mime_with_params: Union[str, MediaType],
    ) -> Optional[MediaType]:
        """Match this media type against another media type.

        Check if this media type matches the given mime type/subtype.
        Wildcards are supported both ways on both type and subtype.
        If mime contains a semicolon, optionally followed by parameters,
        the parameters of the two media types must match exactly.

        .. note::
            Use the `==` operator instead to check for literal matches
            without expanding wildcards.


        Args:
            media_type (str): A type/subtype string to match.

        Returns:
            MediaType: Returns `self` if the media types are compatible.
            None: Returns `None` if the media types are not compatible.
        """
        mt = (
            MediaType._parse(mime_with_params)
            if isinstance(mime_with_params, str)
            else mime_with_params
        )
        return (
            self
            if (
                mt
                # All parameters given in the other media type must match
                and all(self.params.get(k) == v for k, v in mt.params.items())
                # Subtype match
                and (
                    self.subtype == mt.subtype
                    or self.subtype == "*"
                    or mt.subtype == "*"
                )
                # Type match
                and (
                    self.type == mt.type or self.type == "*" or mt.type == "*"
                )
            )
            else None
        )

    @property
    def has_wildcard(self) -> bool:
        """Return True if this media type has a wildcard in it.

        Returns:
            bool: True if this media type has a wildcard in it.
        """
        return any(part == "*" for part in (self.subtype, self.type))

    @classmethod
    def _parse(cls, mime_with_params: str) -> Optional[MediaType]:
        mtype = mime_with_params.strip()
        if "/" not in mime_with_params:
            return None

        mime, *raw_params = mtype.split(";")
        type_, subtype = mime.split("/", 1)
        if not type_ or not subtype:
            raise ValueError(f"Invalid media type: {mtype}")

        params = dict(
            [
                (key.strip(), value.strip())
                for key, value in (param.split("=", 1) for param in raw_params)
            ]
        )

        return cls(type_.lstrip(), subtype.rstrip(), **params)


class Matched:
    """A matching result of a MIME string against a header.

    This class is a representation of a matching result of a MIME string
    against a header. It encapsulates the MIME string, the header, and
    provides methods for matching against other MIME strings.

    Args:
        mime (str): The MIME string to match.
        header (MediaType): The header to match against, if any.
    """

    def __init__(self, mime: str, header: Optional[MediaType]):
        self.mime = mime
        self.header = header

    def __repr__(self):
        return f"<{self} matched {self.header}>" if self else "<no match>"

    def __str__(self):
        return self.mime

    def __bool__(self):
        return self.header is not None

    def __eq__(self, other: Any) -> bool:
        try:
            comp, other_accept = self._compare(other)
        except TypeError:
            return False

        return bool(
            comp
            and (
                (self.header and other_accept.header)
                or (not self.header and not other_accept.header)
            )
        )

    def _compare(self, other) -> Tuple[bool, Matched]:
        if isinstance(other, str):
            parsed = Matched.parse(other)
            if self.mime == other:
                return True, parsed
            other = parsed

        if isinstance(other, Matched):
            return self.header == other.header, other

        raise TypeError(
            "Comparison not supported between unequal "
            f"mime types of '{self.mime}' and '{other}'"
        )

    def match(self, other: Union[str, Matched]) -> Optional[Matched]:
        """Match this MIME string against another MIME string.

        Check if this MIME string matches the given MIME string. Wildcards are supported both ways on both type and subtype.

        Args:
            other (str): A MIME string to match.

        Returns:
            Matched: Returns `self` if the MIME strings are compatible.
            None: Returns `None` if the MIME strings are not compatible.
        """  # noqa: E501
        accept = Matched.parse(other) if isinstance(other, str) else other
        if not self.header or not accept.header:
            return None
        if self.header.match(accept.header):
            return accept
        return None

    @classmethod
    def parse(cls, raw: str) -> Matched:
        media_type = MediaType._parse(raw)
        return cls(raw, media_type)


class AcceptList(list):
    """A list of media types, as used in the Accept header.

    The Accept header entries are listed in order of preference, starting
    with the most preferred. This class is a list of `MediaType` objects,
    that encapsulate also the q value or any other parameters.

    Two separate methods are provided for searching the list:
    - 'match' for finding the most preferred match (wildcards supported)
    -  operator 'in' for checking explicit matches (wildcards as literals)

    Args:
        *args (MediaType): Any number of MediaType objects.
    """

    def match(self, *mimes: str, accept_wildcards=True) -> Matched:
        """Find a media type accepted by the client.

        This method can be used to find which of the media types requested by
        the client is most preferred against the ones given as arguments.

        The ordering of preference is set by:
        1. The order set by RFC 7231, s. 5.3.2, giving a higher priority
            to q values and more specific type definitions,
        2. The order of the arguments (first is most preferred), and
        3. The first matching entry on the Accept header.

        Wildcards are matched both ways. A match is usually found, as the
        Accept headers typically include `*/*`, in particular if the header
        is missing, is not manually set, or if the client is a browser.

        Note: the returned object behaves as a string of the mime argument
        that matched, and is empty/falsy if no match was found. The matched
        header entry `MediaType` or `None` is available as the `m` attribute.

        Args:
            mimes (List[str]): Any MIME types to search for in order of preference.
            accept_wildcards (bool): Match Accept entries with wildcards in them.

        Returns:
            Match: A match object with the mime string and the MediaType object.
        """  # noqa: E501
        a = sorted(
            (-acc.q, i, j, mime, acc)
            for j, acc in enumerate(self)
            if accept_wildcards or not acc.has_wildcard
            for i, mime in enumerate(mimes)
            if acc.match(mime)
        )
        return Matched(*(a[0][-2:] if a else ("", None)))

    def __str__(self):
        """Format as Accept header value (parsed, not original)."""
        return ", ".join(str(m) for m in self)


def parse_accept(accept: Optional[str]) -> AcceptList:
    """Parse an Accept header and order the acceptable media types according to RFC 7231, s. 5.3.2

    https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.2

    Args:
        accept (str): The Accept header value to parse.

    Returns:
        AcceptList: A list of MediaType objects, ordered by preference.

    Raises:
        InvalidHeader: If the header value is invalid.
    """  # noqa: E501
    if not accept:
        if accept == "":
            return AcceptList()  # Empty header, accept nothing
        accept = "*/*"  # No header means that all types are accepted
    try:
        a = [
            mt
            for mt in [MediaType._parse(mtype) for mtype in accept.split(",")]
            if mt
        ]
        if not a:
            raise ValueError
        return AcceptList(sorted(a, key=lambda x: x.key))
    except ValueError:
        raise InvalidHeader(f"Invalid header value in Accept: {accept}")


def parse_content_header(value: str) -> Tuple[str, Options]:
    """Parse content-type and content-disposition header values.

    E.g. `form-data; name=upload; filename="file.txt"` to
    ('form-data', {'name': 'upload', 'filename': 'file.txt'})

    Mostly identical to cgi.parse_header and werkzeug.parse_options_header
    but runs faster and handles special characters better.

    Unescapes %22 to `"` and %0D%0A to `\n` in field values.

    Args:
        value (str): The header value to parse.

    Returns:
        Tuple[str, Options]: The header value and a dict of options.
    """
    pos = value.find(";")
    if pos == -1:
        options: Dict[str, Union[int, str]] = {}
    else:
        options = {
            m.group(1).lower(): (m.group(2) or m.group(3))
            .replace("%22", '"')
            .replace("%0D%0A", "\n")
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
    """Normalize and convert values extracted from forwarded headers.

    Args:
        fwd (OptionsIterable): An iterable of key-value pairs.

    Returns:
        Options: A dict of normalized key-value pairs.
    """
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
    """Normalize address fields of proxy headers.

    Args:
        addr (str): An address string.

    Returns:
        str: A normalized address string.
    """
    if addr == "unknown":
        raise ValueError()  # omit unknown value identifiers
    if addr.startswith("_"):
        return addr  # do not lower-case obfuscated strings
    if _ipv6_re.fullmatch(addr):
        addr = f"[{addr}]"  # bracket IPv6
    return addr.lower()


def parse_host(host: str) -> Tuple[Optional[str], Optional[int]]:
    """Split host:port into hostname and port.

    Args:
        host (str): A host string.

    Returns:
        Tuple[Optional[str], Optional[int]]: A tuple of hostname and port.
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
    """Format a HTTP/1.1 response header.

    Args:
        status (int): The HTTP status code.
        headers (HeaderBytesIterable): An iterable of header tuples.

    Returns:
        bytes: The formatted response header.
    """
    # Note: benchmarks show that here bytes concat is faster than bytearray,
    # b"".join() or %-formatting. %timeit any changes you make.
    ret = _HTTP1_STATUSLINES[status]
    for h in headers:
        ret += b"%b: %b\r\n" % h
    ret += b"\r\n"
    return ret


def parse_credentials(
    header: Optional[str],
    prefixes: Optional[Union[List, Tuple, Set]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Parses any header with the aim to retrieve any credentials from it.

    Args:
        header (Optional[str]): The header to parse.
        prefixes (Optional[Union[List, Tuple, Set]], optional): The prefixes to look for. Defaults to None.

    Returns:
        Tuple[Optional[str], Optional[str]]: The prefix and the credentials.
    """  # noqa: E501
    if not prefixes or not isinstance(prefixes, (list, tuple, set)):
        prefixes = ("Basic", "Bearer", "Token")
    if header is not None:
        for prefix in prefixes:
            if prefix in header:
                return prefix, header.partition(prefix)[-1].strip()
    return None, header
