# Class Based Views

## Why use them?

.. column::

    ### The problem

    A common pattern when designing an API is to have multiple functionality on the same endpoint that depends upon the HTTP method.

    While both of these options work, they are not good design practices and may be hard to maintain over time as your project grows.

.. column::

    ```python
    @app.get("/foo")
    async def foo_get(request):
        ...

    @app.post("/foo")
    async def foo_post(request):
        ...

    @app.put("/foo")
    async def foo_put(request):
        ...

    @app.route("/bar", methods=["GET", "POST", "PATCH"])
    async def bar(request):
        if request.method == "GET":
            ...

        elif request.method == "POST":
            ...
            
        elif request.method == "PATCH":
            ...
    ```


.. column::

    ### The solution

    Class-based views are simply classes that implement response behavior to requests. They provide a way to compartmentalize handling of different HTTP request types at the same endpoint.

.. column::

    ```python
    from sanic.views import HTTPMethodView

    class FooBar(HTTPMethodView):
        async def get(self, request):
            ...
        
        async def post(self, request):
            ...
        
        async def put(self, request):
            ...

    app.add_route(FooBar.as_view(), "/foobar")
    ```

## Defining a view

A class-based view should subclass `HTTPMethodView`. You can then implement class methods with the name of the corresponding HTTP method. If a request is received that has no defined method, a `405: Method not allowed` response will be generated.

.. column::

    To register a class-based view on an endpoint, the `app.add_route` method is used. The first argument should be the defined class with the method `as_view` invoked, and the second should be the URL endpoint.

    The available methods are:

    - get
    - post
    - put
    - patch
    - delete
    - head
    - options

.. column::

    ```python
    from sanic.views import HTTPMethodView
    from sanic.response import text

    class SimpleView(HTTPMethodView):

      def get(self, request):
          return text("I am get method")

      # You can also use async syntax
      async def post(self, request):
          return text("I am post method")

      def put(self, request):
          return text("I am put method")

      def patch(self, request):
          return text("I am patch method")

      def delete(self, request):
          return text("I am delete method")

    app.add_route(SimpleView.as_view(), "/")
    ```

## Path parameters

.. column::

    You can use path parameters exactly as discussed in [the routing section](/guide/basics/routing.md).

.. column::

    ```python
    class NameView(HTTPMethodView):

      def get(self, request, name):
        return text("Hello {}".format(name))

    app.add_route(NameView.as_view(), "/<name>")
    ```

## Decorators

As discussed in [the decorators section](/guide/best-practices/decorators.md), often you will need to add functionality to endpoints with the use of decorators. You have two options with CBV:

1. Apply to _all_ HTTP methods in the view
2. Apply individually to HTTP methods in the view

Let's see what the options look like:

.. column::

    ### Apply to all methods

    If you want to add any decorators to the class, you can set the `decorators` class variable. These will be applied to the class when `as_view` is called.

.. column::

    ```python
    class ViewWithDecorator(HTTPMethodView):
      decorators = [some_decorator_here]

      def get(self, request, name):
        return text("Hello I have a decorator")

      def post(self, request, name):
        return text("Hello I also have a decorator")

    app.add_route(ViewWithDecorator.as_view(), "/url")
    ```


.. column::

    ### Apply to individual methods

    But if you just want to decorate some methods and not all methods, you can as shown here.

.. column::

    ```python
    class ViewWithSomeDecorator(HTTPMethodView):

        @staticmethod
        @some_decorator_here
        def get(request, name):
            return text("Hello I have a decorator")

        def post(self, request, name):
            return text("Hello I do not have any decorators")

        @some_decorator_here
        def patch(self, request, name):
            return text("Hello I have a decorator")
    ```

## Generating a URL

.. column::

    This works just like [generating any other URL](/guide/basics/routing.md#generating-a-url), except that the class name is a part of the endpoint.

.. column::

    ```python
    @app.route("/")
    def index(request):
        url = app.url_for("SpecialClassView")
        return redirect(url)

    class SpecialClassView(HTTPMethodView):
        def get(self, request):
            return text("Hello from the Special Class View!")

    app.add_route(SpecialClassView.as_view(), "/special_class_view")
    ```

