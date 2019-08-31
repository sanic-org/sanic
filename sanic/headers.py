import re
import typing


Options = typing.Dict[str, str]  # key=value fields in various headers

_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
_param = re.compile(fr";\s*{_token}=(?:{_token}|{_quoted})", re.ASCII)
_firefox_quote_escape = re.compile(r'\\"(?!; |\s*$)')

# RFC's quoted-pair escapes are mostly ignored by browsers. Chrome, Firefox and
# curl all have different escaping, that we try to handle as well as possible,
# even though no client espaces in a way that would allow perfect handling.

# For more information, consult ../tests/test_requests.py


def parse_content_header(value: str) -> typing.Tuple[str, Options]:
    """Parse content-type and content-disposition header values.

    E.g. 'form-data; name=upload; filename=\"file.txt\"' to
    ('form-data', {'name': 'upload', 'filename': 'file.txt'})

    Mostly identical to cgi.parse_header and werkzeug.parse_options_header
    but runs faster and handles special characters better. Unescapes quotes.
    """
    value = _firefox_quote_escape.sub("%22", value)
    pos = value.find(";")
    if pos == -1:
        options = {}
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


def parse_forwarded(headers, config):
    """Parse HTTP Forwarded headers.
    Accepts only the last element with secret=`config.FORWARDED_SECRET`
    :return: dict with matching keys (lowercase) and values, or None.
    """
    header = headers.getall("forwarded", None)
    secret = config.FORWARDED_SECRET
    if header is None or not secret:
        return None
    header = ",".join(header)  # Join multiple header lines
    if secret not in header:
        return None
    # Loop over <separator><key>=<value> elements from right to left
    ret = sep = pos = None
    found = False
    for m in _rparam.finditer(header[::-1]):
        # Start of new element? (on parser skips and non-semicolon right sep)
        if m.start() != pos or sep != ";":
            # Was the previous element (from right) what we wanted?
            if found:
                return normalize(ret)
            # Clear values and parse as new element
            ret = {}
        pos = m.end()
        val_token, val_quoted, key, sep = m.groups()
        key = key.lower()[::-1]
        val = (val_token or val_quoted.replace('"\\', '"'))[::-1]
        ret[key] = val
        if key == "secret" and val == secret:
            found = True
        # Check if we would return on next round, to avoid useless parse
        if found and sep != ";":
            return normalize(ret)
    # If there is garbage on the beginning of the header, we may miss the
    # returns inside the loop and end up here, so check if found and return
    # accordingly:
    return normalize(ret) if found else None


def parse_xforwarded(headers, config):
    """Parse traditional proxy headers."""
    real_ip_header = config.REAL_IP_HEADER
    proxies_count = config.PROXIES_COUNT
    addr = real_ip_header and headers.get(real_ip_header)
    if not addr and proxies_count:
        try:
            # Combine, split and filter multiple headers' entries
            forwarded_for = headers.getall(config.FORWARDED_FOR_HEADER)
            proxies = (p.strip() for h in forwarded_for for p in h.split(","))
            proxies = [p for p in proxies if p]
            addr = proxies[-proxies_count] if proxies_count > 0 else proxies[0]
        except (KeyError, IndexError):
            pass
    # No processing of other headers if no address is found
    if not addr:
        return None
    other = (
        (key, headers.get(header))
        for key, header in (
            ("proto", "x-scheme"),
            ("proto", "x-forwarded-proto"),  # Overrides X-Scheme if present
            ("host", "x-forwarded-host"),
            ("port", "x-forwarded-port"),
            ("path", "x-forwarded-path"),
        )
    )
    return normalize({"for": addr, **{k: v for k, v in other if v}})


_ipv6 = "(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}"
_ipv6_re = re.compile(_ipv6)
_host_re = re.compile(
    r"((?:\[" + _ipv6 + r"\])|[a-zA-Z0-9.\-]{1,253})(?::(\d{1,5}))?"
)


def parse_host(host):
    m = _host_re.fullmatch(host)
    if not m:
        return None, None
    host, port = m.groups()
    return host.lower(), port and int(port)


def bracketv6(addr):
    return f"[{addr}]" if _ipv6_re.fullmatch(addr) else addr

def normalize(fwd: dict) -> dict:
    """Normalize and convert values extracted from forwarded headers.
    Modifies fwd in place and returns the same object.
    """
    if "proto" in fwd:
        fwd["proto"] = fwd["proto"].lower()
    if "by" in fwd:
        fwd["by"] = bracketv6(fwd["by"]).lower()
    if "for" in fwd:
        fwd["for"] = bracketv6(fwd["for"]).lower()
    if "port" in fwd:
        try:
            fwd["port"] = int(fwd["port"])
        except ValueError:
            del fwd["port"]
    if "host" in fwd:
        host, port = parse_host(fwd["host"])
        if host:
            fwd["host"] = host
            if port:
                fwd["port"] = port
        else:
            del fwd["host"]
    return fwd
