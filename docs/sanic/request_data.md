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
  Property is providing the default parsing strategy. If you would like to change it look to the section below
  (`Changing the default parsing rules of the queryset`).

  ```python
  from sanic.response import json

  @app.route("/query_string")
  def query_string(request):
      return json({ "parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string })
  ```

- `query_args` (list) - On many cases you would need to access the url arguments in
  a less packed form. `query_args` is the list of `(key, value)` tuples.
  Property is providing the default parsing strategy. If you would like to change it look to the section below
  (`Changing the default parsing rules of the queryset`).
  For the same previous URL queryset `?key1=value1&key2=value2`, the
  `query_args` list would look like `[('key1', 'value1'), ('key2', 'value2')]`.
  And in case of the multiple params with the same key like `?key1=value1&key2=value2&key1=value3`
  the `query_args` list would look like `[('key1', 'value1'), ('key2', 'value2'), ('key1', 'value3')]`.

  The difference between Request.args and Request.query_args
  for the queryset `?key1=value1&key2=value2&key1=value3`

  ```python
  from sanic import Sanic
  from sanic.response import json

  app = Sanic(__name__)


  @app.route("/test_request_args")
  async def test_request_args(request):
      return json({
          "parsed": True,
          "url": request.url,
          "query_string": request.query_string,
          "args": request.args,
          "raw_args": request.raw_args,
          "query_args": request.query_args,
      })

  if __name__ == '__main__':
      app.run(host="0.0.0.0", port=8000)
  ```

  Output

  ```
  {
    "parsed":true,
    "url":"http:\/\/0.0.0.0:8000\/test_request_args?key1=value1&key2=value2&key1=value3",
    "query_string":"key1=value1&key2=value2&key1=value3",
    "args":{"key1":["value1","value3"],"key2":["value2"]},
    "raw_args":{"key1":"value1","key2":"value2"},
    "query_args":[["key1","value1"],["key2","value2"],["key1","value3"]]
  }
  ```

  `raw_args` contains only the first entry of `key1`. Will be deprecated in the future versions.

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

- `headers` (dict) - A case-insensitive dictionary that contains the request headers.

- `method` (str) - HTTP method of the request (ie `GET`, `POST`).

- `ip` (str) - IP address of the requester.

- `port` (str) - Port address of the requester.

- `socket` (tuple) - (IP, port) of the requester.

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
- `token`: The value of Authorization header: `Basic YWRtaW46YWRtaW4=`


## Changing the default parsing rules of the queryset

The default parameters that are using internally in `args` and `query_args` properties to parse queryset:

- `keep_blank_values` (bool): `True` - flag indicating whether blank values in
  percent-encoded queries should be treated as blank strings.
  A true value indicates that blanks should be retained as blank
  strings.  The default false value indicates that blank values
  are to be ignored and treated as if they were  not included.
- `strict_parsing` (bool): `False` - flag indicating what to do with parsing errors. If
  false (the default), errors are silently ignored. If true,
  errors raise a ValueError exception.
- `encoding` and `errors` (str): 'utf-8' and 'replace' - specify how to decode percent-encoded sequences
  into Unicode characters, as accepted by the bytes.decode() method.

If you would like to change that default parameters you could call `get_args` and `get_query_args` methods
with new values.

```python
from sanic.response import json

@app.route("/query_string")
def query_string(request):

    return json({ "parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string })
```


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

## Accessing the handler name with the request.endpoint attribute

The `request.endpoint` attribute holds the handler's name. For instance, the below
route will return "hello".

```python
from sanic.response import text
from sanic import Sanic

app = Sanic()

@app.get("/")
def hello(request):
    return text(request.endpoint)
```

Or, with a blueprint it will be include both, separated by a period. For example,
 the below route would return foo.bar:

```python
from sanic import Sanic
from sanic import Blueprint
from sanic.response import text


app = Sanic(__name__)
blueprint = Blueprint('foo')

@blueprint.get('/')
async def bar(request):
    return text(request.endpoint)

app.blueprint(blueprint)

app.run(host="0.0.0.0", port=8000, debug=True)
```
