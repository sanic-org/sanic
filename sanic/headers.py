from __future__ import annotations

import re

from collections.abc import Iterable
from operator import attrgetter
from typing import Any
from urllib.parse import unquote

from sanic.exceptions import InvalidHeader
from sanic.helpers import STATUS_CODES


_MEDIA_TYPE_KEY = attrgetter("key")


# TODO:
# - the Options object should be a typed object to allow for less casting
#   across the application (in request.py for example)
HeaderIterable = Iterable[tuple[str, Any]]  # Values convertible to str
HeaderBytesIterable = Iterable[tuple[bytes, bytes]]
Options = dict[str, int | str]  # key=value fields in various headers
OptionsIterable = Iterable[tuple[str, str]]  # May contain duplicate keys

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

    __slots__ = ("type", "subtype", "q", "params", "mime", "key")

    def __init__(
        self,
        type_: str,
        subtype: str,
        **params: str,
    ):
        self.type = type_
        self.subtype = subtype
        self.q = float(params["q"]) if "q" in params else 1.0
        self.params = params
        self.mime = f"{type_}/{subtype}"
        self.key = (
            -self.q,
            -len(params),
            subtype == "*",
            type_ == "*",
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
        mime_with_params: str | MediaType,
    ) -> MediaType | None:
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
        if mt is None:
            return None
        if (
            (
                self.subtype == mt.subtype
                or self.subtype == "*"
                or mt.subtype == "*"
            )
            and (self.type == mt.type or self.type == "*" or mt.type == "*")
            and (
                not mt.params
                or all(self.params.get(k) == v for k, v in mt.params.items())
            )
        ):
            return self
        return None

    @property
    def has_wildcard(self) -> bool:
        """Return True if this media type has a wildcard in it.

        Returns:
            bool: True if this media type has a wildcard in it.
        """
        return self.subtype == "*" or self.type == "*"

    @classmethod
    def _parse(cls, mime_with_params: str) -> MediaType | None:
        mtype = mime_with_params.strip()
        if "/" not in mtype:
            return None

        if ";" not in mtype:
            type_, subtype = mtype.split("/", 1)
            if not type_ or not subtype:
                raise ValueError(f"Invalid media type: {mtype}")
            if cls is MediaType:
                obj = cls.__new__(cls)
                obj.type = type_
                obj.subtype = subtype
                obj.q = 1.0
                obj.params = {}
                obj.mime = mtype
                obj.key = (-1.0, 0, subtype == "*", type_ == "*")
                return obj
            return cls(type_, subtype)

        mime, *raw_params = mtype.split(";")
        type_, subtype = mime.split("/", 1)
        if not type_ or not subtype:
            raise ValueError(f"Invalid media type: {mtype}")

        params = {}
        for param in raw_params:
            key, value = param.split("=", 1)
            params[key.strip()] = value.strip()

        if (
            cls is MediaType
            and "self" not in params
            and "type_" not in params
            and "subtype" not in params
        ):
            type_ = type_.lstrip()
            subtype = subtype.rstrip()
            q = float(params["q"]) if "q" in params else 1.0
            obj = cls.__new__(cls)
            obj.type = type_
            obj.subtype = subtype
            obj.q = q
            obj.params = params
            obj.mime = f"{type_}/{subtype}"
            obj.key = (-q, -len(params), subtype == "*", type_ == "*")
            return obj

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

    __slots__ = ("mime", "header")

    def __init__(self, mime: str, header: MediaType | None):
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

    def _compare(self, other) -> tuple[bool, Matched]:
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

    def match(self, other: str | Matched) -> Matched | None:
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
        if not self or not mimes:
            return Matched("", None)

        parsed_mimes: (
            list[tuple[int, str, str, str, dict[str, str] | None]] | None
        ) = None
        best_neg_q = 0.0
        best_i = 0
        best_mime = ""
        best_acc: MediaType | None = None

        for acc in self:
            if not accept_wildcards and (
                acc.subtype == "*" or acc.type == "*"
            ):
                continue

            neg_q = -acc.q
            if best_acc is not None:
                if neg_q > best_neg_q:
                    continue
                if neg_q == best_neg_q and best_i == 0:
                    continue

            same_q = best_acc is not None and neg_q == best_neg_q
            if type(acc) is MediaType:
                if parsed_mimes is None:
                    parsed_mimes = []
                    for i, mime in enumerate(mimes):
                        if isinstance(mime, str):
                            mtype = mime.strip()
                            if "/" not in mtype:
                                continue
                            if ";" not in mtype:
                                mt_type, mt_subtype = mtype.split("/", 1)
                                if not mt_type or not mt_subtype:
                                    raise ValueError(
                                        f"Invalid media type: {mtype}"
                                    )
                                parsed_mimes.append(
                                    (i, mime, mt_type, mt_subtype, None)
                                )
                            else:
                                mt = MediaType._parse(mime)
                                if mt is not None:
                                    parsed_mimes.append(
                                        (
                                            i,
                                            mime,
                                            mt.type,
                                            mt.subtype,
                                            mt.params or None,
                                        )
                                    )
                        elif mime is not None:
                            parsed_mimes.append(
                                (
                                    i,
                                    mime,
                                    mime.type,
                                    mime.subtype,
                                    mime.params or None,
                                )
                            )
                    if not parsed_mimes:
                        return Matched("", None)

                acc_type = acc.type
                acc_subtype = acc.subtype
                acc_params = acc.params
                for i, mime, mt_type, mt_subtype, mt_params in parsed_mimes:
                    if same_q and i >= best_i:
                        break
                    if (
                        (
                            acc_subtype == mt_subtype
                            or acc_subtype == "*"
                            or mt_subtype == "*"
                        )
                        and (
                            acc_type == mt_type
                            or acc_type == "*"
                            or mt_type == "*"
                        )
                        and (
                            mt_params is None
                            or all(
                                acc_params.get(k) == v
                                for k, v in mt_params.items()
                            )
                        )
                    ):
                        best_neg_q = neg_q
                        best_i = i
                        best_mime = mime
                        best_acc = acc
                        break
            else:
                for i, mime in enumerate(mimes):
                    if same_q and i >= best_i:
                        break
                    if acc.match(mime):
                        best_neg_q = neg_q
                        best_i = i
                        best_mime = mime
                        best_acc = acc
                        break

        return Matched(best_mime, best_acc)

    def __str__(self):
        """Format as Accept header value (parsed, not original)."""
        return ", ".join(str(m) for m in self)


