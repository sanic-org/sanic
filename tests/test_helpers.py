from sanic.helpers import has_message_body


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
        assert has_message_body(status_code) is expected
