# Routing

Routing allows the user to specify handler functions for different URL endpoints.

A basic route looks like the following, where `app` is an instance of the
`Sanic` class:

```python
from sanic.response import json

@app.route("/")
async def test(request):
    return json({ "hello": "world" })
``` 

When the url `http://server.url/` is accessed (the base url of the server), the
final `/` is matched by the router to the handler function, `test`, which then
returns a JSON object.

Sanic handler functions must be defined using the `async def` syntax, as they
are asynchronous functions.

## Request Parameters

Sanic comes with a basic router that supports request parameters.

To specify a parameter, surround it with angle quotes like so: `<PARAM>`.
Request parameters will be passed to the route handler functions as keyword
arguments.

```python
from sanic.response import text

@app.route('/tag/<tag>')
async def tag_handler(request, tag):
	return text('Tag - {}'.format(tag))
```

To specify a type for the parameter, add a `:type` after the parameter name,
inside the quotes. If the parameter does not match the specified type, Sanic
will throw a `NotFound` exception, resulting in a `404: Page not found` error
on the URL.

```python
from sanic.response import text

@app.route('/number/<integer_arg:int>')
async def integer_handler(request, integer_arg):
	return text('Integer - {}'.format(integer_arg))

@app.route('/number/<number_arg:number>')
async def number_handler(request, number_arg):
	return text('Number - {}'.format(number_arg))

@app.route('/person/<name:[A-z]>')
async def person_handler(request, name):
	return text('Person - {}'.format(name))

@app.route('/folder/<folder_id:[A-z0-9]{0,4}>')
async def folder_handler(request, folder_id):
	return text('Folder - {}'.format(folder_id))

```

## HTTP request types

By default, a route defined on a URL will be used for all requests to that URL.
However, the `@app.route` decorator accepts an optional parameter, `methods`,
which restricts the handler function to the HTTP methods in the given list.

```python
from sanic.response import text

@app.route('/post')
async def post_handler(request, methods=['POST']):
	return text('POST request - {}'.format(request.json))

@app.route('/get')
async def GET_handler(request, methods=['GET']):
	return text('GET request - {}'.format(request.args))

```

## The `add_route` method

As we have seen, routes are often specified using the `@app.route` decorator.
However, this decorator is really just a wrapper for the `app.add_route`
method, which is used as follows:

```python
from sanic.response import text

# Define the handler functions
async def handler1(request):
	return text('OK')

async def handler2(request, name):
	return text('Folder - {}'.format(name))

async def person_handler2(request, name):
	return text('Person - {}'.format(name))

# Add each handler function as a route
app.add_route(handler1, '/test')
app.add_route(handler2, '/folder/<name>')
app.add_route(person_handler2, '/person/<name:[A-z]>', methods=['GET'])
```
