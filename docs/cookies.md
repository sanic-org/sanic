# Cookies

Cookies are pieces of data which persist inside a user's browser. Sanic can
both read and write cookies, which are stored as key-value pairs.

## Reading cookies

A user's cookies can be accessed `Request` object's `cookie` dictionary.

```python
from sanic.response import text

@app.route("/cookie")
async def test(request):
    test_cookie = request.cookies.get('test')
    return text("Test cookie set to: {}".format(test_cookie))
```

## Writing cookies

When returning a response, cookies can be set on the `Response` object.

```python
from sanic.response import text

@app.route("/cookie")
async def test(request):
    response = text("There's a cookie up in this response")
    response.cookies['test'] = 'It worked!'
    response.cookies['test']['domain'] = '.gotta-go-fast.com'
    response.cookies['test']['httponly'] = True
    return response
```

Response cookies can be set like dictionary values and have the following
parameters available:

- `expires` (datetime): The time for the cookie to expire on the
                        client's browser.
- `path` (string): The subset of URLs to which this cookie applies.
- `comment` (string): A comment (metadata).
- `domain` (string): Specifies the domain for which the cookie is valid. An
           explicitly specified domain must always start with a dot.
- `max-age` (number): Number of seconds the cookie should live for.
- `secure` (boolean): Specifies whether the cookie will only be sent via
                      HTTPS.
- `httponly` (boolean): Specifies whether the cookie cannot be read by
                        Javascript.

**Previous:** [Class-based views](class_based_views.html)

**Next:** [Custom protocols](custom_protocol.html)
