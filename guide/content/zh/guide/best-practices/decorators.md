# 装饰符

创建一致的 DRY 网页API 的最佳方法之一是利用装饰器从处理器中移除功能。 并使之可以在你的意见中重复出现。

.. 列:

```
因此，非常常见的情况是看到一个带有几个装饰师的Sanic视图处理器。
```

.. 列:

````
```python
@app.get("/orders")
@authorized("view_order")
@validate_list_params()
@inject_user()
async def get_order_details(request, params, user):
    ...
```
````

## 示例

这是一个帮助您创建装饰程序的启动模板。

在这个示例中，让我们说你想要检查用户是否被授权访问某个特定端点。 您可以创建一个装饰器，包装处理函数。 检查客户是否有权访问资源的请求，并发送适当的响应。

```python
from functools import wraps
from sanic.response import json

def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = await check_request_for_authorization_status(request)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return json({"status": "not_authorized"}, 403)
        return decorated_function
    return decorator

@app.route("/")
@authorized()
async def test(request):
    return json({"status": "authorized"})
```

## 模板

装饰器是 **基础** ，用于构建带萨尼语的应用程序。 它们提高了您的代码的可携带性和可维护性。

在解析Python的Zen时：“[decorators] 是一个很好的主意——让我们做更多的事！”

为了使它们更容易实现，在这里是三个可复制/可粘贴代码的例子来让您开始操作。

.. 列:

```
不要忘记添加这些导入语句。 虽然它是*不是*必需的，但使用 @wraws` 有助于保持您函数的某些元数据完整。[见文档](https://docs)。 ython.org/3/library/functools.html#functools.wrawals。另外，我们在这里使用 `isawaitable` 模式，允许通过常规或异步函数处理路由处理程序。
```

.. 列:

````
```python
from inspect import isawaitable
from functools import wraps
```
````

### 带参数：

.. 列:

````
你常常想要一个装饰器，它将*总是需要参数。因此，当它实现时，你总是会调用它。

```python
@app.get("/")
@foobar(1, 2)
async def 处理器(请求: 请求):
    return text("hi")
```
````

.. 列:

````
```python
def foobar(g1, arg2:
    def 装饰物(f):
        @wraws(f)
        async def 装饰函数(请求) *args, **kwargs):

            response = f(request, *args, **kwargs)
            if isawaitable (response):
                response = requires

            return response

        return decorated_function

    return Decorator
```
````

### 没有参数

.. 列:

````
有时你想要一个不需要参数的装饰器。 在这种情况下，最好不要调用

``python
@app。 et("/")
@foobar
async def 处理器(请求: 请求):
    return text("hi")
```
````

.. 列:

````
```python
def foobar(function):
    def decorator(f):
        @wraws(f)
        async def decorated_function_request. *args, **kwargs):

            response = f(request, *args, **kwargs)
            if isawaitable (response):
                response = 等待回应

            return response

        return decorated_function

    return decorator(ffunc)
```
````

### 使用或不使用参数

.. 列:

````
If you want a decorator with the ability to be called or not, you can follow this pattern. Using keyword only arguments is not necessary, but might make implementation simpler.

```python
@app.get("/")
@foobar(arg1=1, arg2=2)
async def handler(request: Request):
    return text("hi")
```

```python
@app.get("/")
@foobar
async def handler(request: Request):
    return text("hi")
```
````

.. 列:

````
```python
def foobar(maybe_func=None, *, arg1=None, arg2=None):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):

            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator(maybe_func) if maybe_func else decorator
```
````
