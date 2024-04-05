---
title: CORS
---

# クロスオリジンリソース共有 (CORS)

> CORS のアプリケーションを設定するにはどうすればよいですか?

.. note::

```
🏆 最善の解決策は[Sanic Extensions](../../plugins/sanic-ext/http/cors.md)を使用することです。 

ただし、独自のバージョンをビルドしたい場合は、この限られた例を出発点として使用することができます。
```

### `server.py`

```python
from sanic import Sanic, text

from cors import add_cors_headers
from options import setup_options

app = Sanic("app")

@app.route("/", methods=["GET", "POST"])
async def do_stuff(request):
    return text("...")

# Add OPTIONS handlers to any route that is missing it
app.register_listener(setup_options, "before_server_start")

# Fill in CORS headers
app.register_middleware(add_cors_headers, "response")
```

## `cors.py`

```python
from typing import Iterable

def _add_cors_headers(response, methods: Iterable[str]) -> None:
    allow_methods = list(set(methods))
    if "OPTIONS" not in allow_methods:
        allow_methods.append("OPTIONS")
    headers = {
        "Access-Control-Allow-Methods": ",".join(allow_methods),
        "Access-Control-Allow-Origin": "mydomain.com",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": (
            "origin, content-type, accept, "
            "authorization, x-xsrf-token, x-request-id"
        ),
    }
    response.headers.extend(headers)

def add_cors_headers(request, response):
    if request.method != "OPTIONS":
        methods = [method for method in request.route.methods]
        _add_cors_headers(response, methods)
```

## `options.py`

```python
from collections import defaultdict
from typing import Dict, FrozenSet

from sanic import Sanic, response
from sanic.router import Route

from cors import _add_cors_headers

def _compile_routes_needing_options(
    routes: Dict[str, Route]
) -> Dict[str, FrozenSet]:
    needs_options = defaultdict(list)
    # This is 21.12 and later. You will need to change this for older versions.
    for route in routes.values():
        if "OPTIONS" not in route.methods:
            needs_options[route.uri].extend(route.methods)

    return {
        uri: frozenset(methods) for uri, methods in dict(needs_options).items()
    }

def _options_wrapper(handler, methods):
    def wrapped_handler(request, *args, **kwargs):
        nonlocal methods
        return handler(request, methods)

    return wrapped_handler

async def options_handler(request, methods) -> response.HTTPResponse:
    resp = response.empty()
    _add_cors_headers(resp, methods)
    return resp

def setup_options(app: Sanic, _):
    app.router.reset()
    needs_options = _compile_routes_needing_options(app.router.routes_all)
    for uri, methods in needs_options.items():
        app.add_route(
            _options_wrapper(options_handler, methods),
            uri,
            methods=["OPTIONS"],
        )
    app.router.finalize()
```

---

```
$ curl localhost:9999/ -i
HTTP/1.1 200 OK
Access-Control-Allow-Methods: OPTIONS,POST,GET
Access-Control-Allow-Origin: mydomain.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: origin, content-type, accept, authorization, x-xsrf-token, x-request-id
content-length: 3
connection: keep-alive
content-type: text/plain; charset=utf-8

...

$ curl localhost:9999/ -i -X OPTIONS     
HTTP/1.1 204 No Content
Access-Control-Allow-Methods: GET,POST,OPTIONS
Access-Control-Allow-Origin: mydomain.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: origin, content-type, accept, authorization, x-xsrf-token, x-request-id
connection: keep-alive
```

また、コミュニティからいくつかのリソースをチェックアウトします。

- format@@0(https://github.com/mekicha/awesome-sanic/blob/master/README.md#frontend)
