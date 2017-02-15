from random import choice

from sanic import Sanic
from sanic.response import HTTPResponse


def test_response_body_not_a_string():
    """Test when a response body sent from the application is not a string"""
    app = Sanic('response_body_not_a_string')
    random_num = choice(range(1000))

    @app.route('/hello')
    async def hello_route(request):
        return HTTPResponse(body=random_num)

    request, response = app.test_client.get('/hello')
    assert response.text == str(random_num)
