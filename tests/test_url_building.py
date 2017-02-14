import pytest as pytest
from urllib.parse import urlsplit, parse_qsl

from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView
from sanic.blueprints import Blueprint
from sanic.testing import PORT as test_port
from sanic.exceptions import URLBuildError

import string

URL_FOR_ARGS1 = dict(arg1=['v1', 'v2'])
URL_FOR_VALUE1 = '/myurl?arg1=v1&arg1=v2'
URL_FOR_ARGS2 = dict(arg1=['v1', 'v2'], _anchor='anchor')
URL_FOR_VALUE2 = '/myurl?arg1=v1&arg1=v2#anchor'
URL_FOR_ARGS3 = dict(arg1='v1', _anchor='anchor', _scheme='http',
                     _server='localhost:{}'.format(test_port), _external=True)
URL_FOR_VALUE3 = 'http://localhost:{}/myurl?arg1=v1#anchor'.format(test_port)


def _generate_handlers_from_names(app, l):
    for name in l:
        # this is the easiest way to generate functions with dynamic names
        exec('@app.route(name)\ndef {}(request):\n\treturn text("{}")'.format(
            name, name))


@pytest.fixture
def simple_app():
    app = Sanic('simple_app')
    handler_names = list(string.ascii_letters)

    _generate_handlers_from_names(app, handler_names)

    return app


def test_simple_url_for_getting(simple_app):
    for letter in string.ascii_letters:
        url = simple_app.url_for(letter)

        assert url == '/{}'.format(letter)
        request, response = simple_app.test_client.get(url)
        assert response.status == 200
        assert response.text == letter


@pytest.mark.parametrize('args,url',
                         [(URL_FOR_ARGS1, URL_FOR_VALUE1),
                          (URL_FOR_ARGS2, URL_FOR_VALUE2),
                          (URL_FOR_ARGS3, URL_FOR_VALUE3)])
def test_simple_url_for_getting_with_more_params(args, url):
    app = Sanic('more_url_build')

    @app.route('/myurl')
    def passes(request):
        return text('this should pass')

    assert url == app.url_for('passes', **args)
    request, response = app.test_client.get(url)
    assert response.status == 200
    assert response.text == 'this should pass'


def test_fails_if_endpoint_not_found():
    app = Sanic('fail_url_build')

    @app.route('/fail')
    def fail():
        return text('this should fail')

    with pytest.raises(URLBuildError) as e:
        app.url_for('passes')

    assert str(e.value) == 'Endpoint with name `passes` was not found'


def test_fails_url_build_if_param_not_passed():
    url = '/'

    for letter in string.ascii_letters:
        url += '<{}>/'.format(letter)

    app = Sanic('fail_url_build')

    @app.route(url)
    def fail():
        return text('this should fail')

    fail_args = list(string.ascii_letters)
    fail_args.pop()

    fail_kwargs = {l: l for l in fail_args}

    with pytest.raises(URLBuildError) as e:
        app.url_for('fail', **fail_kwargs)

    assert 'Required parameter `Z` was not passed to url_for' in str(e.value)


def test_fails_url_build_if_params_not_passed():
    app = Sanic('fail_url_build')

    @app.route('/fail')
    def fail():
        return text('this should fail')

    with pytest.raises(ValueError) as e:
        app.url_for('fail', _scheme='http')

    assert str(e.value) == 'When specifying _scheme, _external must be True'


COMPLEX_PARAM_URL = (
    '/<foo:int>/<four_letter_string:[A-z]{4}>/'
    '<two_letter_string:[A-z]{2}>/<normal_string>/<some_number:number>')
PASSING_KWARGS = {
    'foo': 4, 'four_letter_string': 'woof',
    'two_letter_string': 'ba', 'normal_string': 'normal',
    'some_number': '1.001'}
EXPECTED_BUILT_URL = '/4/woof/ba/normal/1.001'


def test_fails_with_int_message():
    app = Sanic('fail_url_build')

    @app.route(COMPLEX_PARAM_URL)
    def fail():
        return text('this should fail')

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs['foo'] = 'not_int'

    with pytest.raises(URLBuildError) as e:
        app.url_for('fail', **failing_kwargs)

    expected_error = (
        'Value "not_int" for parameter `foo` '
        'does not match pattern for type `int`: \d+')
    assert str(e.value) == expected_error


