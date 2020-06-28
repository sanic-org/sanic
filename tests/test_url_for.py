def test_routes_with_host(app):
    @app.route("/")
    @app.route("/", name="hostindex", host="example.com")
    @app.route("/path", name="hostpath", host="path.example.com")
    def index(request):
        pass

    assert app.url_for("index") == "/"
    assert app.url_for("hostindex") == "/"
    assert app.url_for("hostpath") == "/path"
    assert app.url_for("hostindex", _external=True) == "http://example.com/"
    assert (
        app.url_for("hostpath", _external=True)
        == "http://path.example.com/path"
    )
