# Cookie

## 正在阅读

.. 列:

```
Cookie 可以通过 `Request` 对象的 `cookies` 字典访问。
```

.. 列:

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
💡 "request.cookies"对象是几种类型的字典之一，每个值都是 "list"。 这是因为HTTP允许重用单个键来发送多个值。

大部分时间你想使用 `.get()` 方法来访问第一个元素，而不是一个 `list` 。 如果你确实想要一个所有项目的 `list` ，你可以使用 `.getlist()` 。

*添加于v23.3*
```

## 写入中

.. 列:

```
返回响应时，cookie可以在 "Response" 对象上设置: "response.cookies" 此对象是 `CookieJar` 的一个实例，这是一个特殊的词典，它将自动为您写出响应标题。
```

.. 列:

````
```python
@app。 oute("/cookie")
async def test(request):
    response = text("在此响应中有cookie")
    响应。 dd_cookie(
        "test",
        "它正常工作! ,
        domain=". umyummy-cookie。 om",
        httponly=True

    返回响应
```
````

响应 cookie 可以设置为字典值，并且有以下参数可用：

- `路径：str` - 此 cookie 适用的 URL 的子集。 默认值为 `/`。
- `domain: str` - 指定 cookie 有效的域名。 一个明确指定的域必须始终以点开始。
- `max_age: int` - cookie 应该使用的秒数。
- `过期：日期时间` - 客户端浏览器过期的 cookie 时间。 通常最好使用最大年龄。
- `secure: bool` - 指定是否只能通过 HTTPS 发送 cookie 默认值为“True”。
- `http：ool` - 指定 cookie 是否被 JavaScript 读取。
- `samesite: str` - 可用值: Lax, Strict and None 默认为\`Lax'。
- `comment: str` - 备注(metadata)。
- `host_prefix: bool` - 是否将 `__Host-` 前缀添加到 cookie。
- `secure_prefix: bool` - 是否将 `__Secure-` 前缀添加到 cookie。
- `分区：bool` - 是否将 cookie 标记为分区。

为了更好地理解这些数值的影响和用法，阅读[MDN文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)[setting cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)可能会有帮助。

.. tip:: FYI

```
默认情况下，Sanic会将 `secure` 标志设置为 `True` ，以确保只能通过 HTTPS 发送cookie 作为合理的默认值。 这不应对本地发展产生影响，因为通过 HTTP 提供安全的 cookie 仍应发送至 `localhost` 。 欲了解更多信息，您应该在[secure cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)上阅读[MDN documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#Secure)。
```

## 删除中

.. 列:

```
Cookie 可以用语义或明确的方式移除。
```

.. 列:

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

## 吃了

.. 列:

```
Sanic 喜欢cookie
```

.. 列:

```
.. attrs::
    :class: is-size-1 has-text-centered
    
    🍪
```
