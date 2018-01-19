# Class-Based Views

Class-based views are simply classes which implement response behaviour to
requests. They provide a way to compartmentalise handling of different HTTP
request types at the same endpoint. Rather than defining and decorating three
different handler functions, one for each of an endpoint's supported request
type, the endpoint can be assigned a class-based view.

## Defining views

A class-based view should subclass `HTTPMethodView`. You can then implement
class methods for every HTTP request type you want to support. If a request is
received that has no defined method, a `405: Method not allowed` response will
be generated.

To register a class-based view on an endpoint, the `app.add_route` method is
used. The first argument should be the defined class with the method `as_view`
invoked, and the second should be the URL endpoint.

The available methods are `get`, `post`, `put`, `patch`, and `delete`. A class
using all these methods would look like the following.

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

app.add_route(SimpleView.as_view(), '/')

```

You can also use `async` syntax.

```python
from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import text

app = Sanic('some_name')

class SimpleAsyncView(HTTPMethodView):

  async def get(self, request):
      return text('I am async get method')

app.add_route(SimpleAsyncView.as_view(), '/')

```

## URL parameters

If you need any URL parameters, as discussed in the routing guide, include them
in the method definition.

```python
class NameView(HTTPMethodView):

  def get(self, request, name):
    return text('Hello {}'.format(name))

app.add_route(NameView.as_view(), '/<name>')
```

## Decorators

If you want to add any decorators to the class, you can set the `decorators`
class variable. These will be applied to the class when `as_view` is called.

```python
class ViewWithDecorator(HTTPMethodView):
  decorators = [some_decorator_here]

  def get(self, request, name):
    return text('Hello I have a decorator')

  def post(self, request, name):
    return text("Hello I also have a decorator")

app.add_route(ViewWithDecorator.as_view(), '/url')
```

But if you just want to decorator some functions and not all functions, you can use as followed.

```python
class ViewWithSomeDecorator(HTTPMethodView):

    @staticmethod
    @some_decorator_here
    def get(request, name):
        return text("Hello I have a decorator")

    def post(self, request, name):
        return text("Hello I don't have any decorators")
```

## URL Building

If you wish to build a URL for an HTTPMethodView, remember that the class name will be the endpoint
that you will pass into `url_for`. For example:

```python
@app.route('/')
def index(request):
    url = app.url_for('SpecialClassView')
    return redirect(url)


class SpecialClassView(HTTPMethodView):
    def get(self, request):
        return text('Hello from the Special Class View!')


app.add_route(SpecialClassView.as_view(), '/special_class_view')
```


## Using CompositionView

As an alternative to the `HTTPMethodView`, you can use `CompositionView` to
move handler functions outside of the view class.

Handler functions for each supported HTTP method are defined elsewhere in the
source, and then added to the view using the `CompositionView.add` method. The
first parameter is a list of HTTP methods to handle (e.g. `['GET', 'POST']`),
and the second is the handler function. The following example shows
`CompositionView` usage with both an external handler function and an inline
lambda:

```python
from sanic import Sanic
from sanic.views import CompositionView
from sanic.response import text

app = Sanic(__name__)

def get_handler(request):
    return text('I am a get method')

view = CompositionView()
view.add(['GET'], get_handler)
view.add(['POST', 'PUT'], lambda request: text('I am a post/put method'))

# Use the new view to handle requests to the base URL
app.add_route(view, '/')
```

Note: currently you cannot build a URL for a CompositionView using `url_for`.
