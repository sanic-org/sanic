import os
import tempfile

from pathlib import Path

import pytest

from sanic import Sanic
from sanic.handlers.directory import DirectoryHandler


pytestmark = pytest.mark.xdist_group(name="static_files")


def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), "rb") as file:
        return file.read()


def test_static_directory_view(app: Sanic, static_file_directory: str):
    app.static("/static", static_file_directory, directory_view=True)

    _, response = app.test_client.get("/static/")
    assert response.status == 200
    assert response.content_type == "text/html; charset=utf-8"
    assert "<title>Directory Viewer</title>" in response.text


def test_static_index_single(app: Sanic, static_file_directory: str):
    app.static("/static", static_file_directory, index="test.html")

    _, response = app.test_client.get("/static/")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.html"
    )
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_static_index_single_not_found(app: Sanic, static_file_directory: str):
    app.static("/static", static_file_directory, index="index.html")

    _, response = app.test_client.get("/static/")
    assert response.status == 404


def test_static_index_multiple(app: Sanic, static_file_directory: str):
    app.static(
        "/static",
        static_file_directory,
        index=["index.html", "test.html"],
    )

    _, response = app.test_client.get("/static/")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.html"
    )
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_static_directory_view_and_index(
    app: Sanic, static_file_directory: str
):
    app.static(
        "/static",
        static_file_directory,
        directory_view=True,
        index="foo.txt",
    )

    _, response = app.test_client.get("/static/nested/")
    assert response.status == 200
    assert response.content_type == "text/html; charset=utf-8"
    assert "<title>Directory Viewer</title>" in response.text

    _, response = app.test_client.get("/static/nested/dir/")
    assert response.status == 200
    assert response.body == get_file_content(
        f"{static_file_directory}/nested/dir", "foo.txt"
    )
    assert response.content_type == "text/plain; charset=utf-8"


def test_static_directory_handler(app: Sanic, static_file_directory: str):
    dh = DirectoryHandler(
        "/static",
        Path(static_file_directory),
        directory_view=True,
        index="foo.txt",
    )
    app.static("/static", static_file_directory, directory_handler=dh)

    _, response = app.test_client.get("/static/nested/")
    assert response.status == 200
    assert response.content_type == "text/html; charset=utf-8"
    assert "<title>Directory Viewer</title>" in response.text

    _, response = app.test_client.get("/static/nested/dir/")
    assert response.status == 200
    assert response.body == get_file_content(
        f"{static_file_directory}/nested/dir", "foo.txt"
    )
    assert response.content_type == "text/plain; charset=utf-8"


def test_static_directory_handler_fails(app: Sanic):
    dh = DirectoryHandler(
        "/static",
        Path(""),
        directory_view=True,
        index="foo.txt",
    )
    message = (
        "When explicitly setting directory_handler, you cannot "
        "set either directory_view or index. Instead, pass "
        "these arguments to your DirectoryHandler instance."
    )
    with pytest.raises(ValueError, match=message):
        app.static("/static", "", directory_handler=dh, directory_view=True)
    with pytest.raises(ValueError, match=message):
        app.static("/static", "", directory_handler=dh, index="index.html")


@pytest.mark.parametrize(
    "dir_name",
    [
        "你好",  # Chinese
        "こんにちは",  # Japanese
        "안녕하세요",  # Korean
        "hello 世界",  # Mixed ASCII and CJK
    ],
)
def test_static_index_with_cjk_directory_name(app: Sanic, dir_name: str):
    """Test static file serving with CJK characters in directory names.

    See: https://github.com/sanic-org/sanic/issues/3008
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory with CJK name containing an index file
        cjk_dir = Path(tmpdir) / dir_name
        cjk_dir.mkdir()
        index_file = cjk_dir / "index.html"
        index_content = b"<html>Hello from CJK directory</html>"
        index_file.write_bytes(index_content)

        app.static("/static", tmpdir, index="index.html")

        # Access the CJK directory - should serve index.html
        _, response = app.test_client.get(f"/static/{dir_name}/")
        assert response.status == 200
        assert response.body == index_content
