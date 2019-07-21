import re


# https://tools.ietf.org/html/rfc7230#section-3.2.6 and
# https://tools.ietf.org/html/rfc7239#section-4
# These regexes are for *reversed* strings because that works much faster for
# right-to-left matching than the other way around. Be wary that all things are
# a bit backwards! _regex matches forwarded pairs alike ";key=value"
_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"((?:[^"]|"\\)*)"'
_regex = re.compile(f"(?:{_token}|{_quoted})={_token}\\s*($|[;,])", re.ASCII)


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
    forwarded_for = h2 and headers.getall(h2, None)
    if not addr and forwarded_for:
        assert proxies_count == -1 or proxies_count > 0, config.PROXIES_COUNT
        # Combine, split and filter multiple headers' entries
        proxies = (p.strip() for h in forwarded_for for p in h.split(","))
        proxies = [p for p in proxies if p]
        try:
            addr = proxies[-proxies_count] if proxies_count > 0 else proxies[0]
        except IndexError:
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
