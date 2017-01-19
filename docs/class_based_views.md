# Class based views

Sanic has simple class based implementation. You should implement methods(get, post, put, patch, delete) for the class to every HTTP method you want to support. If someone tries to use a method that has not been implemented, there will be 405 response.

## Examples
```python
from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import text

app = Sanic('some_name')


class SimpleView(HTTPMethodView):

  def get(self, request):
      return text('I am get method')

  def post(self, request):
      return text('I am post method')

  def put(self, request):
      return text('I am put method')

  def patch(self, request):
      return text('I am patch method')

  def delete(self, request):
      return text('I am delete method')

app.add_route(SimpleView(), '/')

```

If you need any url params just mention them in method definition:

```python
class NameView(HTTPMethodView):

  def get(self, request, name):
    return text('Hello {}'.format(name))

app.add_route(NameView(), '/<name>')

```

If you want to add decorator for class, you could set decorators variable

```
class ViewWithDecorator(HTTPMethodView):
  decorators = [some_decorator_here]

  def get(self, request, name):
    return text('Hello I have a decorator')

app.add_route(ViewWithDecorator(), '/url')

```
