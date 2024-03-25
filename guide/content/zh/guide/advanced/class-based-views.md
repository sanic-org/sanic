# 基于类的视图(Class Based Views)

## 为什么要使用它？

.. 列:

```
### 问题所在

设计 API 时的常见思路是在根据 HTTP 请求方法的不同而产生不同响应的同一端点上实现多种功能。

虽然这两种选项都可以，但它们并不是良好的设计思维，随着你的项目的发展，可能很难长期维护。
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
### 解决方案

基于类的视图只是实现请求响应行为的类。 它们提供了一种在同一端点划分不同 HTTP 请求类型的处理方法。
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

## 定义一个视图

基于类的视图应当继承 :class:`sanic.views.HTTPMethodView`。 然后，您可以使用相应 HTTP 方法的名称来实现类方法。 如果收到一个没有定义方法的请求，将生成一个 \`405: Method not allowed' 响应。

.. 列:

```
要在一个 URL 端点注册一个基于类的视图，需要使用 `app.add_route` 方法。 第一个参数应该是实现了`as_view`方法的定义类，第二个参数应该是 URL 端点。

可用的方法是：

- get
- post
- put
- patch
- delete
- head
- options
```

.. 列:

````
```python
from sanic.views import HTTPMethodView
from sanic.response import text

class SimpleView(HTTPMethodView):

  def get(self, request):
      return text("I am get method")

  # 也支持 async 语法
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
您可以完全按照[路由部分](/guide/basics/routing.md)中讨论的方式使用路径参数。
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

## 装饰器

正如[装饰器部分](/guide/best-practices/decorators.md)中所讨论的，您通常需要使用装饰器向端点添加功能。 您与 CBV 有两个选项：

1. 应用于视图中的 _全部_ HTTP 方法
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
