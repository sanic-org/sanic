import re
import typing


Options = typing.Dict[str, str]  # key=value fields in various headers

token, quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
parameter = re.compile(fr";\s*{token}=(?:{token}|{quoted})", re.ASCII)

# Note: this intentionally leaves out the quoted-pair escape sequence specified
# in RFCs because browsers escape quotes as %22 and do not escape backslashes.
# In particular, a file upload named foo"bar\ is sent as filename="foo%22bar\"
# by all browsers, and would parse incorrectly if quoted-pair were handled.


def parse_content_header(value: str) -> typing.Tuple[str, Options]:
    """Parse content-type and content-disposition header values.

    E.g. 'form-data; name=upload; filename=\"file.txt\"' to
    ('form-data', {'name': 'upload', 'filename': 'file.txt'})

    Mostly identical to cgi.parse_header and werkzeug.parse_options_header
    but runs faster. Like the others, does NOT unescape anything.
    """
    pos = value.find(";")
    if pos == -1:
        options = {}
    else:
        options = {
            m.group(1).lower(): m.group(2) or m.group(3)
            for m in parameter.finditer(value[pos:])
        }
        value = value[:pos]
    return value.strip().lower(), options
