# Cookies

## Request

Request cookies can be accessed via the request.cookie dictionary

### Example

```python
from sanic import Sanic
from sanic.response import text

@app.route("/cookie")
async def test(request):
    test_cookie = request.cookies.get('test')
    return text("Test cookie set to: {}".format(test_cookie))
```

## Response

Response cookies can be set like dictionary values and 
have the following parameters available:

* expires - datetime - Time for cookie to expire on the client's browser
* path - string - The Path attribute specifies the subset of URLs to 
         which this cookie applies
* comment - string - Cookie comment (metadata)
* domain - string - Specifies the domain for which the
           cookie is valid.  An explicitly specified domain must always 
           start with a dot.
* max-age - number - Number of seconds the cookie should live for
* secure - boolean - Specifies whether the cookie will only be sent via
           HTTPS
* httponly - boolean - Specifies whether the cookie cannot be read
             by javascript

### Example

```python
from sanic import Sanic
from sanic.response import text

@app.route("/cookie")
async def test(request):
    response = text("There's a cookie up in this response")
    response.cookies['test'] = 'It worked!'
    response.cookies['test']['domain'] = '.gotta-go-fast.com'
    response.cookies['test']['httponly'] = True
    return response
```