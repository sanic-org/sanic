# Class based views

Sanic has simple class based implementation. You should implement methods(get, post, put, patch, delete) for the class to every HTTP method you want to support. If someone try to use not implemented method, there will be 405 response.

## Examples
```python
from sanic import Sanic
from sanic.views import MethodView

app = Sanic('some_name')


class SimpleView(MethodView):

  def get(self, request, *args, **kwargs):
      return text('I am get method')

  def post(self, request, *args, **kwargs):
      return text('I am post method')

  def put(self, request, *args, **kwargs):
      return text('I am put method')

  def patch(self, request, *args, **kwargs):
      return text('I am patch method')

  def delete(self, request, *args, **kwargs):
      return text('I am delete method')

app.add_route(SimpleView(), '/')

```

If you need any url params just mention them in method definition:

```python
class NameView(MethodView):

  def get(self, request, name, *args, **kwargs):
    return text('Hello {}'.format(name))

app.add_route(NameView(), '/<name')

```
