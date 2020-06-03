import string

from urllib.parse import parse_qsl, urlsplit

import pytest as pytest

from sanic.blueprints import Blueprint
from sanic.exceptions import URLBuildError
from sanic.response import text
from sanic.testing import HOST as test_host
from sanic.testing import PORT as test_port
from sanic.views import HTTPMethodView


URL_FOR_ARGS1 = dict(arg1=["v1", "v2"])
URL_FOR_VALUE1 = "/myurl?arg1=v1&arg1=v2"
URL_FOR_ARGS2 = dict(arg1=["v1", "v2"], _anchor="anchor")
URL_FOR_VALUE2 = "/myurl?arg1=v1&arg1=v2#anchor"
URL_FOR_ARGS3 = dict(
    arg1="v1",
    _anchor="anchor",
    _scheme="http",
    _server=f"{test_host}:{test_port}",
    _external=True,
)
URL_FOR_VALUE3 = f"http://{test_host}:{test_port}/myurl?arg1=v1#anchor"
URL_FOR_ARGS4 = dict(
    arg1="v1",
    _anchor="anchor",
    _external=True,
    _server=f"http://{test_host}:{test_port}",
)
URL_FOR_VALUE4 = f"http://{test_host}:{test_port}/myurl?arg1=v1#anchor"


def _generate_handlers_from_names(app, l):
    for name in l:
        # this is the easiest way to generate functions with dynamic names
        exec(
            f'@app.route(name)\ndef {name}(request):\n\treturn text("{name}")'
        )


@pytest.fixture
def simple_app(app):
    handler_names = list(string.ascii_letters)

    _generate_handlers_from_names(app, handler_names)

    return app


def test_simple_url_for_getting(simple_app):
    for letter in string.ascii_letters:
        url = simple_app.url_for(letter)

        assert url == f"/{letter}"
        request, response = simple_app.test_client.get(url)
        assert response.status == 200
        assert response.text == letter


@pytest.mark.parametrize(
    "args,url",
    [
        (URL_FOR_ARGS1, URL_FOR_VALUE1),
        (URL_FOR_ARGS2, URL_FOR_VALUE2),
        (URL_FOR_ARGS3, URL_FOR_VALUE3),
        (URL_FOR_ARGS4, URL_FOR_VALUE4),
    ],
)
def test_simple_url_for_getting_with_more_params(app, args, url):
    @app.route("/myurl")
    def passes(request):
        return text("this should pass")

    assert url == app.url_for("passes", **args)
    request, response = app.test_client.get(url)
    assert response.status == 200
    assert response.text == "this should pass"


def test_url_for_with_server_name(app):

    server_name = f"{test_host}:{test_port}"
    app.config.update({"SERVER_NAME": server_name})
    path = "/myurl"

    @app.route(path)
    def passes(request):
        return text("this should pass")

    url = f"http://{server_name}{path}"
    assert url == app.url_for("passes", _server=None, _external=True)
    request, response = app.test_client.get(url)
    assert response.status == 200
    assert response.text == "this should pass"


def test_fails_if_endpoint_not_found(app):
    @app.route("/fail")
    def fail(request):
        return text("this should fail")

    with pytest.raises(URLBuildError) as e:
        app.url_for("passes")

    assert str(e.value) == "Endpoint with name `passes` was not found"


def test_fails_url_build_if_param_not_passed(app):
    url = "/"

    for letter in string.ascii_letters:
        url += f"<{letter}>/"

    @app.route(url)
    def fail(request):
        return text("this should fail")

    fail_args = list(string.ascii_letters)
    fail_args.pop()

    fail_kwargs = {l: l for l in fail_args}

    with pytest.raises(URLBuildError) as e:
        app.url_for("fail", **fail_kwargs)

    assert "Required parameter `Z` was not passed to url_for" in str(e.value)


def test_fails_url_build_if_params_not_passed(app):
    @app.route("/fail")
    def fail(request):
        return text("this should fail")

    with pytest.raises(ValueError) as e:
        app.url_for("fail", _scheme="http")

    assert str(e.value) == "When specifying _scheme, _external must be True"


COMPLEX_PARAM_URL = (
    "/<foo:int>/<four_letter_string:[A-z]{4}>/"
    "<two_letter_string:[A-z]{2}>/<normal_string>/<some_number:number>"
)
PASSING_KWARGS = {
    "foo": 4,
    "four_letter_string": "woof",
    "two_letter_string": "ba",
    "normal_string": "normal",
    "some_number": "1.001",
}
EXPECTED_BUILT_URL = "/4/woof/ba/normal/1.001"


def test_fails_with_int_message(app):
    @app.route(COMPLEX_PARAM_URL)
    def fail(request):
        return text("this should fail")

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs["foo"] = "not_int"

    with pytest.raises(URLBuildError) as e:
        app.url_for("fail", **failing_kwargs)

    expected_error = (
        r'Value "not_int" for parameter `foo` '
        r"does not match pattern for type `int`: -?\d+"
    )
    assert str(e.value) == expected_error


