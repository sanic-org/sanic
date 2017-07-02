# Request Data

When an endpoint receives a HTTP request, the route function is passed a
`Request` object.

The following variables are accessible as properties on `Request` objects:

- `json` (any) - JSON body

  ```python
  from sanic.response import json

  @app.route("/json")
  def post_json(request):
      return json({ "received": True, "message": request.json })
  ```

- `args` (dict) - Query string variables. A query string is the section of a
  URL that resembles `?key1=value1&key2=value2`. If that URL were to be parsed,
  the `args` dictionary would look like `{'key1': ['value1'], 'key2': ['value2']}`.
  The request's `query_string` variable holds the unparsed string value.

  ```python
  from sanic.response import json

  @app.route("/query_string")
  def query_string(request):
      return json({ "parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string })
  ```

- `raw_args` (dict) - On many cases you would need to access the url arguments in
  a less packed dictionary. For same previous URL `?key1=value1&key2=value2`, the
  `raw_args` dictionary would look like `{'key1': 'value1', 'key2': 'value2'}`.

- `files` (dictionary of `File` objects) - List of files that have a name, body, and type

  ```python
  from sanic.response import json

  @app.route("/files")
  def post_json(request):
      test_file = request.files.get('test')

      file_parameters = {
          'body': test_file.body,
          'name': test_file.name,
          'type': test_file.type,
      }

      return json({ "received": True, "file_names": request.files.keys(), "test_file_parameters": file_parameters })
  ```

- `form` (dict) - Posted form variables.

  ```python
  from sanic.response import json

  @app.route("/form")
  def post_json(request):
      return json({ "received": True, "form_data": request.form, "test": request.form.get('test') })
  ```

- `body` (bytes) - Posted raw body. This property allows retrieval of the
  request's raw data, regardless of content type.

  ```python
  from sanic.response import text

  @app.route("/users", methods=["POST",])
  def create_user(request):
      return text("You are trying to create a user with the following POST: %s" % request.body)
  ```

- `ip` (str) - IP address of the requester.

- `app` - a reference to the Sanic application object that is handling this request. This is useful when inside blueprints or other handlers in modules that do not have access to the global `app` object.

  ```python
  from sanic.response import json
  from sanic import Blueprint

  bp = Blueprint('my_blueprint')

  @bp.route('/')
  async def bp_root(request):
      if request.app.config['DEBUG']:
          return json({'status': 'debug'})
      else:
          return json({'status': 'production'})

  ```
- `url`: The full URL of the request, ie: `http://localhost:8000/posts/1/?foo=bar`
- `scheme`: The URL scheme associated with the request: `http` or `https`
- `host`: The host associated with the request: `localhost:8080`
- `path`: The path of the request: `/posts/1/`
- `query_string`: The query string of the request: `foo=bar` or a blank string `''`
- `uri_template`: Template for matching route handler: `/posts/<id>/`


## Accessing values using `get` and `getlist`

The request properties which return a dictionary actually return a subclass of
`dict` called `RequestParameters`. The key difference when using this object is
the distinction between the `get` and `getlist` methods.

- `get(key, default=None)` operates as normal, except that when the value of
  the given key is a list, *only the first item is returned*.
- `getlist(key, default=None)` operates as normal, *returning the entire list*.

```python
from sanic.request import RequestParameters

args = RequestParameters()
args['titles'] = ['Post 1', 'Post 2']

args.get('titles') # => 'Post 1'

args.getlist('titles') # => ['Post 1', 'Post 2']
```


## Full API Reference

```eval_rst
.. autoclass:: sanic.request.Request
    :members: json, token, form, files, args, raw_args, cookies, ip, scheme, host, content_type, path, query_string, url
```