def test_fails_with_two_letter_string_message():
    app = Sanic('fail_url_build')

    @app.route(COMPLEX_PARAM_URL)
    def fail():
        return text('this should fail')

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs['two_letter_string'] = 'foobar'

    with pytest.raises(URLBuildError) as e:
        app.url_for('fail', **failing_kwargs)

    expected_error = (
        'Value "foobar" for parameter `two_letter_string` '
        'does not satisfy pattern [A-z]{2}')

    assert str(e.value) == expected_error


def test_fails_with_number_message():
    app = Sanic('fail_url_build')

    @app.route(COMPLEX_PARAM_URL)
    def fail():
        return text('this should fail')

    failing_kwargs = dict(PASSING_KWARGS)
    failing_kwargs['some_number'] = 'foo'

    with pytest.raises(URLBuildError) as e:
        app.url_for('fail', **failing_kwargs)

    expected_error = (
        'Value "foo" for parameter `some_number` '
        'does not match pattern for type `float`: [0-9\\\\.]+')

    assert str(e.value) == expected_error


def test_adds_other_supplied_values_as_query_string():
    app = Sanic('passes')

    @app.route(COMPLEX_PARAM_URL)
    def passes():
        return text('this should pass')

    new_kwargs = dict(PASSING_KWARGS)
    new_kwargs['added_value_one'] = 'one'
    new_kwargs['added_value_two'] = 'two'

    url = app.url_for('passes', **new_kwargs)

    query = dict(parse_qsl(urlsplit(url).query))

    assert query['added_value_one'] == 'one'
    assert query['added_value_two'] == 'two'


@pytest.fixture
def blueprint_app():
    app = Sanic('blueprints')

    first_print = Blueprint('first', url_prefix='/first')
    second_print = Blueprint('second', url_prefix='/second')

    @first_print.route('/foo')
    def foo():
        return text('foo from first')

    @first_print.route('/foo/<param>')
    def foo_with_param(request, param):
        return text(
            'foo from first : {}'.format(param))

    @second_print.route('/foo')  # noqa
    def foo():
        return text('foo from second')

    @second_print.route('/foo/<param>')  # noqa
    def foo_with_param(request, param):
        return text(
            'foo from second : {}'.format(param))

    app.blueprint(first_print)
    app.blueprint(second_print)

    return app


def test_blueprints_are_named_correctly(blueprint_app):
    first_url = blueprint_app.url_for('first.foo')
    assert first_url == '/first/foo'

    second_url = blueprint_app.url_for('second.foo')
    assert second_url == '/second/foo'


def test_blueprints_work_with_params(blueprint_app):
    first_url = blueprint_app.url_for('first.foo_with_param', param='bar')
    assert first_url == '/first/foo/bar'

    second_url = blueprint_app.url_for('second.foo_with_param', param='bar')
    assert second_url == '/second/foo/bar'


@pytest.fixture
def methodview_app():
    app = Sanic('methodview')

    class ViewOne(HTTPMethodView):
        def get(self, request):
            return text('I am get method')

        def post(self, request):
            return text('I am post method')

        def put(self, request):
            return text('I am put method')

        def patch(self, request):
            return text('I am patch method')

        def delete(self, request):
            return text('I am delete method')

    app.add_route(ViewOne.as_view('view_one'), '/view_one')

    class ViewTwo(HTTPMethodView):
        def get(self, request):
            return text('I am get method')

        def post(self, request):
            return text('I am post method')

        def put(self, request):
            return text('I am put method')

        def patch(self, request):
            return text('I am patch method')

        def delete(self, request):
            return text('I am delete method')

    app.add_route(ViewTwo.as_view(), '/view_two')

    return app


def test_methodview_naming(methodview_app):
    viewone_url = methodview_app.url_for('ViewOne')
    viewtwo_url = methodview_app.url_for('ViewTwo')

    assert viewone_url == '/view_one'
    assert viewtwo_url == '/view_two'
