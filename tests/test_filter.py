from functools import wraps
from sanic import Sanic, Blueprint
from sanic.response import text


def test_sync_app_filter_over_sync_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')

    @app.get('/')
    def sync_index(request):
        return text('sync_index')

    @app.filter(sync_index)
    def sync_filter(handler, request):
        response = handler(request)
        response.body += b"_sync_filter"
        return response

    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_sync_filter'


def test_sync_app_filter_over_async_handler():
    app = Sanic('test_sync_app_filter_over_async_handler')

    @app.get('/async')
    async def async_index(request):
        return text('async_index')

    try:
        @app.filter(async_index)
        def sync_filter(handler, request):
            response = handler(request)
            response.body += b"_async_filter"
            return response
    except TypeError:
        pass
    else:
        raise Exception('This should not pass')


def test_async_app_filter_over_sync_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')

    @app.get('/')
    def sync_index(request):
        return text('sync_index')

    @app.filter(sync_index)
    async def async_filter(handler, request):
        # the handler should always be awaitable
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_async_filter'


def test_async_app_filter_over_async_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')

    @app.get('/')
    async def async_index(request):
        return text('async_index')

    @app.filter(async_index)
    async def async_filter(handler, request):
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    req, resp = app.test_client.get('/')
    assert resp.text == 'async_index_async_filter'


def test_async_app_filter_over_sync_app_filter_over_sync_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')

    @app.get('/')
    def sync_index(request):
        return text('sync_index')

    @app.filter(sync_index)
    def sync_filter(handler, request):
        response = handler(request)
        response.body += b"_sync_filter"
        return response

    @app.filter('sync_index')
    async def async_filter(handler, request):
        # the handler should always be awaitable
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_sync_filter_async_filter'


def test_handler_decorator():
    app = Sanic('test_sync_app_filter_over_sync_handler')

    def check_args(handler):
        @wraps(handler)
        async def new_handler(request):
            abc = request.args.get('abc', None)
            if abc is None:
                return text("wrong")
            return await handler(request)

        new_handler.abc = "abc"
        return new_handler

    def filter_decorator(handler_decorator):
        @wraps(handler_decorator)
        def new_decorator(filter_func):
            new_handler = None

            async def new_handler_filter(handler, *args, **kwargs):
                nonlocal new_handler
                if new_handler is None:
                    new_handler = handler_decorator(handler)
                return await filter_func(new_handler, *args, **kwargs)
            return new_handler_filter
        return new_decorator

    @app.get('/')
    def sync_index(request):
        return text('sync_index')

    @app.filter(sync_index)
    def sync_filter(handler, request):
        response = handler(request)
        response.body += b"_sync_filter"
        return response

    @app.get('/checked')  # add to others with change
    @check_args
    @app.filter('sync_index')
    async def async_filter(handler, request):
        # the handler should always be awaitable
        return await handler(request)

    @app.get('/async')
    async def async_index(request):
        return text('async_index')

    @app.filter(async_index)
    # one could also `lift` a handler decorator to a filter one
    @filter_decorator(check_args)
    async def async_filter(handler, request):
        # the handler should always be awaitable
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_sync_filter'

    req, resp = app.test_client.get('/checked')
    assert resp.text == 'wrong'

    req, resp = app.test_client.get('/checked?abc=1')
    assert resp.text == 'sync_index_sync_filter'

    req, resp = app.test_client.get('/async')
    assert resp.text == 'wrong_async_filter'

    req, resp = app.test_client.get('/async?abc=1')
    assert resp.text == 'async_index_async_filter'


def test_sync_blueprint_filter_over_sync_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')
    bp = Blueprint(app.name)

    @bp.get('/')
    def sync_index(request):
        return text('sync_index')

    @bp.filter(sync_index)
    def sync_filter(handler, request):
        response = handler(request)
        response.body += b"_sync_filter"
        return response

    app.blueprint(bp)
    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_sync_filter'


def test_sync_blueprint_filter_over_async_handler():
    app = Sanic('test_sync_app_filter_over_async_handler')
    bp = Blueprint(app.name)

    @bp.get('/async')
    async def async_index(request):
        return text('async_index')

    try:
        @bp.filter(async_index)
        def sync_filter(handler, request):
            response = handler(request)
            response.body += b"_async_filter"
            return response
    except TypeError:
        pass
    else:
        raise Exception('This should not pass')


def test_async_blueprint_filter_over_sync_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')
    bp = Blueprint(app.name)

    @bp.get('/')
    def sync_index(request):
        return text('sync_index')

    @bp.filter(sync_index)
    async def async_filter(handler, request):
        # the handler should always be awaitable
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    app.blueprint(bp)
    req, resp = app.test_client.get('/')
    assert resp.text == 'sync_index_async_filter'


def test_async_blueprint_filter_over_async_handler():
    app = Sanic('test_sync_app_filter_over_sync_handler')
    bp = Blueprint(app.name)

    @bp.get('/')
    async def async_index(request):
        return text('async_index')

    @bp.filter(async_index)
    async def async_filter(handler, request):
        response = await handler(request)
        response.body += b"_async_filter"
        return response

    app.blueprint(bp)
    req, resp = app.test_client.get('/')
    assert resp.text == 'async_index_async_filter'


if __name__ == '__main__':
    targets = locals().copy()
    for k, v in targets.items():
        if k.startswith('test') and callable(v):
            print('', k)
            v()
