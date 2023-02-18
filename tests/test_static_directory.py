import os

from pathlib import Path

import pytest

from sanic import Sanic
from sanic.handlers.directory import DirectoryHandler


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
    assert response.headers["Content-Type"] == "text/html"


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
    assert response.headers["Content-Type"] == "text/html"


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
    assert response.content_type == "text/plain"


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
    assert response.content_type == "text/plain"


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
