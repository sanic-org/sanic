import aiohttp
from sanic.log import log

HOST = '127.0.0.1'
PORT = 42101


async def local_request(method, uri, cookies=None, *args, **kwargs):
    url = 'http://{host}:{port}{uri}'.format(host=HOST, port=PORT, uri=uri)
    log.info(url)
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with getattr(
                session, method.lower())(url, *args, **kwargs) as response:
            response.text = await response.text()
            response.body = await response.read()
            return response


def sanic_endpoint_test(app, method='get', uri='/', gather_request=True,
                        debug=False, server_kwargs={}, *request_args,
                        **request_kwargs):
    results = [None, None]
    exceptions = []

    if gather_request:
        def _collect_request(request):
            if results[0] is None:
                results[0] = request
        app.request_middleware.appendleft(_collect_request)

    @app.listener('after_server_start')
    async def _collect_response(sanic, loop):
        try:
            response = await local_request(method, uri, *request_args,
                                           **request_kwargs)
            results[-1] = response
        except Exception as e:
            exceptions.append(e)
        app.stop()

    app.run(host=HOST, debug=debug, port=PORT, **server_kwargs)
    app.listeners['after_server_start'].pop()

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
