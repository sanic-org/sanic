from sanic import helpers


def test_has_message_body():
    tests = (
        (100, False),
        (102, False),
        (204, False),
        (200, True),
        (304, False),
        (400, True),
    )
    for status_code, expected in tests:
        assert helpers.has_message_body(status_code) is expected


def test_is_entity_header():
    tests = (
        ("allow", True),
        ("extension-header", True),
        ("", False),
        ("test", False),
    )
    for header, expected in tests:
        assert helpers.is_entity_header(header) is expected


def test_is_hop_by_hop_header():
    tests = (
        ("connection", True),
        ("upgrade", True),
        ("", False),
        ("test", False),
    )
    for header, expected in tests:
        assert helpers.is_hop_by_hop_header(header) is expected
