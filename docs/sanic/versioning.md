# Versioning

You can pass the `version` keyword to the route decorators, or to a blueprint initializer. It will result in the `v{version}` url prefix where `{version}` is the version number.

## Per route

You can pass a version number to the routes directly.

```python
from sanic import response


@app.route('/text', verion=1)
def handle_request(request):
    return response.text('Hello world! Version 1')

@app.route('/text', verion=2)
def handle_request(request):
    return response.text('Hello world! Version 2')

app.run(port=80)
```

Then with curl:

```bash
curl localhost/v1/text
curl localhost/v2/text
```

## Global blueprint version

You can also pass a version number to the blueprint, which will apply to all routes.

```python
from sanic import response
from sanic.blueprints import Blueprint

bp = Blueprint('test', version=1)

@bp.route('/html')
def handle_request(request):
    return response.html('<p>Hello world!</p>')
```

Then with curl:

```bash
curl localhost/v1/html
```
