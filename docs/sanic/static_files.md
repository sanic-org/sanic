# Static Files

Static files and directories, such as an image file, are served by Sanic when
registered with the `app.static` method. The method takes an endpoint URL and a
filename. The file specified will then be accessible via the given endpoint.

```python
from sanic import Sanic
app = Sanic(__name__)

# Serves files from the static folder to the URL /static
app.static('/static', './static')

# Serves the file /home/ubuntu/test.png when the URL /the_best.png
# is requested
app.static('/the_best.png', '/home/ubuntu/test.png')

app.run(host="0.0.0.0", port=8000)
```

Note: currently you cannot build a URL for a static file using `url_for`. 
