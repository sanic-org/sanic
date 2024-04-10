# Cookies

## 读取(Reading)

.. column::

```
可以通过 `Request` 对象的 `cookies` 字典来访问 Cookies。
```

.. column::

````
```python
@app.route("/cookie")
async def test(request):
    test_cookie = request.cookies.get("test")
    return text(f"Test cookie: {test_cookie}")
```
````

.. tip:: 提示一下

```
💡 `request.cookies` 对象是一种具有列表值的字典类型之一。这是因为在 HTTP 中，允许使用单个键重复以发送多个值。

大部分情况下，您可能希望使用 `.get()` 方法获取第一个元素而不是一个 `list`。如果您确实需要所有项目组成的 `list`，可以使用 `.getlist()` 方法。

*该功能在 v23.3 版本中添加*
```

## 写入(Writing)

.. column::

```
在返回响应时，可以通过 `Response` 对象上的 `response.cookies` 设置 cookie。该对象是 `CookieJar` 类的一个实例，这是一种特殊类型的字典，它会自动为您写入响应头部信息。
```

.. column::

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

响应中的 cookie 可以像设置字典值一样设置，并且具有以下可用参数：

- `path: str` - 指定该 cookie 适用的 URL 子集， 默认为 `/`。
- `domain: str` - 指定 cookie 有效的域名 。 显式指定的域名必须始终以点号开始。
- `max_age: int` - 表示 cookie 应该存活的时间（秒）。
- `expires: datetime` - 指定 cookie 在客户端浏览器上过期的时间。 通常最好使用 `max_age`。
- `secure: bool` - 表示该 cookie 是否仅通过 HTTPS 发送， 默认为 `True`。
- `httponly: bool` - 表示是否禁止 JavaScript 读取该 cookie 。
- `samesite: str` - 可选值包括 Lax、Strict 和 None， 默认为\`Lax'。
- `comment: str` - 用于提供 cookie 的注释（元数据）。
- `host_prefix: bool` - 指定是否为 cookie 添加 __Host- 前缀。
- `secure_prefix: bool` - 指定是否为 cookie 添加 __Secure- 前缀。
- `partitioned: bool` - 表示是否标记该 cookie 为分区（partitioned）cookie。

为了更好地理解这些参数的作用和使用场景，阅读[MDN文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)  和 [关于设置cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)的相关文档可能会有所帮助。

.. tip:: 提示一下

```
默认情况下，Sanic 会将 `secure` 标志设为 `True`，确保 cookie 只通过 HTTPS 安全传输，这是一个明智的默认设置。这对于本地开发来说一般不会有影响，因为在 HTTP 上安全的 cookie 仍然会被发送到 `localhost`。了解更多的信息，你可能需要阅读 [MDN 文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies) 和 [安全 cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#Secure).
```

## 删除(Deleting)

.. column::

```
Cookie 可以通过语义化方式或明确方式移除。
```

.. column::

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

*别忘了在必要时添加 `path` 或 `domain`！*
````

## 食用(Eating)

.. column::

```
Sanic 喜欢吃 cookies，给你也分一块！
```

.. column::

```
.. attrs::
    :class: is-size-1 has-text-centered
    
    🍪
```
