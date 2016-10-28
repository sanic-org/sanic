# Routing

Sanic comes with a basic router that supports request parameters.  To specify a parameter, surround it with carrots like so: `<PARAM>`.  Request parameters will be passed to the request handler functions as keyword arguments.  To specify a type, add a :type after the parameter name, in the carrots.  If the parameter does not match the type supplied, Sanic will throw a NotFound exception, resulting in a 404 page not found error.


## Examples

```python
from sanic import Sanic
from sanic.response import text

@app.route('/tag/<tag>')
async def tag_handler(request, tag):
	return text('Tag - {}'.format(tag))

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
