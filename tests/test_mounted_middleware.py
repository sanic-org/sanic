from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.request import Request
from sanic.response import json, text, HTTPResponse
from sanic.exceptions import MiddlewareTypeError


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_mounted_request_middleware():
    app = Sanic("test_mounted_request_middleware")

    results = []
    
    async def request_middleware(request):
        results.append(request)

    @app.route('/', middleware={"request": request_middleware})
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get('/')
    
    assert response.text == "OK"
    assert type(results[0]) is Request

def test_early_response_from_mounted_request_middleware():
    app = Sanic("test_early_response_from_mounted_request_middleware")

    results = []

    async def early_request_middleware(request):
        results.append(1)
        return text("response from early_request_middleware")

    @app.route('/', middleware={"request": early_request_middleware})
    async def handler(request):
        results.append(2)
        return text("response from handler")

    request, response = app.test_client.get('/')

    assert response.text == "response from early_request_middleware"
    assert results[0] == 1
    assert len(results) == 1

def test_multi_mounted_request_middleware():
    app = Sanic("test_multi_mounted_request_middleware")

    results = []
    added = ['ADD1', 'aADD1', 'ADD2', 'aADD2']

    def mounted_request_middleware1(request):
        results.append(added[0])
    
    async def mounted_async_request_middleware1(request):
        results.append(added[1])

    def mounted_request_middleware2(request):
        results.append(added[2])
    
    async def mounted_async_request_middleware2(request):
        results.append(added[3])
    
    middlewares = (
        mounted_request_middleware1,
        mounted_async_request_middleware1,
        mounted_request_middleware2,
        mounted_async_request_middleware2
    )

    @app.route('/', middleware={"request": middlewares})
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get('/')

    for i, v in enumerate(added):
        assert results[i] == added[i]

    assert response.text == "OK"

def test_mounted_request_middleware_parameter():
    app = Sanic("test_mounted_request_middleware_parameter")

    results = []
    async def request_middleware(request, id):
        results.append(id)

    @app.route('/<id>', middleware={"request": request_middleware})
    def handler(request, id):
        return text("OK")

    request, response = app.test_client.get('/42')

    assert results[0] == str(42)
    assert response.text == "OK"
    


def test_mounted_response_middleware():
    app = Sanic("test_mounted_response_middleware")

    results = []

    async def response_middleware(request, response):
        results.append(42)

    @app.route('/', middleware={"response": response_middleware})
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get('/')

    assert results[0] == 42


def test_early_response_from_mounted_response_middleware():
    app = Sanic("test_early_response_from_mounted_response_middleware")

    results = []
    added = ['hADD1', 'mADD2', 'eADD3', 'nADD4']

    def response_middleware(request, response):
        results.append(added[1])

    async def early_response_middleware(request, response):
        results.append(added[2])
        response.headers.update({"Added": "Response Middleware"})
        return response
    
    def not_called_response_middleware(requst, response):
        results.append(added[3])

    middlewares = [
        response_middleware,
        early_response_middleware,
        not_called_response_middleware
    ]

    @app.route('/', middleware={"response": middlewares})
    def handler(request):
        results.append(added[0])        
        return text('handlerOK')

    request, response = app.test_client.get('/')

    for i,v in enumerate(added):
        if i != 3:
            assert results[i] == added[i]

    assert len(results) == 3
    assert response.headers["Added"]== "Response Middleware"

def test_mounted_response_middleware_parameter():
    app = Sanic("test_mounted_response_middleware_parameter")

    results = []

    async def response_middleware(request, response, id):
        results.append(id)

    @app.route('/<id>', middleware={"response": response_middleware})
    async def handler(request, id):
        return text("OK")

    request, response = app.test_client.get('/42')

    assert results[0] == str(42)
    assert response.text == "OK"
    

def test_exception():
    app = Sanic("test_exception")

    wrong_request = 123

    try:
        @app.route('/', middleware={"request": wrong_request})
        async def handler1(request):
            return text("BAD")
    except MiddlewareTypeError as ex:
        assert str(ex) == "Middleware mounted on a handler should be a function or a sequence of functions"

