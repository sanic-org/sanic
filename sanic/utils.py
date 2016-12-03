import aiohttp
from sanic.log import log

HOST = '127.0.0.1'
PORT = 42101


async def local_request(method, uri, cookies=None, *args, **kwargs):
    url = 'http://{host}:{port}{uri}'.format(host=HOST, port=PORT, uri=uri)
    log.info(url)
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with getattr(session, method)(url, *args, **kwargs) as response:
            response.text = await response.text()
            response.body = await response.read()
            return response


def sanic_endpoint_test(app, method='get', uri='/', gather_request=True,
                        loop=None, debug=False, *request_args,
                        **request_kwargs):
    results = []
    exceptions = []

    if gather_request:
        @app.middleware
        def _collect_request(request):
            results.append(request)

    async def _collect_response(sanic, loop):
        try:
            response = await local_request(method, uri, *request_args,
                                           **request_kwargs)
            results.append(response)
        except Exception as e:
            exceptions.append(e)
        app.stop()

    app.run(host=HOST, debug=debug, port=42101,
            after_start=_collect_response, loop=loop)

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
            return results[0]
        except:
            raise ValueError(
                "Request object expected, got ({})".format(results))
