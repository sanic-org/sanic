import inspect

import pytest

from sanic import helpers
from sanic.config import Config


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


def test_remove_entity_headers():
    tests = (
        ({}, {}),
        ({"Allow": "GET, POST, HEAD"}, {}),
        (
            {
                "Content-Type": "application/json",
                "Expires": "Wed, 21 Oct 2015 07:28:00 GMT",
                "Foo": "Bar",
            },
            {"Expires": "Wed, 21 Oct 2015 07:28:00 GMT", "Foo": "Bar"},
        ),
        (
            {"Allow": "GET, POST, HEAD", "Content-Location": "/test"},
            {"Content-Location": "/test"},
        ),
    )

    for header, expected in tests:
        assert helpers.remove_entity_headers(header) == expected


def test_import_string_class():
    obj = helpers.import_string("sanic.config.Config")
    assert isinstance(obj, Config)


def test_import_string_module():
    module = helpers.import_string("sanic.config")
    assert inspect.ismodule(module)


def test_import_string_exception():
    with pytest.raises(ImportError):
        helpers.import_string("test.test.test")
