import re


# https://tools.ietf.org/html/rfc7230#section-3.2.6 and
# https://tools.ietf.org/html/rfc7239#section-4
_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
# forwarded_pair = f'(^|[;,])\\s*{_token}=(?:{_token}|{_quoted})', re.ASCII)
# Same as forwarded_pair but for fast *reverse* string matching:
_regex = re.compile(f"(?:{_token}|{_quoted})={_token}\\s*($|[;,])", re.ASCII)


def parse_forwarded(header, secret=None):
    """Parse HTTP Forwarded header.
    Last proxy is returned, or if a secret is provided, a proxy with
    secret="yoursecret".
    :return: dict with fields from matched element
    """
    if header is None or secret is not None and secret not in header:
        return None
    ret = {}
    pos = len(header)
    # Loop over <separator><key>=<value> elements from right to left
    for m in _regex.finditer(header[::-1]):
        # If scanner jumps over something unrecognized, clear values
        if m.end() != pos:
            ret = {}
        pos = m.start()
        val_quoted, val_token, key, sep = m.groups()
        key, val = key.lower()[::-1], (val_token or val_quoted)[::-1]
        ret[key] = val
        if secret is not None and key == "secret" and val == secret:
            secret = None
        if sep != ";":
            # Element done; stop parsing if secret matched
            if secret is None:
                break
            ret = {}  # Advancing to previous comma-separated element
    return ret if secret is None and ret else None


def parse_xforwarded(headers, config):
    """Parse X-Real-IP and X-Forwarded-* headers."""
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
            ("proto", "x-forwarded-proto"),
            ("host", "x-forwarded-host"),
            ("port", "x-forwarded-port"),
            ("path", "x-forwarded-path"),
        )
    )
    return {"for": addr, **{k: v for k, v in other if v}}
