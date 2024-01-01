# 基于类的视图(Class Based Views)

## 为什么要使用它？

.. 列:

```
### 问题

设计一个 API 时常见的模式是在依赖HTTP 方法的同一个端点上具有多个功能。

虽然这两种选项都起作用，但它们并不是良好的设计做法，随着你的项目的发展，可能很难长期维持。
```

.. 列:

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

.. 列:

```
### 解析器

基于类的视图只是实现回应行为的类类。 它们为在同一端点将不同HTTP请求类型的处理分割开来提供了一条途径。
```

.. 列:

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

## 定义视图(Defining a view)

A class-based view should subclass :class:`sanic.views.HTTPMethodView`. 然后您可以执行具有相应的 HTTP 方法名称的类方法。 如果收到一个没有定义方法的请求，将生成一个 \`405: 方法不允许' 响应。

.. 列:

```
要在端点注册一个基于类的视图，将使用 `app.add_route` 方法。 第一个参数应该是使用`as_view`方法的定义类，第二个参数应该是URL终点。

可用的方法是：

- get
- 发表
- 放置
- 补丁
- 删除
- 首长
- 选项
```

.. 列:

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

## 路径参数

.. 列:

```
您可以使用路径参数就像[路由部分](/guide/basics/routing.md)中讨论过的路径参数。
```

.. 列:

````
```python
class NameView(HTTPMethodView):

  def get(self, request, name):
    return text("Hello {}".format (name))

app.add_route(NameView.asp.as_view(), "/<name>")
```
````

## 装饰符

正如在[装饰物部分](/guide/best practices/decorators.md)中所讨论的那样，您常常需要在终点中添加使用装饰物的功能。 您与 CBV 有两个选项：

1. 应用于视图中的 _all_ HTTP 方法
2. 单独应用于视图中的 HTTP 方法

让我们看看这些选项是什么样子：

.. 列:

```
### 应用于所有方法

如果您想要将任何装饰符添加到类中，您可以设置 "装饰符" 类变量。 当调用`as_view`时，这些将应用于该类。
```

.. 列:

````
```python
class ViewWidDecorator(HTTPMethodView):
  decorators = [some_decorator_here]

  def get(self, request, pass). 姓名:
    退货文本("Hello I have a decorator")

  def post(self, 请求，名称：
    return text("Hello I also a Decorator")

app dd_route(ViewWidDecorator.as_view(), "/url")
```
````

.. 列:

```
### 应用于个别方法

但是如果你只想装饰一些方法而不是所有方法，你可以如这里所示。
```

.. 列:

````
```python
class Viewwitwithout Decorator(HTTPMethodView):

    @static方法
    @some_decorator_here
    def get(request 姓名:
        退货文本("Hello I have a decorator")

    def post(self, 请求 姓名：
        return text("Hello I no some decorators")

    @some_decorator_here
    def patch(self, 请求，名称：
        返回文本("Hello I have a decorator")
```
````

## 正在生成 URL

.. 列:

```
这就像[生成任何其它URL](/guide/basics/routing.md#generating-a-url)一样，只是类名称是端点的一部分。
```

.. 列:

````
```python
@app.route("/")
def index(request):
    url = app. rl_for("SpecialClassView")
    return redirect(url)

class SpecialClassView(HTTPMethodView):
    def get(self, 请求:
        返回文本("您好，来自特殊类视图!

应用。 dd_route(SpecialClassView.as_view), "/special_class_view")
```
````
