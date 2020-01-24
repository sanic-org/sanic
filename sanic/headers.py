import re

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import unquote

from sanic.helpers import STATUS_CODES


HeaderIterable = Iterable[Tuple[str, Any]]  # Values convertible to str
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
# even though no client espaces in a way that would allow perfect handling.

# For more information, consult ../tests/test_requests.py


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
    addr = real_ip_header and headers.get(real_ip_header)
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
            yield key, headers.get(header)

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


def format_http1(headers: HeaderIterable) -> bytes:
    """Convert a headers iterable into HTTP/1 header format.

    - Outputs UTF-8 bytes where each header line ends with \\r\\n.
    - Values are converted into strings if necessary.
    """
    return "".join(f"{name}: {val}\r\n" for name, val in headers).encode()


def format_http1_response(
    status: int, headers: HeaderIterable, body=b""
) -> bytes:
    """Format a full HTTP/1.1 response.

    - If `body` is included, content-length must be specified in headers.
    """
    headerbytes = format_http1(headers)
    return b"HTTP/1.1 %d %b\r\n%b\r\n%b" % (
        status,
        STATUS_CODES.get(status, b"UNKNOWN"),
        headerbytes,
        body,
    )
