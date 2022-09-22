import inspect
import logging
import os
import sys

from collections import Counter
from pathlib import Path
from time import gmtime, strftime

import pytest

from sanic import Sanic, text
from sanic.exceptions import FileNotFound


@pytest.fixture(scope="module")
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, "static")
    return static_directory


@pytest.fixture(scope="module")
def double_dotted_directory_file(static_file_directory: str):
    """Generate double dotted directory and its files"""
    if sys.platform == "win32":
        raise Exception("Windows doesn't support double dotted directories")

    file_path = Path(static_file_directory) / "dotted.." / "dot.txt"
    double_dotted_dir = file_path.parent
    Path.mkdir(double_dotted_dir, exist_ok=True)
    with open(file_path, "w") as f:
        f.write("DOT\n")
    yield file_path
    Path.unlink(file_path)
    Path.rmdir(double_dotted_dir)


def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), "rb") as file:
        return file.read()


@pytest.fixture(scope="module")
def large_file(static_file_directory):
    large_file_path = os.path.join(static_file_directory, "large.file")

    size = 2 * 1024 * 1024
    with open(large_file_path, "w") as f:
        f.write("a" * size)

    yield large_file_path

    os.remove(large_file_path)


@pytest.fixture(autouse=True, scope="module")
def symlink(static_file_directory):
    src = os.path.abspath(
        os.path.join(os.path.dirname(static_file_directory), "conftest.py")
    )
    symlink = "symlink"
    dist = os.path.join(static_file_directory, symlink)
    os.symlink(src, dist)
    yield symlink
    os.remove(dist)


@pytest.fixture(autouse=True, scope="module")
def hard_link(static_file_directory):
    src = os.path.abspath(
        os.path.join(os.path.dirname(static_file_directory), "conftest.py")
    )
    hard_link = "hard_link"
    dist = os.path.join(static_file_directory, hard_link)
    os.link(src, dist)
    yield hard_link
    os.remove(dist)


@pytest.mark.parametrize(
    "file_name",
    ["test.file", "decode me.txt", "python.png", "symlink", "hard_link"],
)
def test_static_file(app, static_file_directory, file_name):
    app.static(
        "/testing.file", get_file_path(static_file_directory, file_name)
    )

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize(
    "file_name",
    ["test.file", "decode me.txt", "python.png", "symlink", "hard_link"],
)
def test_static_file_pathlib(app, static_file_directory, file_name):
    file_path = Path(get_file_path(static_file_directory, file_name))
    app.static("/testing.file", file_path)
    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize(
    "file_name",
    [b"test.file", b"decode me.txt", b"python.png"],
)
def test_static_file_bytes(app, static_file_directory, file_name):
    bsep = os.path.sep.encode("utf-8")
    file_path = static_file_directory.encode("utf-8") + bsep + file_name
    app.static("/testing.file", file_path)
    request, response = app.test_client.get("/testing.file")
    assert response.status == 200


@pytest.mark.parametrize(
    "file_name",
    [{}, [], object()],
)
def test_static_file_invalid_path(app, static_file_directory, file_name):
    app.route("/")(lambda x: x)
    with pytest.raises(ValueError):
        app.static("/testing.file", file_name)
    request, response = app.test_client.get("/testing.file")
    assert response.status == 404


@pytest.mark.parametrize("file_name", ["test.html"])
def test_static_file_content_type(app, static_file_directory, file_name):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        content_type="text/html; charset=utf-8",
    )

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("test.html", "text/html; charset=utf-8"),
        ("decode me.txt", "text/plain; charset=utf-8"),
        ("test.file", "application/octet-stream"),
    ],
)
def test_static_file_content_type_guessed(
    app, static_file_directory, file_name, expected
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
    )

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert response.headers["Content-Type"] == expected


