# 请求(Request)

查看 API 文档： [sanic.request](/api/sanic.request)

:class: `sanic.request.Request` 实例的参数中包含大量有用的信息。 详情请参阅[API 文档](https://sanic.readthedocs.io/)。

正如我们在 [响应函数(Handlers)](./handlers) 部分中所看到的，路由处理器的第一个参数通常是 :class:`sanic.request.Request` 对象。 因为Sanic是一个异步框架，处理器将在一个 [`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) 内运行，并由事件循环（event loop）调度。 这意味着处理器将在一个隔离的上下文中执行，并且请求对象（Rquest）将是该处理器任务所独有的。

.. column::

```
按照惯例，参数被命名为`request`，但您可以根据需要随意命名。参数的名称并不重要。以下两个处理器的写法都是有效的。
```

.. column::

````
```python
@app.get("/foo")
async def typical_use_case(request):
    return text("I said foo!")
```

```python
@app.get("/foo")
async def atypical_use_case(req):
    return text("I said foo!")
```
````

.. column::

```
对请求的对象添加一个注解变的超级简单
```

.. column::

````
```python
from sanic.request import Request
from sanic.response import text

@app.get("/typed")
async def typed_handler(request: Request):
    return text("Done.")
```
````

.. tip:: 提示

```
为了方便起见，假设您正在使用现代IDE，您应当利用类型注解来辅助完成代码提示和文档编写。这对于使用request对象时尤其有帮助，因为它具有**许多**属性和方法。

若要查看所有可用属性和方法的完整列表，请参阅 [API 文档](/api/sanic.request).
```

## 请求体(Body)

`Request`对象允许您用以下几种不同的方式访问请求体的内容。

### JSON（json数据）

.. column::

```
**参数**: `request.json`  
**描述**: 已解析的 JSON 对象
```

.. column::

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}'
```

```python
>>> print(request.json)
{'foo': 'bar'}
```
````

### Raw（原始数据）

.. column::

```
**参数**: `request.body`  
**描述**: 请求正文中的原始字节
```

.. column::

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}'
```

```python
>>> print(request.body)
b'{"foo": "bar"}'
```
````

### Form（表单数据）

.. column::

```
**参数**: `request.form`  
**描述**: 表单数据

.. tip:: 额外补充

`request.form`对象是几种类型之一，它是一个字典，其中每个值都是一个列表。这是因为HTTP协议允许单个键被重复用来发送多个值。

大多数情况下，您可能希望使用`.get()`方法访问第一个元素而不是一个列表。如果您确实需要所有项的列表，您可以使用`.getlist()`方法。
```

.. column::

````
```bash
$ curl localhost:8000 -d 'foo=bar'
```

```python
>>> print(request.body)
b'foo=bar'

>>> print(request.form)
{'foo': ['bar']}

>>> print(request.form.get("foo"))
bar

>>> print(request.form.getlist("foo"))
['bar']
```
````

### Uploaded（上传文件）

.. column::

```
**参数**: `request.files`  
**描述**: 上传给服务器的文件数据

.. tip:: 额外提示

`request.files`对象是一种字典类型的实例，其中每个值都是一个列表。这是由于HTTP协议允许单个键被重复用来发送多个文件。

大多数时候，您可能希望通过`.get()`方法获取并访问第一个文件对象而非整个列表。如果您确实需要获取所有文件项的列表，您可以使用`.getlist()`方法。
```

.. column::

````
```bash
$ curl -F 'my_file=@/path/to/TEST' http://localhost:8000
```

```python
>>> print(request.body)
b'--------------------------cb566ad845ad02d3\r\nContent-Disposition: form-data; name="my_file"; filename="TEST"\r\nContent-Type: application/octet-stream\r\n\r\nhello\n\r\n--------------------------cb566ad845ad02d3--\r\n'

>>> print(request.files)
{'my_file': [File(type='application/octet-stream', body=b'hello\n', name='TEST')]}

>>> print(request.files.get("my_file"))
File(type='application/octet-stream', body=b'hello\n', name='TEST')

>>> print(request.files.getlist("my_file"))
[File(type='application/octet-stream', body=b'hello\n', name='TEST')]
```
````

## 上下文(Context)

### 请求上下文内容

request.ctx 对象是存储请求相关信息的地方。 它仅在请求的生命周期内存在，并且是针对该请求独一无二的。

这与app.ctx对象形成了对比，后者是在所有请求间共享的。 务必注意不要混淆它们！

默认情况下，request.ctx对象是一个SimpleNamespace对象，允许您在其上设置任意属性。 Sanic不会对此对象做任何用途，因此您可以自由地按照需要使用它，无需担心名称冲突问题。

````python

### 典型应用场景

这种做法常用于存储诸如认证用户详情之类的数据。我们将在后面的[middleware](./middleware.md)部分详细介绍，但这里先给出一个简单的示例。

```python
@app.on_request
async def run_before_handler(request):
    request.ctx.user = await fetch_user_by_token(request.token)

@app.route('/hi')
async def hi_my_name_is(request):
    if not request.ctx.user:
        return text("Hmm... I don't know you)
    return text(f"Hi, my name is {request.ctx.user.name}")
````

如您所见，`request.ctx`对象是一个很好的位置，用于存储您需要在多个处理器中访问的信息，从而使您的代码更加遵循DRY原则（Don't Repeat Yourself），也更易于维护。 但是，正如我们在中间件章节中将要学习的那样，您还可以使用它来存储在一个中间件中产生的信息，这些信息将在另一个中间件中使用。

### 连接上下文(Connection context)

.. column::

```

很多时候，您的API需要为同一客户端并发（或连续）处理多个请求。这种情况在需要查询多个端点以获取数据的渐进式Web应用程序中经常发生。

HTTP协议要求通过使用 [保持连接头](../deployment/configuration.md#keep-alive-timeout).来减轻由连接引起的开销时间。

当多个请求共享单个连接时，Sanic提供了一个上下文对象，允许这些请求共享状态。
```

.. column::

````
```python
@app.on_request
async def increment_foo(request):
    if not hasattr(request.conn_info.ctx, "foo"):
        request.conn_info.ctx.foo = 0
    request.conn_info.ctx.foo += 1

@app.get("/")
async def count_foo(request):
    return text(f"request.conn_info.ctx.foo={request.conn_info.ctx.foo}")
```

```bash
$ curl localhost:8000 localhost:8000 localhost:8000
request.conn_info.ctx.foo=1
request.conn_info.ctx.foo=2
request.conn_info.ctx.foo=3
```
````

.. warning::

```
虽然对于通过单一HTTP连接在请求之间存储信息而言，这是一个便利的位置，但不要假定单个连接上的所有请求都来自同一个最终用户。这是因为HTTP代理和负载均衡器可能会将多个连接复用到单个到服务器的连接中。

**切勿** 使用此机制来存储关于单个用户的信息。为此目的应使用`request.ctx`对象。
```

### 自定义请求对象(Custom Request Objects)

正如在[自定义app](./app.md#custom-requests)部分讨论的那样，您可以创建:class:`sanic.request.Request`的一个子类，以向请求对象添加更多功能。 这对于添加专属于您的应用程序的额外属性或方法非常有用。

.. column::

```
例如，设想您的应用程序发送了一个包含用户ID的自定义头部。您可以创建一个自定义请求对象，它将解析该头部并将用户ID为您存储起来。
```

.. column::

````
```python
from sanic import Sanic, Request

class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = self.headers.get("X-User-ID")

app = Sanic("Example", request_class=CustomRequest)
```
````

.. column::

```
现在，您可以在处理器中访问 `user_id` 属性。
```

.. 列:

````
```python
@app.route("/")
async def handler(request: CustomRequest):
    return text(f"User ID: {request.user_id}")
```
````

### 自定义请求上下文（Custom Request Context）

默认情况下，请求上下文(`request.ctx`) 是一个[`Simpenamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 对象，允许您在它上设置任意属性。 尽管在整个应用程序中重用这一逻辑非常有助于提高效率，但在开发过程中可能会遇到困难，因为IDE无法知道有哪些可用的属性。

为了解决这个问题，您可以创建一个自定义请求上下文对象，以替代默认的`SimpleNamespace`。 这样您可以在上下文对象中添加类型提示，并使其在您的IDE中可用。

.. column::

```
首先，通过继承 :class:`sanic.request.Request` 类来创建自定义请求类型。接着，您需要添加一个 `make_context()` 方法，该方法返回您的自定义上下文对象实例。*注意：`make_context` 方法应为静态方法。*
```

.. column::

````
```python
from sanic import Sanic, Request
from types import SimpleNamespace

class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx.user_id = self.headers.get("X-User-ID")

    @staticmethod
    def make_context() -> CustomContext:
        return CustomContext()

@dataclass
class CustomContext:
    user_id: str = None
```
````

.. note:: 注意

```
这是一个Sanic高级用户的特性，使得在大型代码库中拥有类型化的请求上下文对象变得极为方便。当然这不是必需的，但会非常有帮助。
```

_添加于 v23.6_

## 路径参数（Parameters）

.. column::

```
从路径参数中提取的值会被注入到处理器作为参数，更具体地说，是以关键字参数的形式。关于这一点，在[路由章节](./routing.md)中有更多详细信息。
```

.. column::

````
```python
@app.route('/tag/<tag>')
async def tag_handler(request, tag):
    return text("Tag - {}".format(tag))

# or, explicitly as keyword arguments
@app.route('/tag/<tag>')
async def tag_handler(request, *, tag):
    return text("Tag - {}".format(tag))
```
````

## 查询参数（Arguments）

在 "request" 实例上有两个属性来获取查询参数：

- `request.args`
- `requery_args`

这些让您能够从请求路径中访问查询参数（URL中`?`号后面的部分）。

### 典型应用场景

在大多数情况下，您将想使用 `request.args` 对象来访问查询参数。 它是解析后的查询字符串，存储为一个字典。

迄今为止，这是最常见的模式。

.. column::

```
考虑这样一个示例：我们有一个带有`q`参数的`/search`路由入口，我们希望使用这个参数来进行搜索。
```

.. column::

````
```python
@app.get("/search")
async def search(request):
   query = request.args.get("q")
    if not query:
        return text("No query string provided")
    return text(f"Searching for: {query}")
```
````

### 解析查询字符串

然而，在某些情况下，您可能希望以原始字符串形式或元组列表形式访问查询字符串。 为此，您可以使用`request.query_string` 和 `request.query_args` 属性。

此外还应注意，HTTP协议允许单个键拥有多个值。 虽然`request.args`看起来像一个常规字典，但实际上它是一种特殊类型，允许单个键对应多个值。 您可以通过`request.args.getlist()`方法来访问这些多个值。

- `request.query_string` - 原始查询字符串
- `request.query_args` - 解析成元组的查询字符串
- `request.args` - 解析成字典的查询字符串
  - `request.args.get()` - 获取查询参数中对应key的第一个值 (像普通字典一样)
  - `request.args.getlist()` - 取查询参数中对应key的所有值（返回一个数组）

```sh
curl "http://localhost:8000?key1=val1&key2=val2&key1=val3"
```

```python
>>> print(request.args)
{'key1': ['val1', 'val3'], 'key2': ['val2']}

>>> print(request.args.get("key1"))
val1

>>> print(request.args.getlist("key1"))
['val1', 'val3']

>>> print(request.query_args)
[('key1', 'val1'), ('key2', 'val2'), ('key1', 'val3')]

>>> print(request.query_string)
key1=val1&key2=val2&key1=val3

```

.. tip:: 额外提示

```
`request.args`对象是一种字典类型的实例，其中每个值都是一个列表。这是由于HTTP协议允许单个参数名多次出现以传输多个值。

大多数情况下，您可能希望使用`.get()`方法来获取并访问第一个元素而非整个列表。但如果确实需要获取所有项目组成的列表，您可以使用`.getlist()`方法。
```

## 获取当前请求对象

有时您可能会发现在应用程序中的某个位置无法直接访问当前请求， 比如在日志格式化时。 此时，您可以使用Request.get_current()来获取当前请求（如果需要的话）。

请记住，请求对象只限于运行处理器的那个单独的 [`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) 内。 如果您不在那个任务中，就不会存在请求对象。

```python
import logging

from sanic import Request, Sanic, json
from sanic.exceptions import SanicException
from sanic.log import LOGGING_CONFIG_DEFAULTS

LOGGING_FORMAT = (
    "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
    "%(request_id)s %(request)s %(message)s %(status)d %(byte)d"
)

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.request_id = ""

    try:
        request = Request.get_current()
    except SanicException:
        ...
    else:
        record.request_id = str(request.id)

    return record

logging.setLogRecordFactory(record_factory)


LOGGING_CONFIG_DEFAULTS["formatters"]["access"]["format"] = LOGGING_FORMAT
app = Sanic("Example", log_config=LOGGING_CONFIG_DEFAULTS)
```

在此示例中，我们正在将`request.id`添加到每个访问日志消息中。

_添加于 v22.6_
