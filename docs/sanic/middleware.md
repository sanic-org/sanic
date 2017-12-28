# Middleware And Listeners

Middleware are functions which are executed before or after requests to the
server. They can be used to modify the *request to* or *response from*
user-defined handler functions.

Additionally, Sanic provides listeners which allow you to run code at various points of your application's lifecycle.

## Middleware

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

## Listeners

If you want to execute startup/teardown code as your server starts or closes, you can use the following listeners:

- `before_server_start`
- `after_server_start`
- `before_server_stop`
- `after_server_stop`

These listeners are implemented as decorators on functions which accept the app object as well as the asyncio loop. 

For example:

```python
@app.listener('before_server_start')
async def setup_db(app, loop):
    app.db = await db_setup()

@app.listener('after_server_start')
async def notify_server_started(app, loop):
    print('Server successfully started!')

@app.listener('before_server_stop')
async def notify_server_stopping(app, loop):
    print('Server shutting down!')

@app.listener('after_server_stop')
async def close_db(app, loop):
    await app.db.close()
```

If you want to schedule a background task to run after the loop has started,
Sanic provides the `add_task` method to easily do so.

```python
async def notify_server_started_after_five_seconds():
    await asyncio.sleep(5)
    print('Server successfully started!')

app.add_task(notify_server_started_after_five_seconds())
```

Sanic will attempt to automatically inject the app, passing it as an argument to the task:

```python
async def notify_server_started_after_five_seconds(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(notify_server_started_after_five_seconds)
```

Or you can pass the app explicitly for the same effect:

```python
async def notify_server_started_after_five_seconds(app):
    await asyncio.sleep(5)
    print(app.name)

app.add_task(notify_server_started_after_five_seconds(app))
`
