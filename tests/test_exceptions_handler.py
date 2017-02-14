from sanic import Sanic
from sanic.response import text
from sanic.exceptions import InvalidUsage, ServerError, NotFound
from bs4 import BeautifulSoup

exception_handler_app = Sanic('test_exception_handler')


@exception_handler_app.route('/1')
def handler_1(request):
    raise InvalidUsage("OK")


@exception_handler_app.route('/2')
def handler_2(request):
    raise ServerError("OK")


@exception_handler_app.route('/3')
def handler_3(request):
    raise NotFound("OK")


@exception_handler_app.route('/4')
def handler_4(request):
    foo = bar
    return text(foo)


@exception_handler_app.route('/5')
def handler_5(request):
    class CustomServerError(ServerError):
        status_code=200
    raise CustomServerError('Custom server error')


@exception_handler_app.exception(NotFound, ServerError)
def handler_exception(request, exception):
    return text("OK")


def test_invalid_usage_exception_handler():
    request, response = exception_handler_app.test_client.get('/1')
    assert response.status == 400


def test_server_error_exception_handler():
    request, response = exception_handler_app.test_client.get('/2')
    assert response.status == 200
    assert response.text == 'OK'


def test_not_found_exception_handler():
    request, response = exception_handler_app.test_client.get('/3')
    assert response.status == 200


def test_text_exception__handler():
    request, response = exception_handler_app.test_client.get('/random')
    assert response.status == 200
    assert response.text == 'OK'


def test_html_traceback_output_in_debug_mode():
    request, response = exception_handler_app.test_client.get(
        '/4', debug=True)
    assert response.status == 500
    soup = BeautifulSoup(response.body, 'html.parser')
    html = str(soup)

    assert 'response = handler(request, *args, **kwargs)' in html
    assert 'handler_4' in html
    assert 'foo = bar' in html

    summary_text = " ".join(soup.select('.summary')[0].text.split())
    assert (
        "NameError: name 'bar' "
        "is not defined while handling uri /4") == summary_text


def test_inherited_exception_handler():
    request, response = exception_handler_app.test_client.get('/5')
    assert response.status == 200
