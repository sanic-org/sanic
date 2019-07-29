import re

token, quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"((?:[^"]|\\")*)"'
parameter = re.compile(fr';\s*{token}=(?:{token}|{quoted})', re.ASCII)


def parse_options_header(value: str):
    """Parse HTTP header values of Content-Type format."""
    pos = value.find(';')
    if pos == -1:
        options = {}
    else:
        options = {
            m.group(1).lower(): m.group(2) or m.group(3).replace(r'\"', '"')
            for m in parameter.finditer(value[pos:])
        }
        value = value[:pos]
    return value.strip().lower(), options
