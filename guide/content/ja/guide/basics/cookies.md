# Cookie

## 読書中

.. 列::

```
Cookie は `Request` オブジェクトの `cookies` 辞書からアクセスできます。
```

.. 列::

````
```python
@app.route("/cookie")
async def test(request):
    test_cookie = request.cookies.get("test")
    return text(f"Test cookie: {test_cookie}")
```
````

.. tip:: FYI

```
💡 The `request.cookies` object is one of a few types that is a dictionary with each value being a `list`. This is because HTTP allows a single key to be reused to send multiple values.

Most of the time you will want to use the `.get()` method to access the first element and not a `list`. If you do want a `list` of all items, you can use `.getlist()`.

*Added in v23.3*
```

## 執筆中

.. 列::

```
レスポンスを返すときは、`Response` オブジェクト: `response.cookies` にクッキーを設定できます。 このオブジェクトは `CookieJar` のインスタンスで、自動的にレスポンスヘッダーを書き込む特別な種類の辞書です。
```

.. 列::

````
```python
@app.route("/cookie")
async def test(request):
    response = text("There's a cookie up in this response")
    response.add_cookie(
        "test",
        "It worked!",
        domain=".yummy-yummy-cookie.com",
        httponly=True
    )
    return response
```
````

Response Cookieは辞書の値のように設定でき、次のパラメータを使用できます。

- `path: str` - このクッキーが適用される URL のサブセット。 デフォルトは `/` です。
- `domain: str` - クッキーが有効なドメインを指定します。 明示的に指定されたドメインは常にドットで始まる必要があります。
- `max_age: int` - クッキーが生き残るべき秒数。
- `expires: datetime` - クッキーがクライアントのブラウザで期限切れになる時間。 通常、max-age を代わりに使用する方が良いです。
- `secure: bool` - HTTPS でのみクッキーを送信するかどうかを指定します。 デフォルトは `True` です。
- `httponly: bool` - クッキーをJavaScriptで読み取れないかどうかを指定します。
- `samesite: str` - 利用可能な値: Lax, Strict, None。 デフォルトは `Lax` です。
- `comment: str` - コメント (metadata)
- `host_prefix: bool` - Cookieに`__Host-`プレフィックスを追加するかどうか。
- `secure_prefix: bool` - Cookieに`__Secure-`プレフィックスを追加するかどうか。
- `partitioned: bool` - クッキーをパーティションとしてマークするかどうか。

これらの値の意味と使用状況をよりよく理解するためには、format@@0(https\://developer.mozilla.org/en-US/docs/Web/HTTP/Cookie)のformat@@1(https\://developer.mozilla.org/docs/Web/HTTP/Cookie)を読むと便利かもしれません。

.. tip:: FYI

```
デフォルトでは、Sanicは`secure`フラグを`True`に設定し、HTTPS経由でのみクッキーが正常なデフォルトとして送信されるようにします。 これはローカル開発にとって影響を与えるべきではありません。なぜなら、HTTP を介した セキュアな Cookie は `localhost` に送られるべきだからです。 詳細については、[secure cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookie#restrict_access_to_cookies) の[secure cookies](https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie#Secure)をご覧ください。
```

## 削除中

.. 列::

```
クッキーは意味的または明示的に削除することができます。
```

.. 列::

````
```python
@app.route("/cookie")
async def test(request):
    response = text("Time to eat some cookies muahaha")

    # This cookie will be set to expire in 0 seconds
    response.delete_cookie("eat_me")

    # This cookie will self destruct in 5 seconds
    response.add_cookie("fast_bake", "Be quick!", max_age=5)

    return response
```

*Don't forget to add `path` or `domain` if needed!*
````

## 食べる

.. 列::

```
Sanicはクッキーが好き
```

.. 列::

```
.. attrs:
    :class: is-size-1 has-text-centered
    
🍪
```
