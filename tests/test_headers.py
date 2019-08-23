import pytest

from sanic import headers


@pytest.mark.parametrize(
    "input, expected",
    [
        ("text/plain", ("text/plain", {})),
        ("text/vnd.just.made.this.up ; ", ("text/vnd.just.made.this.up", {})),
        ("text/plain;charset=us-ascii", ("text/plain", {"charset": "us-ascii"})),
        ('text/plain ; charset="us-ascii"', ("text/plain", {"charset": "us-ascii"})),
        (
            'text/plain ; charset="us-ascii"; another=opt',
            ("text/plain", {"charset": "us-ascii", "another": "opt"})
        ),
        (
            'attachment; filename="silly.txt"',
            ("attachment", {"filename": "silly.txt"})
        ),
        (
            'attachment; filename="strange;name"',
            ("attachment", {"filename": "strange;name"})
        ),
        (
            'attachment; filename="strange;name";size=123;',
            ("attachment", {"filename": "strange;name", "size": "123"})
        ),
        (
            # Note: browsers don't use quoted-pair escapes but instead %22 for
            # double quote (which gets unquoted later on in sanic.request),
            # and backslashes are *NOT* escaped.
            'form-data; name="files"; filename="fo%22o;bar\\"',
            ("form-data", {"name": "files", "filename": 'fo%22o;bar\\'})
        ),
    ]
)
def test_parse_headers(input, expected):
    assert headers.parse_content_header(input) == expected
