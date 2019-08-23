import re
import typing


Options = typing.Dict[str, str]  # key=value fields in various headers

token, quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
parameter = re.compile(fr";\s*{token}=(?:{token}|{quoted})", re.ASCII)
firefox_quote_escape = re.compile(r'\\"(?!; |\s*$)')

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
    value = firefox_quote_escape.sub("%22", value)
    pos = value.find(";")
    if pos == -1:
        options = {}
    else:
        options = {
            m.group(1).lower(): m.group(2) or m.group(3).replace("%22", '"')
            for m in parameter.finditer(value[pos:])
        }
        value = value[:pos]
    return value.strip().lower(), options
