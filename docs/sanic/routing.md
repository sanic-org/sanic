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

## Request parameters

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

By default, a route defined on a URL will be avaialble for only GET requests to that URL.
However, the `@app.route` decorator accepts an optional parameter, `methods`,
whicl allows the handler function to work with any of the HTTP methods in the list.

```python
from sanic.response import text

@app.route('/post', methods=['POST'])
async def post_handler(request):
	return text('POST request - {}'.format(request.json))

@app.route('/get', methods=['GET'])
async def get_handler(request):
	return text('GET request - {}'.format(request.args))

```

There are also shorthand method decorators:

```python
from sanic.response import text

@app.post('/post')
async def post_handler(request):
	return text('POST request - {}'.format(request.json))

@app.get('/get')
async def get_handler(request):
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

## URL building with `url_for`

Sanic provides a `url_for` method, to generate URLs based on the handler method name. This is useful if you want to avoid hardcoding url paths into your app; instead, you can just reference the handler name. For example:

```python
@app.route('/')
async def index(request):
    # generate a URL for the endpoint `post_handler`
    url = app.url_for('post_handler', post_id=5)
    # the URL is `/posts/5`, redirect to it
    return redirect(url)


@app.route('/posts/<post_id>')
async def post_handler(request, post_id):
    return text('Post - {}'.format(post_id))
```

Other things to keep in mind when using `url_for`:

- Keyword arguments passed to `url_for` that are not request parameters will be included in the URL's query string. For example:
```python
url = app.url_for('post_handler', post_id=5, arg_one='one', arg_two='two')
# /posts/5?arg_one=one&arg_two=two
```
- Multivalue argument can be passed to `url_for`. For example:
```python
url = app.url_for('post_handler', post_id=5, arg_one=['one', 'two'])
# /posts/5?arg_one=one&arg_one=two
```
- Also some special arguments (`_anchor`, `_external`, `_scheme`, `_method`, `_server`) passed to `url_for` will have special url building (`_method` is not support now and will be ignored). For example:
```python
url = app.url_for('post_handler', post_id=5, arg_one='one', _anchor='anchor')
# /posts/5?arg_one=one#anchor

url = app.url_for('post_handler', post_id=5, arg_one='one', _external=True)
# //server/posts/5?arg_one=one
# _external requires passed argument _server or SERVER_NAME in app.config or url will be same as no _external

url = app.url_for('post_handler', post_id=5, arg_one='one', _scheme='http', _external=True)
# http://server/posts/5?arg_one=one
# when specifying _scheme, _external must be True

# you can pass all special arguments one time
url = app.url_for('post_handler', post_id=5, arg_one=['one', 'two'], arg_two=2, _anchor='anchor', _scheme='http', _external=True, _server='another_server:8888')
# http://another_server:8888/posts/5?arg_one=one&arg_one=two&arg_two=2#anchor
```
- All valid parameters must be passed to `url_for` to build a URL. If a parameter is not supplied, or if a parameter does not match the specified type, a `URLBuildError` will be thrown.





