async def get_uri(app):
        return {'uris': app.router.routes_all}



async def get_middlewares(app):
    middlewares = {
        'request': app.request_middleware,
        'response': app.response_middleware,
        'named_request': app.named_request_middleware,
        'named_response': app.named_response_middleware }

    return {'middlewares': middlewares}