def parse_accept(accept: str | None) -> AcceptList:
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
        a = AcceptList()
        parse = MediaType._parse
        for mtype in accept.split(","):
            mt = parse(mtype)
            if mt is not None:
                a.append(mt)
        if not a:
            raise ValueError
        if len(a) > 1:
            a.sort(key=_MEDIA_TYPE_KEY)
        return a
    except ValueError:
        raise InvalidHeader(f"Invalid header value in Accept: {accept}")


def parse_content_header(value: str) -> tuple[str, Options]:
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
        return value.strip().lower(), {}
    options: dict[str, int | str] = {}
    for m in _param.finditer(value, pos):
        val = m.group(2) or m.group(3)
        if "%" in val:
            val = val.replace("%22", '"').replace("%0D%0A", "\n")
        options[m.group(1).lower()] = val
    return value[:pos].strip().lower(), options


# https://tools.ietf.org/html/rfc7230#section-3.2.6 and
# https://tools.ietf.org/html/rfc7239#section-4
# This regex is for *reversed* strings because that works much faster for
# right-to-left matching than the other way around. Be wary that all things are
# a bit backwards! _rparam matches forwarded pairs alike ";key=value"
_rparam = re.compile(f"(?:{_token}|{_quoted})={_token}\\s*($|[;,])", re.ASCII)


def parse_forwarded(headers, config) -> Options | None:
    """Parse RFC 7239 Forwarded headers.
    The value of `by` or `secret` must match `config.FORWARDED_SECRET`
    :return: dict with keys and values, or None if nothing matched
    """
    header = headers.getall("forwarded", None)
    secret = config.FORWARDED_SECRET
    if header is None or not secret:
        return None
    header = header[0] if len(header) == 1 else ",".join(header)
    if secret not in header:
        return None
    # Loop over <separator><key>=<value> elements from right to left
    sep = pos = None
    options_list: list[tuple[str, str]] = []
    found = False
    for m in _rparam.finditer(header[::-1]):
        # Start of new element? (on parser skips and non-semicolon right sep)
        if m.start() != pos or sep != ";":
            # Was the previous element (from right) what we wanted?
            if found:
                break
            # Clear values and parse as new element
            del options_list[:]
        pos = m.end()
        val_token, val_quoted, key, sep = m.groups()
        key = key.lower()[::-1]
        if val_token:
            val = val_token[::-1]
        elif "\\" in val_quoted:
            val = val_quoted.replace('"\\', '"')[::-1]
        else:
            val = val_quoted[::-1]
        options_list.append((key, val))
        if key in ("secret", "by") and val == secret:
            found = True
        # Check if we would return on next round, to avoid useless parse
        if found and sep != ";":
            break
    # If secret was found, return the matching options in left-to-right order
    return fwd_normalize(reversed(options_list)) if found else None


def parse_xforwarded(headers, config) -> Options | None:
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
    ret: dict[str, int | str] = {}
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


def parse_host(host: str) -> tuple[str | None, int | None]:
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
    header: str | None,
    prefixes: list | tuple | set | None = None,
) -> tuple[str | None, str | None]:
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