def test_static_file_content_type_with_charset(app, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, "decode me.txt"),
        content_type="text/plain;charset=ISO-8859-1",
    )

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert response.headers["Content-Type"] == "text/plain;charset=ISO-8859-1"


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "symlink", "hard_link"]
)
@pytest.mark.parametrize("base_uri", ["/static", "", "/dir"])
def test_static_directory(app, file_name, base_uri, static_file_directory):
    app.static(base_uri, static_file_directory)

    request, response = app.test_client.get(uri=f"{base_uri}/{file_name}")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_head_request(app, file_name, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    request, response = app.test_client.head("/testing.file")
    assert response.status == 200
    assert "Accept-Ranges" in response.headers
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_correct(app, file_name, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    headers = {"Range": "bytes=12-19"}
    request, response = app.test_client.get("/testing.file", headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:20
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_front(app, file_name, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    headers = {"Range": "bytes=12-"}
    request, response = app.test_client.get("/testing.file", headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_back(app, file_name, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    headers = {"Range": "bytes=-12"}
    request, response = app.test_client.get("/testing.file", headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        -12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("use_modified_since", [True, False])
@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_empty(
    app, file_name, static_file_directory, use_modified_since
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
        use_modified_since=use_modified_since,
    )

    request, response = app.test_client.get("/testing.file")
    assert response.status == 200
    assert "Content-Length" in response.headers
    assert "Content-Range" not in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )
    assert response.body == bytes(
        get_file_content(static_file_directory, file_name)
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_error(app, file_name, static_file_directory):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    headers = {"Range": "bytes=1-0"}
    request, response = app.test_client.get("/testing.file", headers=headers)
    assert response.status == 416
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "bytes */%s" % (
        len(get_file_content(static_file_directory, file_name)),
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_invalid_unit(
    app, file_name, static_file_directory
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    unit = "bit"
    headers = {"Range": f"{unit}=1-0"}
    request, response = app.test_client.get("/testing.file", headers=headers)

    assert response.status == 416
    assert f"{unit} is not a valid Range Type" in response.text


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_invalid_start(
    app, file_name, static_file_directory
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    start = "start"
    headers = {"Range": f"bytes={start}-0"}
    request, response = app.test_client.get("/testing.file", headers=headers)

    assert response.status == 416
    assert f"'{start}' is invalid for Content Range" in response.text


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_invalid_end(
    app, file_name, static_file_directory
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    end = "end"
    headers = {"Range": f"bytes=1-{end}"}
    request, response = app.test_client.get("/testing.file", headers=headers)

    assert response.status == 416
    assert f"'{end}' is invalid for Content Range" in response.text


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_invalid_parameters(
    app, file_name, static_file_directory
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    headers = {"Range": "bytes=-"}
    request, response = app.test_client.get("/testing.file", headers=headers)

    assert response.status == 416
    assert "Invalid for Content Range parameters" in response.text


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "python.png"]
)
def test_static_file_specified_host(app, static_file_directory, file_name):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        host="www.example.com",
    )

    headers = {"Host": "www.example.com"}
    request, response = app.test_client.get("/testing.file", headers=headers)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    request, response = app.test_client.get("/testing.file")
    assert response.status == 404


@pytest.mark.parametrize("use_modified_since", [True, False])
@pytest.mark.parametrize("stream_large_files", [True, 1024])
@pytest.mark.parametrize("file_name", ["test.file", "large.file"])
def test_static_stream_large_file(
    app,
    static_file_directory,
    file_name,
    use_modified_since,
    stream_large_files,
    large_file,
):
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_modified_since=use_modified_since,
        stream_large_files=stream_large_files,
    )

    request, response = app.test_client.get("/testing.file")

    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "python.png"]
)
def test_use_modified_since(app, static_file_directory, file_name):

    file_stat = os.stat(get_file_path(static_file_directory, file_name))
    modified_since = strftime(
        "%a, %d %b %Y %H:%M:%S GMT", gmtime(file_stat.st_mtime)
    )

    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_modified_since=True,
    )

    request, response = app.test_client.get(
        "/testing.file", headers={"If-Modified-Since": modified_since}
    )

    assert response.status == 304


def test_file_not_found(app, static_file_directory):
    app.static("/static", static_file_directory)

    request, response = app.test_client.get("/static/not_found")

    assert response.status == 404
    assert "File not found" in response.text


@pytest.mark.parametrize("static_name", ["_static_name", "static"])
@pytest.mark.parametrize("file_name", ["test.html"])
def test_static_name(app, static_file_directory, static_name, file_name):
    app.static("/static", static_file_directory, name=static_name)

    request, response = app.test_client.get(f"/static/{file_name}")

    assert response.status == 200


def test_nested_dir(app, static_file_directory):
    app.static("/static", static_file_directory)

    request, response = app.test_client.get("/static/nested/dir/foo.txt")

    assert response.status == 200
    assert response.text == "foo\n"


def test_handle_is_a_directory_error(app, static_file_directory):
    error_text = "Is a directory. Access denied"
    app.static("/static", static_file_directory)

    @app.exception(Exception)
    async def handleStaticDirError(request, exception):
        if isinstance(exception, IsADirectoryError):
            return text(error_text, status=403)
        raise exception

    request, response = app.test_client.get("/static/")

    assert response.status == 403
    assert response.text == error_text


def test_stack_trace_on_not_found(app, static_file_directory, caplog):
    app.static("/static", static_file_directory)

    with caplog.at_level(logging.INFO):
        _, response = app.test_client.get("/static/non_existing_file.file")

    counter = Counter([(r[0], r[1]) for r in caplog.record_tuples])

    assert response.status == 404
    assert counter[("sanic.root", logging.INFO)] == 9
    assert counter[("sanic.root", logging.ERROR)] == 0
    assert counter[("sanic.error", logging.ERROR)] == 0
    assert counter[("sanic.server", logging.INFO)] == 2


def test_no_stack_trace_on_not_found(app, static_file_directory, caplog):
    app.static("/static", static_file_directory)

    @app.exception(FileNotFound)
    async def file_not_found(request, exception):
        return text(f"No file: {request.path}", status=404)

    with caplog.at_level(logging.INFO):
        _, response = app.test_client.get("/static/non_existing_file.file")

    counter = Counter([(r[0], r[1]) for r in caplog.record_tuples])

    assert response.status == 404
    assert counter[("sanic.root", logging.INFO)] == 9
    assert counter[("sanic.root", logging.ERROR)] == 0
    assert counter[("sanic.error", logging.ERROR)] == 0
    assert counter[("sanic.server", logging.INFO)] == 2
    assert response.text == "No file: /static/non_existing_file.file"


def test_multiple_statics(app, static_file_directory):
    app.static("/file", get_file_path(static_file_directory, "test.file"))
    app.static("/png", get_file_path(static_file_directory, "python.png"))

    _, response = app.test_client.get("/file")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.file"
    )

    _, response = app.test_client.get("/png")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "python.png"
    )


def test_resource_type_default(app, static_file_directory):
    app.static("/static", static_file_directory)
    app.static("/file", get_file_path(static_file_directory, "test.file"))

    _, response = app.test_client.get("/static")
    assert response.status == 404

    _, response = app.test_client.get("/file")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.file"
    )


def test_resource_type_file(app, static_file_directory):
    app.static(
        "/file",
        get_file_path(static_file_directory, "test.file"),
        resource_type="file",
    )

    _, response = app.test_client.get("/file")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.file"
    )

    with pytest.raises(TypeError):
        app.static("/static", static_file_directory, resource_type="file")


def test_resource_type_dir(app, static_file_directory):
    app.static("/static", static_file_directory, resource_type="dir")

    _, response = app.test_client.get("/static/test.file")
    assert response.status == 200
    assert response.body == get_file_content(
        static_file_directory, "test.file"
    )

    with pytest.raises(TypeError):
        app.static(
            "/file",
            get_file_path(static_file_directory, "test.file"),
            resource_type="dir",
        )


def test_resource_type_unknown(app, static_file_directory, caplog):
    with pytest.raises(ValueError):
        app.static("/static", static_file_directory, resource_type="unknown")


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows does not support double dotted directories",
)
def test_dotted_dir_ok(
    app: Sanic, static_file_directory: str, double_dotted_directory_file: Path
):
    app.static("/foo", static_file_directory)
    dot_relative_path = str(
        double_dotted_directory_file.relative_to(static_file_directory)
    )
    _, response = app.test_client.get("/foo/" + dot_relative_path)
    assert response.status == 200
    assert response.body == b"DOT\n"


def test_breakout(app: Sanic, static_file_directory: str):
    app.static("/foo", static_file_directory)

    _, response = app.test_client.get("/foo/..%2Ffake/server.py")
    assert response.status == 404

    _, response = app.test_client.get("/foo/..%2Fstatic/test.file")
    assert response.status == 404


@pytest.mark.skipif(
    sys.platform != "win32", reason="Block backslash on Windows only"
)
def test_double_backslash_prohibited_on_win32(
    app: Sanic, static_file_directory: str
):
    app.static("/foo", static_file_directory)

    _, response = app.test_client.get("/foo/static/..\\static/test.file")
    assert response.status == 404
    _, response = app.test_client.get("/foo/static\\../static/test.file")
    assert response.status == 404
