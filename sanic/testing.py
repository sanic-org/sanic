from sanic.log import log
from functools import partial

HOST = '127.0.0.1'
PORT = 42101

SUPPORTED_METHODS = [
    'get',
    'post',
    'put',
    'delete',
    'patch',
    'options',
    'head',
]


class TestClient:
    def __init__(self, app):
        self.app = app

    async def _local_request(self, method, uri, cookies=None, *args, **kwargs):
        import aiohttp
        if uri.startswith(('http:', 'https:', 'ftp:', 'ftps://' '//')):
            url = uri
        else:
            url = 'http://{host}:{port}{uri}'.format(
                host=HOST, port=PORT, uri=uri)

        log.info(url)
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with getattr(
                    session, method.lower())(url, *args, **kwargs) as response:
                response.text = await response.text()
                response.body = await response.read()
                return response

    def _sanic_endpoint_test(
            self, method='get', uri='/', gather_request=True,
            debug=False, server_kwargs={},
            *request_args, **request_kwargs):
        results = [None, None]
        exceptions = []

        if gather_request:
            def _collect_request(request):
                if results[0] is None:
                    results[0] = request
            self.app.request_middleware.appendleft(_collect_request)

        @self.app.listener('after_server_start')
        async def _collect_response(sanic, loop):
            try:
                response = await self._local_request(
                    method, uri, *request_args,
                    **request_kwargs)
                results[-1] = response
            except Exception as e:
                exceptions.self.append(e)
            self.app.stop()

        self.app.run(host=HOST, debug=debug, port=PORT, **server_kwargs)
        self.app.listeners['after_server_start'].pop()

        if exceptions:
            raise ValueError("Exception during request: {}".format(exceptions))

        if gather_request:
            try:
                request, response = results
                return request, response
            except:
                raise ValueError(
                    "Request and response object expected, got ({})".format(
                        results))
        else:
            try:
                return results[-1]
            except:
                raise ValueError(
                    "Request object expected, got ({})".format(results))

    def __getattr__(self, attr, *args, **kwargs):
        if attr in SUPPORTED_METHODS:
            return partial(self._sanic_endpoint_test, attr, *args, **kwargs)
        else:
            raise AttributeError
