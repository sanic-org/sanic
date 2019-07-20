import re

# https://tools.ietf.org/html/rfc7230#section-3.2.6 and https://tools.ietf.org/html/rfc7239#section-4
_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
# _forwarded_pair = re.compile(f'(^|[;,])\\s*{_token}=(?:{_token}|{_quoted})', re.ASCII)
# Same as forwarded_pair but with reversed string because that allows fast matching from end
_forwarded_reverse = re.compile(f'(?:{_token}|{_quoted})={_token}\\s*($|[;,])', re.ASCII)

def parse_forwarded(header, secret=None):
    """Parse HTTP Forwarded header.
    Last proxy is returned, or if a secret is provided, a proxy with secret="yoursecret".
    :return: dict with fields from matched element
    """
    if header is None or secret is not None and secret not in header:
        return None
    ret = {}
    for m in _forwarded_reverse.finditer(header[::-1]):
        val_quoted, val_token, key, sep = m.groups()
        key, val = key.lower()[::-1], (val_token or val_quoted)[::-1]
        if key != 'secret': ret[key] = val
        elif val == secret: secret = None
        if sep == ";": continue
        if secret is None: break
        ret = {}  # Advancing to previous comma-separated element
    return ret if secret is None and ret else None

def parse_xforwarded(headers, config):
    """Parse X-Real-IP and X-Forwarded-* headers."""
    addr = config.REAL_IP_HEADER and headers.get(config.REAL_IP_HEADER)
    forwarded_for = config.FORWARDED_FOR_HEADER and headers.get(config.FORWARDED_FOR_HEADER)
    if not addr and forwarded_for:
        proxies_count = config.PROXIES_COUNT
        assert proxies_count == -1 or proxies_count > 0, config.PROXIES_COUNT
        try:
            proxies = forwarded_for.split(",")
            addr = proxies[-proxies_count] if proxies_count > 0 else proxies[0]
        except (AttributeError, IndexError):
            return None
        addr = addr.strip()
    if not addr:
        return None
    other = (
        ('proto', headers.get('x-scheme')),
        *((h, headers.get(f'x-forwarded-{h}')) for h in ('proto', 'host', 'port', 'path'))
    )
    return {'for': addr, **{h: v for h, v in other if v}}
