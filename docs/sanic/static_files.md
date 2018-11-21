# Static Files

Static files and directories, such as an image file, are served by Sanic when
registered with the `app.static()` method. The method takes an endpoint URL and a
filename. The file specified will then be accessible via the given endpoint.

```python
from sanic import Sanic
from sanic.blueprints import Blueprint

app = Sanic(__name__)

# Serves files from the static folder to the URL /static
app.static('/static', './static')
# use url_for to build the url, name defaults to 'static' and can be ignored
app.url_for('static', filename='file.txt') == '/static/file.txt'
app.url_for('static', name='static', filename='file.txt') == '/static/file.txt'

# Serves the file /home/ubuntu/test.png when the URL /the_best.png
# is requested
app.static('/the_best.png', '/home/ubuntu/test.png', name='best_png')

# you can use url_for to build the static file url
# you can ignore name and filename parameters if you don't define it
app.url_for('static', name='best_png') == '/the_best.png'
app.url_for('static', name='best_png', filename='any') == '/the_best.png'

# you need define the name for other static files
app.static('/another.png', '/home/ubuntu/another.png', name='another')
app.url_for('static', name='another') == '/another.png'
app.url_for('static', name='another', filename='any') == '/another.png'

# also, you can use static for blueprint
bp = Blueprint('bp', url_prefix='/bp')
bp.static('/static', './static')

# servers the file directly
bp.static('/the_best.png', '/home/ubuntu/test.png', name='best_png')
app.blueprint(bp)

app.url_for('static', name='bp.static', filename='file.txt') == '/bp/static/file.txt'
app.url_for('static', name='bp.best_png') == '/bp/test_best.png'

app.run(host="0.0.0.0", port=8000)
```

> **Note:** Sanic does not provide directory index when you serve a static directory.

## Virtual Host

The `app.static()` method also support **virtual host**. You can serve your static files with spefic **virtual host** with `host` argument. For example:

```python
from sanic import Sanic

app = Sanic(__name__)

app.static('/static', './static')
app.static('/example_static', './example_static', host='www.example.com')
```

## Streaming Large File

In some cases, you might server large file(ex: videos, images, etc.) with Sanic. You can choose to use **streaming file** rather than download directly.

Here is an example:
```python
from sanic import Sanic

app = Sanic(__name__)

app.static('/large_video.mp4', '/home/ubuntu/large_video.mp4', stream_large_files=True)
```

When `stream_large_files` is `True`, Sanic will use `file_stream()` instead of `file()` to serve static files. This will use **1KB** as the default chunk size. And, if needed, you can also use a custom chunk size. For example:
```python
from sanic import Sanic

app = Sanic(__name__)

chunk_size = 1024 * 1024 * 8 # Set chunk size to 8KB
app.static('/large_video.mp4', '/home/ubuntu/large_video.mp4', stream_large_files=chunk_size)
```
