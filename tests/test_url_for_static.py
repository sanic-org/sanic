import inspect
import os

import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint


@pytest.fixture(scope="module")
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, "static")
    return static_directory


def get_file_path(static_file_directory, file_name):
    return os.path.join(static_file_directory, file_name)


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(get_file_path(static_file_directory, file_name), "rb") as file:
        return file.read()


@pytest.mark.parametrize(
    "file_name",
    [
        "test.file",
        "decode me.txt",
        "python.png",
    ],
)
def test_static_file(static_file_directory, file_name):
    app = Sanic("qq")
    app.static(
        "/testing.file", get_file_path(static_file_directory, file_name)
    )
    app.static(
        "/testing2.file",
        get_file_path(static_file_directory, file_name),
        name="testing_file",
    )

    app.router.finalize()

    uri = app.url_for("static")
    uri2 = app.url_for("static", filename="any")
    uri3 = app.url_for("static", name="static", filename="any")

    assert uri == "/testing.file"
    assert uri == uri2
    assert uri2 == uri3

    app.router.reset()

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)

    app.router.reset()

    bp = Blueprint("test_bp_static", url_prefix="/bp")

    bp.static("/testing.file", get_file_path(static_file_directory, file_name))
    bp.static(
        "/testing2.file",
        get_file_path(static_file_directory, file_name),
        name="testing_file",
    )

    app.blueprint(bp)

    uris = [
        app.url_for("static", name="test_bp_static.static"),
        app.url_for("static", name="test_bp_static.static", filename="any"),
        app.url_for("test_bp_static.static"),
        app.url_for("test_bp_static.static", filename="any"),
    ]

    assert all(uri == "/bp/testing.file" for uri in uris)

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)

    # test for other parameters
    uri = app.url_for("static", _external=True, _server="http://localhost")
    assert uri == "http://localhost/testing.file"

    uri = app.url_for(
        "static",
        name="test_bp_static.static",
        _external=True,
        _server="http://localhost",
    )
    assert uri == "http://localhost/bp/testing.file"

    # test for defined name
    uri = app.url_for("static", name="testing_file")
    assert uri == "/testing2.file"

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)

    uri = app.url_for("static", name="test_bp_static.testing_file")
    assert uri == "/bp/testing2.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.testing_file", filename="any"
    )

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
@pytest.mark.parametrize("base_uri", ["/static", "", "/dir"])
def test_static_directory(file_name, base_uri, static_file_directory):
    app = Sanic("base")

    app.static(base_uri, static_file_directory)
    base_uri2 = base_uri + "/2"
    app.static(base_uri2, static_file_directory, name="uploads")

    uri = app.url_for("static", name="static", filename=file_name)
    assert uri == f"{base_uri}/{file_name}"

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)

    uri2 = app.url_for("static", name="static", filename="/" + file_name)
    uri3 = app.url_for("static", filename=file_name)
    uri4 = app.url_for("static", filename="/" + file_name)
    uri5 = app.url_for("static", name="uploads", filename=file_name)
    uri6 = app.url_for("static", name="uploads", filename="/" + file_name)

    assert uri == uri2
    assert uri2 == uri3
    assert uri3 == uri4

    assert uri5 == f"{base_uri2}/{file_name}"
    assert uri5 == uri6

    bp = Blueprint("test_bp_static", url_prefix="/bp")

    bp.static(base_uri, static_file_directory)
    bp.static(base_uri2, static_file_directory, name="uploads")

    app.router.reset()
    app.blueprint(bp)

    uri = app.url_for(
        "static", name="test_bp_static.static", filename=file_name
    )
    uri2 = app.url_for(
        "static", name="test_bp_static.static", filename="/" + file_name
    )

    uri4 = app.url_for(
        "static", name="test_bp_static.uploads", filename=file_name
    )
    uri5 = app.url_for(
        "static", name="test_bp_static.uploads", filename="/" + file_name
    )

    assert uri == f"/bp{base_uri}/{file_name}"
    assert uri == uri2

    assert uri4 == f"/bp{base_uri2}/{file_name}"
    assert uri4 == uri5

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_head_request(file_name, static_file_directory):
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.head(uri)
    assert response.status == 200
    assert "Accept-Ranges" in response.headers
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )

    request, response = app.test_client.head(uri)
    assert response.status == 200
    assert "Accept-Ranges" in response.headers
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_correct(file_name, static_file_directory):
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    headers = {"Range": "bytes=12-19"}
    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:20
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )
    assert uri == app.url_for("test_bp_static.static")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:20
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_front(file_name, static_file_directory):
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    headers = {"Range": "bytes=12-"}
    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )
    assert uri == app.url_for("test_bp_static.static")
    assert uri == app.url_for("test_bp_static.static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_back(file_name, static_file_directory):
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    headers = {"Range": "bytes=-12"}
    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        -12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )
    assert uri == app.url_for("test_bp_static.static")
    assert uri == app.url_for("test_bp_static.static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 206
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    static_content = bytes(get_file_content(static_file_directory, file_name))[
        -12:
    ]
    assert int(response.headers["Content-Length"]) == len(static_content)
    assert response.body == static_content


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_static_content_range_empty(file_name, static_file_directory):
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.get(uri)
    assert response.status == 200
    assert "Content-Length" in response.headers
    assert "Content-Range" not in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )
    assert response.body == bytes(
        get_file_content(static_file_directory, file_name)
    )

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )
    assert uri == app.url_for("test_bp_static.static")
    assert uri == app.url_for("test_bp_static.static", filename="any")

    request, response = app.test_client.get(uri)
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
    app = Sanic("base")
    app.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )

    bp = Blueprint("test_bp_static", url_prefix="/bp")
    bp.static(
        "/testing.file",
        get_file_path(static_file_directory, file_name),
        use_content_range=True,
    )
    app.blueprint(bp)

    headers = {"Range": "bytes=1-0"}
    uri = app.url_for("static")
    assert uri == "/testing.file"
    assert uri == app.url_for("static", name="static")
    assert uri == app.url_for("static", name="static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 416
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "bytes */%s" % (
        len(get_file_content(static_file_directory, file_name)),
    )

    # blueprint
    uri = app.url_for("static", name="test_bp_static.static")
    assert uri == "/bp/testing.file"
    assert uri == app.url_for(
        "static", name="test_bp_static.static", filename="any"
    )
    assert uri == app.url_for("test_bp_static.static")
    assert uri == app.url_for("test_bp_static.static", filename="any")

    request, response = app.test_client.get(uri, headers=headers)
    assert response.status == 416
    assert "Content-Length" in response.headers
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "bytes */%s" % (
        len(get_file_content(static_file_directory, file_name)),
    )
