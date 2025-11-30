# 認証

> 認証と認証を制御するにはどうすればよいですか?

これは、いくつかのスニペットに詰め込むために_非常に複雑な対象です。 しかし、これはこの問題に取り組む方法についてのアイデアを提供する必要があります。 この例では [JWTs](https://jwt.io/)を使用しますが、この概念はセッションや他のスキームにも同様に適用されるはずです。

## `server.py`

```python
from sanic import Sanic, text

from auth import protected
from login import login

app = Sanic("AuthApp")
app.config.SECRET = "KEEP_IT_SECRET_KEEP_IT_SAFE"
app.blueprint(login)

@app.get("/secret")
@protected
async def secret(request):
    return text("To go fast, you must be fast.")
```

## `login.py`

```python
import jwt
from sanic import Blueprint, text

login = Blueprint("login", url_prefix="/login")

@login.post("/")
async def do_login(request):
    token = jwt.encode({}, request.app.config.SECRET)
    return text(token)
```

## `auth.py`

```python
from functools import wraps

import jwt
from sanic import text

def check_token(request):
    if not request.token:
        return False

    try:
        jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
    except jwt.exceptions.InvalidTokenError:
        return False
    else:
        return True

def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated = check_token(request)

            if is_authenticated:
                response = await f(request, *args, **kwargs)
                return response
            else:
                return text("You are unauthorized.", 401)

        return decorated_function

    return decorator(wrapped)
```

This decorator pattern is taken from the [decorators page](../best-practices/decorators.md).

---

```bash
$ curl localhost:9999/secret -i
HTTP/1.1 401 Unauthorized
content-length: 21
connection: keep-alive
content-type: text/plain; charset=utf-8

You are unauthorized.


$ curl localhost:9999/login -X POST
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.e30.rjxS7ztIGt5tpiRWS8BGLUqjQFca4QOetHcZTi061DE


$ curl localhost:9999/secret -i -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.e30.rjxS7ztIGt5tpiRWS8BGLUqjQFca4QOetHcZTi061DE"
HTTP/1.1 200 OK
content-length: 29
connection: keep-alive
content-type: text/plain; charset=utf-8

To go fast, you must be fast.


$ curl localhost:9999/secret -i -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.e30.BAD"                                        
HTTP/1.1 401 Unauthorized
content-length: 21
connection: keep-alive
content-type: text/plain; charset=utf-8

You are unauthorized.
```

また、コミュニティからいくつかのリソースをチェックアウトします。

- Awesome Sanic - [Authorization](https://github.com/mekicha/awesome-sanic/blob/master/README.md#authentication) & [Session](https://github.com/mekicha/awesome-sanic/blob/master/README.md#session)
- [EuroPython 2020 - Web APIでのアクセス制御の克服](https://www.youtube.com/watch?v=Uqgoj43ky6A)
