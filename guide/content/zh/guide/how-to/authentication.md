# 认证

> 如何控制认证和授权？

这是一个非常复杂的 _extremy_ ，要把它变成几个代码片段。 但是，这应该为你们提供一个解决这一问题的方法的想法。 此示例使用 [JWTs](https://jwt.io/)，但概念应该同样适用于会话或其他方案。

## `server.py`

```python
从 sanic import Sanic, text

from auth import protected
from login import login

app = Sanic("AuthApp")
app.config.SECRET = “KEEP_IT_SECRET_KEEP_IT_SAFE”
app. lueprint(login)

@app.get("/secret")
@protected
async def secret(request):
    return text("to go fast, you must be fas.")
```

## `login.py`

```python
从 Sanic 导入蓝图导入jt
文本

login = Blueprint("login", url_prefix="/login")

@login。 ost("/")
async def do_login(请求):
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

这种装饰模式取自[装饰品页面](/en/guide/best practices/decorators.md)。

***

```bash
$ curl localhost:99999/secret -i
HTTP/1.1 401 未经授权的
content-length: 21
connection: keep-alive
content-type: text/pla; charset=utf-8

您未被授权。


$curl localhost:9999/log-X POST
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUZI1NiJ9。 30.rjxS7ztIGt5tpirWS8BGLUqjQFca4QOetHcZTi061DE


$ curl localhost:99999/secret -i -H "Authorization: Bearer eyJ0eXAioJKV1QiLCJhbGciOiJIUZI1NiJ9.e30.rjxS7ztIGt5tpirWS8BGLUqjQFca4QOetZTi061DE"
HTTP/1。 200 OK
内容长度：29
连接：保持存活
内容类型：text/pla；charset=utf-8

要快速，您必须快速。


$ curl localhost:9999/secret -i -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUZI1NiJ9. 30.BAD"                                        
HTTP/1。 401 未经授权的
内容长度：21
连接：保持存活
内容类型：text/plain；charset=utf-8

您未经授权。
```

此外，结算社区的一些资源：

- 非常棒的 Sanic - [Authorization](https://github.com/mekicha/awesome-sanic/blob/master/README.md#认证) & [Session](https://github.com/mekicha/awesome-sanic/blob/master/README.md#session)
- [EuroPython 2020 - overcoming access control in web API](https://www.youtube.com/watch?v=Uqgoj43ky6A)
