# 请求

查看 API 文档： [sanic.request](/api/sanic.request)

:class: `sanic.request.Request` 实例包含了许多有用的信息，这些信息可以在其参数中获得。 详情请参阅[API 文档](https://sanic.readthedocs.io/)。

正如我们在 [handlers](./handlers) 部分中所看到的，路由处理器的第一个参数通常是 :class:`sanic.request.Request` 对象。 因为Sanic是一个异步框架，处理器将在一个 [`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) 内运行，并由事件循环调度。 这意味着处理器将在一个隔离的上下文中执行，并且请求对象对于该处理器是唯一的。

.. 列:

```
按照惯例，参数被命名为`request`，但您可以根据需要随意命名。参数的名称并不重要。以下两个处理器的写法都是有效的。
```

.. 列:

````
```python
@app.get("/foo")
async def typical_use_case(request):
    return text("我说了！")
```

```python
@app. et("/foo")
async def atypical_use_case(req):
    return text("我说了！")
```
````

.. 列:

```
注释请求对象超级简单。
    
```

.. 列:

````
```python
来自sanic.request
from sanic.request import text

@app.get("/输入")
async def typed_handler(request: Request):
    return text("完成")
```
````

.. tip::

```
为了您的方便，假设您正在使用现代的集成开发环境（IDE），您应该利用类型注解来帮助代码自动完成和文档编写。这在使用request对象时尤为有用，因为它具有**许多**属性和方法。

要查看可用属性和方法的完整列表，请参阅[API文档]
(/api/sanic.request)。
```

## 正文内容

`Request`对象允许您以几种不同的方式访问请求体的内容。

### JSON

.. 列:

```
**参数**: `request.json`  
**Description**: 已解析的 JSON 对象
```

.. 列:

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}'
```

```python
>>> print(request.json)
{'foo': 'bar'}
```
````

### 原始数据

.. 列:

```
**参数**: `request.body`  
**描述**: 请求正文中的原始字节
```

.. 列:

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}"
``'

```python
>> print(request.body)
b'{"foo": "bar"}"
```
````

### 形式

.. 列:

```
**Parameter**: `request.form`  
**Description**: The form data

.. tip:: FYI

    The `request.form` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

    Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.
```

.. 列:

````
```bash
$ curl localhost:8000 -d 'foo=bar'
```

```python
>> > print(request.body)
b'foo=bar'

>> Print(request). orm)
{'foot': ['bar']}

>> Print(request.form.get("foo"))
bar

>> Print(request.form.getlist("foo"))
['bar']
```
````

### 上传完成

.. 列:

```
**Parameter**: `request.files`  
**Description**: The files uploaded to the server

.. tip:: FYI

    The `request.files` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

    Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.
```

.. 列:

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

## 二. 背景

### 请求上下文内容

`request.ctx`对象是您的游戏场，可以存储您需要的关于请求的任何信息。 这只适用于请求的持续时间，是请求独有的。

这可以与所有请求共享的 `app.ctx` 对象混合。 请注意不要混淆他们！

默认情况下，`request.ctx`对象是 `SimpleNamespace`，允许您在它上设置任意属性。 Sanic将不会为任何东西使用此对象，所以你可以自由地使用它，不管你想不必担心名称冲突。

````python

### Typical use case

This is often used to store items like authenticated user details. We will get more into [middleware](./middleware.md) later, but here is a simple example.

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

正如你可以看到的那样，`请求'。 tx`对象是一个很好的地方来存储您需要在多个处理程序中访问的信息，使您的代码更加DRY和更容易维护。 但是，我们将在[中间件部分](./中间件部分)中学习。 您也可以使用它来存储来自一个中间件的信息，这些信息将用于另一个中间件中。

### 连接环境

.. 列:

```
Often times your API will need to serve multiple concurrent (or consecutive) requests to the same client. This happens, for example, very often with progressive web apps that need to query multiple endpoints to get data.

The HTTP protocol calls for an easing of overhead time caused by the connection with the use of [keep alive headers](../deployment/configuration.md#keep-alive-timeout).

When multiple requests share a single connection, Sanic provides a context object to allow those requests to share state.
```

.. 列:

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

.. 警告：:

```
虽然这看起来是一个方便的地方来存储通过单个HTTP连接请求之间的信息。 不假设单个连接上的所有请求来自单个终端用户。 这是因为HTTP 代理和负载均衡器可以将多个多个连接连接到您的服务器。

**DO Not** 使用它来存储有关单个用户的信息。为此使用 `request.ctx` 对象。
```

### 自定义请求对象

As dicussed in [application customization](./app.md#custom-requests), you can create a subclass of :class:`sanic.request.Request` to add additional functionality to the request object. 这有助于添加特定于您应用程序的附加属性或方法。

.. 列:

```
例如，请想象您的应用程序发送一个包含用户ID的自定义标题。 您可以创建一个自定义请求对象，解析该标头并为您存储用户 ID。
```

.. 列:

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

.. 列:

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

### 自定义请求内容

默认情况下，请求上下文(`request.ctx`) 是一个[`Simpenamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 对象，允许您在它上设置任意属性。 虽然这对于在您的应用程序中重新使用逻辑非常有用， 在发展经验中可能很困难，因为IDE将不知道有哪些属性。

为了帮助解决这个问题，您可以创建一个将被使用的自定义请求上下文对象，而不是默认的\`SimpleNamespace'。 这可以让您在上下文对象中添加提示并让它们在您的 IDE 中可用。

.. 列:

```
Start by subclassing the :class:`sanic.request.Request` class to create a custom request type. Then, you will need to add a `make_context()` method that returns an instance of your custom context object. *NOTE: the `make_context` method should be a static method.*
```

.. 列:

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

.. 注：

```
这是一个神秘的电源用户功能，它使得在大代码折叠中具有请求上下文对象变得非常方便。 当然，这是不需要的，但可能很有帮助。
```

_添加于 v23.6_

## 参数

.. 列:

```
从路径参数中提取的值作为参数注入到处理程序中，或更具体地作为关键字参数注入。 [路由部分](./routing.md) 中有更多关于这一点的详细信息。
```

.. 列:

````
```python
@app.route('/tag/<tag>')
Async def tag_handler(请求，标签):
    return text("Tag - {}"。 ormat(标签))

# 或明确作为关键词参数
@app。 oute('/tag/<tag>')
async def tag_handler(请求, *, 标签):
    return text("Tag - {}".format (tag))
```
````

## 参数

在 "request" 实例上有两个属性来获取查询参数：

- `request.args`
- `requery_args`

这些允许您访问请求路径中的查询参数(URL中`?`后面的部分)。

### 典型的使用情况

在大多数情况下，您将想使用 `request.args` 对象来访问查询参数。 这将是解析的查询字符串。

这是迄今最常见的模式。

.. 列:

```
考虑一个我们想要用来搜索某些东西的 `/search` 端点的例子。
```

.. 列:

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

但有时您可能想要以原始字符串或导管列表的形式访问查询字符串。 为此，您可以使用 `request.query_string` 和 `request.query_args` 属性。

还应该注意的是，HTTP允许单个键的多个值。 虽然`request.args`看起来像一个常规字典，但它实际上是一种特殊的类型，允许一个单个键的多个值。 您可以使用 `request.args.getlist()` 方法访问这个。

- `requery_string` - 原始查询字符串
- `requery_args` - 解析的查询字符串为导游列表
- `request.args` - 解析的查询字符串为 _特殊_ 字典
  - `request.args.get()` - 获取关键字的第一个值 (像普通字典一样)
  - `request.args.getlist()` - 获取所有键值

```sh
curl "http://localhost:8000?key1=val1&key2=val2&key1=val3"
```

```python
>>> Print(request.args)
{'key1': ['val1', 'val3'], 'key2': ['val2']}

>> print(request.args.get("key1"))
val1

>> print(request.args. etlist("key1"))
['val1', 'val3']

>> Print(request.query_args)
[('key1', 'val1'), ('key2', 'val2'), ('key1', 'val3')]

>> > 打印(request.query_string)
key1=val1&key2=val2&key1=val3

```

.. tip:: FYI

```
"request.args"对象是几种类型的字典之一，每个值都是一个列表。 这是因为HTTP允许重用单个键来发送多个值。  

大多数您想使用 `.get()` 方法访问第一个元素而不是列表的时间。 如果您确实想要列出所有项目，您可以使用 `.getlist()` 。
```

## 当前请求获取

有时您可能会在无法访问的地方发现您需要访问您的应用程序中的当前请求。 一个典型的例子可能是 `logging` 格式。 您可以使用 `Request.get_current()` 方法获取当前请求(如果有)。

记住，请求对象仅限于正在运行处理程序的单个[[asyncio.Task\`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task)。 如果你没有执行这项任务，没有请求对象。

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
