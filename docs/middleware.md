# Middleware

Middleware are functions which are executed before or after requests to the
server. They can be used to modify the *request to* or *response from*
user-defined handler functions.

There are two types of middleware: request and response. Both are declared
using the `@app.middleware` decorator, with the decorator's parameter being a
string representing its type: `'request'` or `'response'`. Response middleware
receives both the request and the response as arguments.


The simplest middleware doesn't modify the request or response at all:

```python
@app.middleware('request')
async def print_on_request(request):
	print("I print when a request is received by the server")

@app.middleware('response')
async def print_on_response(request, response):
	print("I print when a response is returned by the server")
```

## Modifying the request or response

Middleware can modify the request or response parameter it is given, *as long
as it does not return it*. The following example shows a practical use-case for
this.

```python
app = Sanic(__name__)

@app.middleware('response')
async def custom_banner(request, response):
	response.headers["Server"] = "Fake-Server"

@app.middleware('response')
async def prevent_xss(request, response):
	response.headers["x-xss-protection"] = "1; mode=block"

app.run(host="0.0.0.0", port=8000)
```

The above code will apply the two middleware in order. First, the middleware
**custom_banner** will change the HTTP response header *Server* to
*Fake-Server*, and the second middleware **prevent_xss** will add the HTTP
header for preventing Cross-Site-Scripting (XSS) attacks. These two functions
are invoked *after* a user function returns a response.

## Responding early

If middleware returns a `HTTPResponse` object, the request will stop processing
and the response will be returned. If this occurs to a request before the
relevant user route handler is reached, the handler will never be called.
Returning a response will also prevent any further middleware from running.

```python
@app.middleware('request')
async def halt_request(request):
	return text('I halted the request')

@app.middleware('response')
async def halt_response(request, response):
	return text('I halted the response')
```

**Previous:** [Static Files](static_files.html)

**Next:** [Exceptions](exceptions.html)
