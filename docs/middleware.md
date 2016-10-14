# Middleware

Middleware can be executed before or after requests.  It is executed in the order it was registered.  If middleware return a reponse object, the request will stop processing and a response will be returned.

Middleware is registered via the middleware decorator, and can either be added as 'request' or 'response' middleware, based on the argument provided in the decorator.  Response middleware receives both the request and the response as arguments.

## Examples

```python
app = Sanic('__name__')

@app.middleware
async def halt_request(request):
	print("I am a spy")

@app.middleware('request')
async def halt_request(request):
	return text('I halted the request')

@app.middleware('response')
async def halt_response(request, response):
	return text('I halted the response')

@app.route('/')
async def handler(request):
	return text('I would like to speak now please')

app.run(host="0.0.0.0", port=8000)
```