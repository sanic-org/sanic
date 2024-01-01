# デコレーター

一貫性のあるDRY Web APIを作成する最善の方法の1つは、デコレータを使用してハンドラから機能を削除することです。 再現できるようにするのです

.. 列::

```
したがって、その上に複数のデコレータを持つSanicビューハンドラを見ることは非常に一般的である。
```

.. 列::

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

## 例

ここにデコレータを作成するためのスターターテンプレートがあります。

この例では、ユーザーが特定のエンドポイントにアクセスする権限があることを確認しましょう。 ハンドラ関数をラップするデコレータを作成できます。 クライアントがリソースにアクセスする権限があるかどうかをリクエストをチェックし、適切なレスポンスを送信します。

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

## テンプレート

デコレータはSanicでアプリケーションを構築するための**基本**です。 これらはコードの移植性と保守性を高めます。

Pythonの禅を言い換えると、「[decorators] は素晴らしいアイデアです。

実装を容易にするために、ここでは、始めるためのコピー/貼り付け可能なコードの3つの例を紹介します。

.. 列::

```
これらのインポート文を追加することを忘れないでください。 `@wraps`を使うと、関数のメタデータをそのまま保持することができます。format@@0(https://docs) ython.org/3/library/functtools.html#functools.wraps). また、ここでは`isawaitable`パターンを使用して、通常または非同期の関数でルートハンドラを使用できます。
```

.. 列::

````
```python
from inspect import isawaitable
from functtools import wraps
```
````

### 引数あり

.. 列::

````
多くの場合、*常に*引数を必要とするデコレータが必要になります。そのため、実装された場合は常にそれを呼び出すことになります。

```python
@app.get("/")
@foobar(1, 2)
async def handler(request: Request):
    return text("hi")
```
````

.. 列::

````
```python
def foobar(arg1, arg2):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):

            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator
```
````

### 引数なし

.. 列::

````
Sometimes you want a decorator that will not take arguments. When this is the case, it is a nice convenience not to have to call it

```python
@app.get("/")
@foobar
async def handler(request: Request):
    return text("hi")
```
````

.. 列::

````
```python
def foobar(func):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):

            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator(func)
```
````

### 引数の有無にかかわらず

.. 列::

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

.. 列::

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
