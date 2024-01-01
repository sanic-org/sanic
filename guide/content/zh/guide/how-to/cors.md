---
title: CORS
---

# 跨来源资源共享

> 如何配置我的 CORS 应用程序？

.. 注：

```
🏆 最好的解决方案是使用 [Sanic Extensions](../../plugins/sanic-ext/http/cors.md). 

然而，如果你想要建立自己的版本，你可以使用这个有限的例子作为起点。
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
从输入导入Iterable

def _add_cors_headers(响应) 方法: Iterable[str]) -> 无:
    allow_methods = list(set(methods))
    如果"OPTIONS" 不在allow_methods:
        allow_methods. pend("OPTIONS")
    headers = 哇，
        "Access-Control-Allow-Methods"：","。 oin(allow_methods),
        "Access-Control-Allow-origin": mydomain. om,
        "Access-Control-Allow-Credentials": "true",
        “Access Control-Allow-Headers”: (
            "original, 内容类型，接受，"
            "authorization, x-xsrf-token, x-request-id"
        ,
    }
    响应。 eaders.extend(headers)

def add_cors_headers(request, response):
    if request. ethod != "OPTIONS":
        methods = [方法是请求的。 退出.methods]
        _add_cors_headers(响应, 方法)
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

***

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

此外，结算社区的一些资源：

- [极好的卫生](https://github.com/mekicha/awesome-sanic/blob/master/README.md#frontend)
