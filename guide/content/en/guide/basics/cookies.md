# Cookies

## Reading

.. column::

    Cookies can be accessed via the `Request` object’s `cookies` dictionary.

.. column::

    ```python
    @app.route("/cookie")
    async def test(request):
        test_cookie = request.cookies.get("test")
        return text(f"Test cookie: {test_cookie}")
    ```



.. tip:: FYI

    💡 The `request.cookies` object is one of a few types that is a dictionary with each value being a `list`. This is because HTTP allows a single key to be reused to send multiple values.

    Most of the time you will want to use the `.get()` method to access the first element and not a `list`. If you do want a `list` of all items, you can use `.getlist()`.

    *Added in v23.3*



## Writing

.. column::

    When returning a response, cookies can be set on the `Response` object: `response.cookies`. This object is an instance of `CookieJar` which is a special sort of dictionary that automatically will write the response headers for you.

.. column::

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

Response cookies can be set like dictionary values and have the following parameters available:

- `path: str` - The subset of URLs to which this cookie applies. Defaults to `/`.
- `domain: str` - Specifies the domain for which the cookie is valid. An explicitly specified domain must always start with a dot.
- `max_age: int` - Number of seconds the cookie should live for.
- `expires: datetime` - The time for the cookie to expire on the client’s browser. Usually it is better to use max-age instead.
- `secure: bool` - Specifies whether the cookie will only be sent via HTTPS. Defaults to `True`.
- `httponly: bool` - Specifies whether the cookie cannot be read by JavaScript.
- `samesite: str` - Available values: Lax, Strict, and None. Defaults to `Lax`.
- `comment: str` - A comment (metadata).
- `host_prefix: bool` - Whether to add the `__Host-` prefix to the cookie.
- `secure_prefix: bool` - Whether to add the `__Secure-` prefix to the cookie.
- `partitioned: bool` - Whether to mark the cookie as partitioned.

To better understand the implications and usage of these values, it might be helpful to read the [MDN documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies) on [setting cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie).


.. tip:: FYI

    By default, Sanic will set the `secure` flag to `True` to ensure that cookies are only sent over HTTPS as a sensible default. This should not be impactful for local development since secure cookies over HTTP should still be sent to `localhost`. For more information, you should read the [MDN documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies) on [secure cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#Secure).


## Deleting

.. column::

    Cookies can be removed semantically or explicitly.

.. column::

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

## Eating

.. column::

    Sanic likes cookies
    
.. column::

    .. attrs::
        :class: is-size-1 has-text-centered
        
        🍪
