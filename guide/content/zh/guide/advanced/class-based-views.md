# 基于类的视图(Class Based Views)

## 为什么要使用它？

.. column::

```
### 问题所在

设计API时常见的一个模式是在同一路由入口上根据HTTP方法实现多种功能。

虽然这两种方案都能正常工作，但它们并不是良好的设计实践，并且随着项目的增长，可能会随着时间推移变得难以维护。
```

.. column::

````
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
````

.. column::

```
### 解决方案

基于类的视图本质上是实现响应请求行为的类。它们提供了一种方式，在同一路由入口上将不同类型的HTTP请求处理方式进行模块化管理。
```

.. column::

````
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
````

## 定义视图 (Defining a view)

一个基于类的视图应继承自  :class:`sanic.views.HTTPMethodView`. 然后，您可以实现与相应HTTP方法同名的类方法。 如果接收到的方法未定义的请求，将生成`405: Method not allowed`的响应。

.. column::

```
在路由入口上注册基于类的视图时，通常使用 `app.add_route` 方法。第一个参数应当是已定义的类，并调用其 `as_view` 方法，第二个参数则是该视图要绑定的URL路由入口。

可用的方法包括：

- get
- post
- put
- patch
- delete
- head
- options
```

.. column::

````
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
````

## 路径参数（Path parameters）

.. column::

```
您可以完全按照[路由部分](/zh/guide/basics/routing.md)中讨论的方式来使用路径参数。
```

.. column::

````
```python
class NameView(HTTPMethodView):

  def get(self, request, name):
    return text("Hello {}".format(name))

app.add_route(NameView.as_view(), "/<name>")
```
````

## 装饰器（Decorators）

正如在[装饰器](/zh/guide/best-practices/decorators.md)部分讨论的那样，您经常需要通过使用装饰器为路由入口添加功能。 对于基于类的视图（CBV），有两种选择：

1. 应用于视图中的**所有**HTTP方法
2. 分别应用于视图中的各个HTTP方法

让我们来看一下这两种选项的样子：

.. column::

```
### 应用于视图中的所有HTTP方法

若要向此类添加任何装饰器，您可以设置 `decorators` 类变量。当调用 `as_view` 时，这些装饰器将会应用于此类。
```

.. column::

````
```python
class ViewWithDecorator(HTTPMethodView):
  decorators = [some_decorator_here]

  def get(self, request, name):
    return text("Hello I have a decorator")

  def post(self, request, name):
    return text("Hello I also have a decorator")

app.add_route(ViewWithDecorator.as_view(), "/url")
```
````

.. column::

```
### 分别应用于视图中的各个HTTP方法

但是，如果您只想装饰某些方法而不是所有方法，则可以如以下所示操作。
```

.. column::

````
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
````

## 动态路由(Generating a URL)

.. column::

```
这就像[生成任何其他URL](/zh/guide/basics/routing.md#generating-a-url)一样工作，只不过类名是路由入口的一部分。
```

.. column::

````
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
````

