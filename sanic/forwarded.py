import re


# https://tools.ietf.org/html/rfc7230#section-3.2.6 and
# https://tools.ietf.org/html/rfc7239#section-4
# These regexes are for *reversed* strings because that works much faster for
# right-to-left matching than the other way around. Be wary that all things are
# a bit backwards! _regex matches forwarded pairs alike ";key=value"
_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"((?:[^"]|"\\)*)"'
_regex = re.compile(f"(?:{_token}|{_quoted})={_token}\\s*($|[;,])", re.ASCII)


def parse_forwarded(header: str, secret: str) -> dict:
    """Parse HTTP Forwarded header.
    Accepts only the rightmost element that includes secret="yoursecret".
    :return: dict with matching keys (lower case) and values, or None.
    """
    if header is None or not secret or secret not in header:
        return None
    # Loop over <separator><key>=<value> elements from right to left
    ret = sep = pos = None
    for m in _regex.finditer(header[::-1]):
        # Start of new element? (on parser skips and non-semicolon right sep)
        if m.start() != pos or sep != ";":
            if secret is True:
                return ret
            ret = {}
        pos = m.end()
        val_token, val_quoted, key, sep = m.groups()
        key = key.lower()[::-1]
        val = (val_token or val_quoted.replace('"\\', '"'))[::-1]
        ret[key] = val
        if secret is not True and key == "secret" and val == secret:
            secret = True
        if secret is True and sep != ";":
            return ret
    return ret if secret is True else None


def parse_xforwarded(headers, config):
    """Parse X-Real-IP, X-Scheme and X-Forwarded-* headers."""
    proxies_count = config.PROXIES_COUNT
    if not proxies_count:
        return None
    h1, h2 = config.REAL_IP_HEADER, config.FORWARDED_FOR_HEADER
    addr = h1 and headers.get(h1)
    forwarded_for = h2 and headers.get(h2)
    if not addr and forwarded_for:
        assert proxies_count == -1 or proxies_count > 0, config.PROXIES_COUNT
        try:
            proxies = [
                p for p in map(str.strip, forwarded_for.split(",")) if p
            ]
            addr = proxies[-proxies_count] if proxies_count > 0 else proxies[0]
        except (AttributeError, IndexError):
            return None
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
    return {"for": addr, **{k: v for k, v in other if v}}
