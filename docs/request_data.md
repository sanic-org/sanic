# Request Data

## Properties

The following request variables are accessible as properties:

request.files (dictionary of File objects) - List of files that have a name, body, and type
request.json (any) - JSON body
request.args (dict) - Query String variables.  Use getlist to get multiple of the same name
request.form (dict) - Posted form variables.  Use getlist to get multiple of the same name

See request.py for more information

## Examples

```python
from sanic import Sanic
from sanic.response import json

@app.route("/json")
def post_json(request):
    return json({ "received": True, "message": request.json })

@app.route("/form")
def post_json(request):
    return json({ "received": True, "form_data": request.form, "test": request.form.get('test') })

@app.route("/files")
def post_json(request):
	test_file = request.files.get('test')

	file_parameters = {
		'body': test_file.body,
		'name': test_file.name,
		'type': test_file.type,
	}

    return json({ "received": True, "file_names": request.files.keys(), "test_file_parameters": file_parameters })

@app.route("/query_string")
def query_string(request):
    return json({ "parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string })
```