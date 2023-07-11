from datetime import datetime, timezone
from logging import INFO

import pytest

from sanic.compat import Header
from sanic.response.convenience import validate_file


@pytest.mark.parametrize(
    "ifmod,lastmod,expected",
    (
        ("Sat, 01 Apr 2023 00:00:00 GMT", 1672524000, None),
        (
            "Sat, 01 Apr 2023 00:00:00",
            1672524000,
            "converting if_modified_since",
        ),
        (
            "Sat, 01 Apr 2023 00:00:00 GMT",
            datetime(2023, 1, 1, 0, 0, 0),
            "converting last_modified",
        ),
        (
            "Sat, 01 Apr 2023 00:00:00",
            datetime(2023, 1, 1, 0, 0, 0),
            None,
        ),
        (
            "Sat, 01 Apr 2023 00:00:00 GMT",
            datetime(2023, 1, 1, 0, 0, 0).replace(tzinfo=timezone.utc),
            None,
        ),
        (
            "Sat, 01 Apr 2023 00:00:00",
            datetime(2023, 1, 1, 0, 0, 0).replace(tzinfo=timezone.utc),
            "converting if_modified_since",
        ),
    ),
)
@pytest.mark.asyncio
async def test_file_timestamp_validation(
    lastmod, ifmod, expected, caplog: pytest.LogCaptureFixture
):
    headers = Header([["If-Modified-Since", ifmod]])

    with caplog.at_level(INFO):
        response = await validate_file(headers, lastmod)
    assert response.status == 304
    records = caplog.records
    if not expected:
        assert len(records) == 0
    else:
        record = records[0]
        assert expected in record.message