def test_passes_with_negative_int_message(app):
    @app.route("path/<possibly_neg:int>/another-word")
    def good(request, possibly_neg):
        assert isinstance(possibly_neg, int)
        return text(f"this should pass with `{possibly_neg}`")

    u_plus_3 = app.url_for("good", possibly_neg=3)
    assert u_plus_3 == "/path/3/another-word", u_plus_3
    request, response = app.test_client.get(u_plus_3)
    assert response.text == "this should pass with `3`"
    u_neg_3 = app.url_for("good", possibly_neg=-3)
    assert u_neg_3 == "/path/-3/another-word", u_neg_3
    request, response = app.test_client.get(u_neg_3)
    assert response.text == "this should pass with `-3`"


def test_fails_with_two_letter_string_message(app):
    @app.route(COMPLEX_PARAM_URL)
    def fail(request):
        return text("this should fail")

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs["two_letter_string"] = "foobar"

    with pytest.raises(URLBuildError) as e:
        app.url_for("fail", **failing_kwargs)

    expected_error = (
        'Value "foobar" for parameter `two_letter_string` '
        "does not satisfy pattern [A-z]{2}"
    )

    assert str(e.value) == expected_error


def test_fails_with_number_message(app):
    @app.route(COMPLEX_PARAM_URL)
    def fail(request):
        return text("this should fail")

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs["some_number"] = "foo"

    with pytest.raises(URLBuildError) as e:
        app.url_for("fail", **failing_kwargs)

    expected_error = (
        'Value "foo" for parameter `some_number` '
        r"does not match pattern for type `float`: -?(?:\d+(?:\.\d*)?|\.\d+)"
    )

    assert str(e.value) == expected_error


@pytest.mark.parametrize("number", [3, -3, 13.123, -13.123])
def test_passes_with_negative_number_message(app, number):
    @app.route("path/<possibly_neg:number>/another-word")
    def good(request, possibly_neg):
        assert isinstance(possibly_neg, (int, float))
        return text(f"this should pass with `{possibly_neg}`")

    u = app.url_for("good", possibly_neg=number)
    assert u == f"/path/{number}/another-word", u
    request, response = app.test_client.get(u)
    # For ``number``, it has been cast to a float - so a ``3`` becomes a ``3.0``
    assert response.text == f"this should pass with `{float(number)}`"


def test_adds_other_supplied_values_as_query_string(app):
    @app.route(COMPLEX_PARAM_URL)
    def passes(request):
        return text("this should pass")

    new_kwargs = dict(PASSING_KWARGS)
    new_kwargs["added_value_one"] = "one"
    new_kwargs["added_value_two"] = "two"

    url = app.url_for("passes", **new_kwargs)

    query = dict(parse_qsl(urlsplit(url).query))

    assert query["added_value_one"] == "one"
    assert query["added_value_two"] == "two"


@pytest.fixture
def blueprint_app(app):

    first_print = Blueprint("first", url_prefix="/first")
    second_print = Blueprint("second", url_prefix="/second")

    @first_print.route("/foo")
    def foo(request):
        return text("foo from first")

    @first_print.route("/foo/<param>")
    def foo_with_param(request, param):
        return text(f"foo from first : {param}")

    @second_print.route("/foo")  # noqa
    def foo(request):
        return text("foo from second")

    @second_print.route("/foo/<param>")  # noqa
    def foo_with_param(request, param):
        return text(f"foo from second : {param}")

    app.blueprint(first_print)
    app.blueprint(second_print)

    return app


def test_blueprints_are_named_correctly(blueprint_app):
    first_url = blueprint_app.url_for("first.foo")
    assert first_url == "/first/foo"

    second_url = blueprint_app.url_for("second.foo")
    assert second_url == "/second/foo"


def test_blueprints_work_with_params(blueprint_app):
    first_url = blueprint_app.url_for("first.foo_with_param", param="bar")
    assert first_url == "/first/foo/bar"

    second_url = blueprint_app.url_for("second.foo_with_param", param="bar")
    assert second_url == "/second/foo/bar"


@pytest.fixture
def methodview_app(app):
    class ViewOne(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

        def post(self, request):
            return text("I am post method")

        def put(self, request):
            return text("I am put method")

        def patch(self, request):
            return text("I am patch method")

        def delete(self, request):
            return text("I am delete method")

    app.add_route(ViewOne.as_view("view_one"), "/view_one")

    class ViewTwo(HTTPMethodView):
        def get(self, request):
            return text("I am get method")

        def post(self, request):
            return text("I am post method")

        def put(self, request):
            return text("I am put method")

        def patch(self, request):
            return text("I am patch method")

        def delete(self, request):
            return text("I am delete method")

    app.add_route(ViewTwo.as_view(), "/view_two")

    return app


def test_methodview_naming(methodview_app):
    viewone_url = methodview_app.url_for("ViewOne")
    viewtwo_url = methodview_app.url_for("ViewTwo")

    assert viewone_url == "/view_one"
    assert viewtwo_url == "/view_two"
