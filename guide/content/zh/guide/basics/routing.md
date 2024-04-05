# 路由

.. 列:

```
So far we have seen a lot of this decorator in different forms.

But what is it? And how do we use it?
```

.. 列:

````
```python
@app.route("/stairway")
    ...

@app.get("/to")
    ...

@app.post("/heaven")
    ...
```
````

## 添加路由

.. 列:

```
The most basic way to wire up a handler to an endpoint is with `app.add_route()`.

See [API docs](https://sanic.readthedocs.io/en/stable/sanic/api_reference.html#sanic.app.Sanic.url_for) for more details.
```

.. 列:

````
```python
async def 处理器(请求):
    return text("OK")

app.add_route(handler, "/test")
```
````

.. 列:

```
默认情况下，路由是可用的 HTTP `GET` 调用。您可以更改处理程序来响应一个或多个HTTP方法。
```

.. 列:

````
```python
app.add_route(
    handler,
    '/test',
    meths=["POST", "PUT",
)
```
````

.. 列:

```
使用装饰符语法, 前面的示例与此相同。
```

.. 列:

````
```python
@app.route('/test', methods=["POST", "PUT"])
async def handler(request):
    return text('OK')
```
````

## HTTP 方法

每种标准HTTP方法都有一个方便装饰器。

### 获取

```python
@app.get('/test')
async def 处理器(请求):
    返回文本('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTPMethods/GET)

### 帖子

```python
@app.post('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTPMethods/POST)

### 弹出

```python
@app.put('/test')
async def 处理器(请求):
    返回文本('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/PUT)

### PATCH

```python
@app.patch('/test')
async def 处理器(请求):
    返回文本('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTPMethods/PATCH)

### 删除

```python
@app.delete('/test')
async def 处理器(请求):
    返回文本('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTPMethods/DELETE)

### 黑色

```python
@app.head('/test')
async def 处理器(请求):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTPMethods/HEAD)

### 选项

```python
@app.options('/test')
async def 处理器(请求):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS)

.. 警告：:

````
默认情况下，Sanic **只**在不安全的 HTTP 方法上消耗传入的请求机构：“POST`、`PUT`、`PATCH`、`DELETE`”。 如果您想要在 HTTP 请求中在任何其他方法上接收数据，， 您将需要做以下两个选项之一：

**选项#1 - 告诉Sanic使用`ignore_body`**
```python
@app。 赤道("/path", ignore_body=False)
async def handler(_):
    ...
```

**Option #2 - 手动使用 `receive_body`**
```python
@app. et("/path")
async def 处理器(请求: 请求):
    等待request.receive_body()
```
````

## 路径参数

.. 列:

```
Sanic 允许模式匹配，也允许从 URL 路径中提取值。然后这些参数作为关键词参数在路由处理器中注入。
```

.. 列:

````
```python
@app.get("/tag/<tag>")
async def tag_handler(请求，标签):
    return text("Tag - {}".form(标签))
```
````

.. 列:

```
您可以声明参数类型。匹配时将强制执行，并且还将输入变量。
```

.. 列:

````
```python
@app.get("/fo/<foo_id:uuid>")
async def uuid_handler(request, foo_id: UUID):
    return text("UUUID - {}".format (fo_id))
```
````

.. 列:

```
对于一些标准类型，如`str`、`int`和`UUID`，Sanic可以从函数签名中推断路径参数类型。 这意味着可能并非总是需要在路径参数定义中包含类型。
```

.. 列:

````
```python
@app。 et("/foo/<foo_id>") # 路径参数
async def uuid_handler不存在:uuid (请求) foo_id: UUID:
    return text("UUID - {}" ormat(fo_id))
```
````

### 支持的类型

### `str`

.. 列:

```
**Regular expression applied**: `r"[^/]+"`  
**Cast type**: `str`  
**Example matches**:  

- `/path/to/Bob`
- `/path/to/Python%203`

Beginning in v22.3 `str` will *not* match on empty strings. See `strorempty` for this behavior.
```

.. 列:

````
```python
@app.route("/path/to/<foo:str>")
Async def 处理器(请求, foo: str):
    ...
```
````

### `strorempty`

.. 列:

```
**Regular expression applied**: `r"[^/]*"`  
**Cast type**: `str`  
**Example matches**:

- `/path/to/Bob`
- `/path/to/Python%203`
- `/path/to/`

Unlike the `str` path parameter type, `strorempty` can also match on an empty string path segment.

*Added in v22.3*
```

.. 列:

````
```python
@app.route("/path/to/<foo:strorempty>")
Async def 处理器(请求, foo: str):
    ...
```
````

### `int`

.. 列:

```
**正则表达式已应用**: `r"-?\d+"  
**Cast 类型**: `int`  
**示例匹配** :  

- `/path/to/10`
- `/path/to/-10`

_不匹配浮点, 十六进制, octal等_
```

.. 列:

````
```python
@app.route("/path/to/<foo:int>")
Async def 处理器(请求, foo: int):
    ...
```
````

### `float`

.. 列:

```
**正则表达式已应用**: `r"-?(?:\d+(?:\.\d*)?|\.\d+)"  
**投射类型**: `float`  
**示例匹配**:  

- `/path/to/10`
- `/path/to/-10`
- `/path/to/1.5`
```

.. 列:

````
```python
@app.route("/path/to/<foo:float>")
Async def 处理器(请求，foo: float):
    ...
```
````

### `alpha`

.. 列:

```
**正则表达式已应用**：`r'[A-Za-z]+"`  
**快速类型**：`str`  
**示例匹配**：  

- `/path/to/Bob`
- `/path/to/Python`

_不匹配数字， 或空格或其他特殊字符_
```

.. 列:

````
```python
@app.route("/path/to/<foo:alpha>")
Async def 处理器(请求, foo: str):
    ...
```
````

### `slug`

.. 列:

```
**正则表达式**：`r'[a-z0-9]+(?:-[a-z0-9]+)*"  
**快速类型**：`str`  
**示例匹配**：  

- `/path/to/some-news-story`
- `/path/to/or-has-digits-123`

*添加于v21.6*
```

.. 列:

````
```python
@app.route("/path/to/<article:slug>")
async def 处理器(请求，文章: str):
    ...
```
````

### `path`

.. 列:

```
**正则表达式已应用**: `r"[^/].*?"  
**快速类型**: `str`  
**示例匹配**:
- `/path/to/hello`
- `/path/to/hello.txt`
- `/path/to/hello/world.txt`
```

.. 列:

````
```python
@app.route("/path/to/<foo:path>")
Async def 处理器(请求, foo: str):
    ...
```
````

.. 警告：:

```
因为这将在`/`上匹配， 你应该仔细和彻底地测试你使用`path`的模式，这样他们就不会捕获打算用于另一端点的流量。 此外，根据您如何使用这种类型，您可能会在应用程序中创建一条横向脆弱性。 你的任务是保护你的终点不受这种影响。 但如果您需要帮助，请在我们的社区频道中寻求帮助:)
```

### `ymd`

.. 列:

```
**正则表达式已应用**: `r"^([12]\d{3}( 0[1-9]|1[0-2])-( 0[1-9]|[12]\d|3[01])""  
**Cast类型**: `datetime.  
**示例匹配**:  

- `/path/to/2021-03-28`
```

.. 列:

````
```python
@app.route("/path/to/<foo:ymd>")
Async def 处理程序(请求，foo: datetime.date):
    ...
```
````

### `uuid`

.. 列:

```
**Regular expression applied**: `r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}"`  
**Cast type**: `UUID`  
**Example matches**:  

- `/path/to/123a123a-a12a-1a1a-a1a1-1a12a1a12345`
```

.. 列:

````
```python
@app.route("/path/to/<foo:uuid>")
Async def 处理器(请求, foo: UUID):
    ...
```
````

### ext

.. 列:

```
**正则表达式**：n/a
**铸造类型**：*varies*
**示例匹配**：
```

.. 列:

````
```python
@app.route("/path/to/<foo:ext>")
Async def 处理程序(请求，foo: str, ext: str):
    ...
```
````

| 定义                                                       | 示例                                                          | 文件名      | 扩展                          |
| -------------------------------------------------------- | ----------------------------------------------------------- | -------- | --------------------------- |
| \file:ext                                | 页次                                                          | `"page"` | `"txt"`                     |
| \file:ext=jpg                            | jpg                                                         | `"cat"`  | \`"jpg""                    |
| \file:ext=jpg\\\|png\\\|gif\\\|svg | jpg                                                         | `"cat"`  | \`"jpg""                    |
| \<file=int:ext>                          | 123.txt                                     | `123`    | `"txt"`                     |
| \<file=int:ext=jpg\\|png\\|gif\\|svg> | 123.svg                                     | `123`    | `"svg"`                     |
| \<file=float:ext=tar.gz> | 3.14.tar.gz | `3.14`   | \`"tar.gz"" |

文件扩展名可以使用特殊的 `ext` 参数类型匹配。 它使用特殊格式，允许您指定其他类型的参数类型作为文件名。 和上面的示例表所示的一个或多个具体扩展。

它不支持 `path` 参数类型。

_添加于 v22.3_

### 正则表达式

.. 列:

```
**正则表达式已应用**：_无论你插入了什么样的  
**投射类型**：`str`  
**示例匹配**：  

- `/path/to/2021-01-01`

这使你能够自由地定义你使用的特定匹配模式。

在所显示的示例中，我们正在寻找一个 `YYYY-MM-DD` 格式的日期。
```

.. 列:

````
```python
@app.route(r"/path/to/<foo:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))>")
async def 处理程序(请求，foo: str):
    ...
```
````

### 正则表达式匹配

与复杂的路由相比，上述例子往往太简单， 我们使用完全不同的路由匹配模式，所以我们将在这里详细解释正则表达式匹配的高级用途。

有时候你想要匹配路由的一部分：

```text
/image/123456789.jpg
```

如果你想要匹配文件模式，但仅捕获数字部分，你需要做一些regex funn 😄:

```python
app.route(r"/image/<img_id:(?P<img_id>\d+)\.jpg>")
```

此外，所有这些都应当是可以接受的：

```python
@app.get(r"/<foo:[a-z]{3}.txt>")                # matching on the full pattern
@app.get(r"/<foo:([a-z]{3}).txt>")              # defining a single matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).txt>")       # defining a single named matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).(?:txt)>")   # defining a single named matching group, with one or more non-matching groups
```

而且，如果使用一个命名匹配组，它必须与段标签相同。

```python
@app.get(r"/<foo:(?P<foo>\d+).jpg>")  # OK
@app.get(r"/<foo:(?P<bar>\d+).jpg>")  # NOT OK
```

更多常规使用方法，请参阅[正则表达式操作](https://docs.python.org/3/library/re.html)

## 正在生成 URL

.. 列:

```
Sanic 提供了一个基于处理方法名称：`app.url_for()`生成URL的方法。 如果你想要避免硬编码URL路径到你的应用，那么这将是有用的；相反，你只能引用处理程序名称。
```

.. 列:

````
```python
@app。 oute('/')
async def index(request):
    # 为端点 `post_handler`
    url = app. rl_for('post_handler', post_id=5)

    # 重定向到 "/posts/5"
    return redirect(url)

@app. oute('/posts/<post_id>')
async def post_handler(request, post_id):
    ...
```
````

.. 列:

```
您可以传递任意数量的关键字参数。 任何为 _not_ 的请求参数都将作为查询字符串的一部分实现。
```

.. 列:

````
```python
claim app.url_for(
    "post_handler",
    post_id=5,
    arg_one="one",
    arg_two="two",
) =="/posts/5?arg_one=one&arg_two=two"
```
````

.. 列:

```
还支持通过单个查询键的多个值。
```

.. 列:

````
```python
claim app.url_for(
    "post_handler",
    post_id=5,
    arg_one=["one", "two",
) =="/posts/5?arg_one=one=one&arg_one=two"
```
````

### 特殊关键字参数

详见API Docs。

```python
app.url_for("post_handler", post_id=5, arg_one="one", _anchor="anchor")
# '/posts/5?arg_one=one#anchor'

# _external requires you to pass an argument _server or set SERVER_NAME in app.config if not url will be same as no _external
app.url_for("post_handler", post_id=5, arg_one="one", _external=True)
# '//server/posts/5?arg_one=one'

# when specifying _scheme, _external must be True
app.url_for("post_handler", post_id=5, arg_one="one", _scheme="http", _external=True)
# 'http://server/posts/5?arg_one=one'

# you can pass all special arguments at once
app.url_for("post_handler", post_id=5, arg_one=["one", "two"], arg_two=2, _anchor="anchor", _scheme="http", _external=True, _server="another_server:8888")
# 'http://another_server:8888/posts/5?arg_one=one&arg_one=two&arg_two=2#anchor'
```

### 自定义路由名称

.. 列:

```
在注册路由时可以通过 `name` 参数使用自定义路由名称。
```

.. 列:

````
```python
@app.get("/get", name="get_handler")
def handler(request):
    return text("OK")
```
````

.. 列:

```
现在，使用此自定义名称检索URL
```

.. 列:

````
```python
assert app.url_for("get_handler", foo="bar") == "/get?foo=bar"
```
````

## Websockets路由

.. 列:

```
Websocket 路由器类似于HTTP方法。
```

.. 列:

````
```python
async def 处理器(请求) ws：
    message = "Start"
    而True：
        等待w。 end(message)
        message = 等待ws.recv()

app.add_websocket_route(handler, "/test")
```
````

.. 列:

```
它还有一个方便装饰器。
```

.. 列:

````
```python
@app.websocket("/test")
async def handler(request, w):
    message = "Start"
    while True:
        request ws.send(message)
        message = 等待ws.recv()
```
````

阅读[websockets部分](/guide/advanced/websockets.md)以了解如何工作的更多信息。

## 严格斜线

.. 列:

```
Sanic 路由可以被配置为完全匹配是否存在尾随斜线： `/`。 这可以在几个级别上进行配置，按照这个先后顺序排列：

1。 Route
2. 蓝图
3. 蓝图组
4 应用程序
```

.. 列:

````
```python
# provide default strict_slashes value for all routes
app = Sanic(__file__, strict_slashes=True)
```

```python
# overwrite strict_slashes value for specific route
@app.get("/get", strict_slashes=False)
def handler(request):
    return text("OK")
```

```python
# it also works for blueprints
bp = Blueprint(__file__, strict_slashes=True)

@bp.get("/bp/get", strict_slashes=False)
def handler(request):
    return text("OK")
```

```python
bp1 = Blueprint(name="bp1", url_prefix="/bp1")
bp2 = Blueprint(
    name="bp2",
    url_prefix="/bp2",
    strict_slashes=False,
)

# This will enforce strict slashes check on the routes
# under bp1 but ignore bp2 as that has an explicitly
# set the strict slashes check to false
group = Blueprint.group([bp1, bp2], strict_slashes=True)
```
````

## 静态文件

.. 列:

```
In order to serve static files from Sanic, use `app.static()`.

The order of arguments is important:

1. Route the files will be served from
2. Path to the files on the server

See [API docs](https://sanic.readthedocs.io/en/stable/sanic/api/app.html#sanic.app.Sanic.static) for more details.
```

.. 列:

````
```python
app.static("/static/", "/path/to/directory")
```
````

.. tip::

```
通常最佳做法是以斜杠结束您的目录路径(`/this/is/a/directory/`)。这会通过更明确地去除模糊性。
```

.. 列:

```
您也可以为个别文件服务。
```

.. 列:

````
```python
app.static("/", "/path/to/index.html")
```
````

.. 列:

```
命名您的端点有时也是有用的
```

.. 列:

````
```python
app.static(
    "/user/uploads/",
    "/path/to/uploads/",
    name="上传",
)
```
````

.. 列:

```
检索URL与处理程序相似。但当我们需要一个目录中的特定文件时，我们也可以添加 `filename` 参数。
```

.. 列:

````
```python
claim app.url_for(
    "static",
    name="static",
    filename="filename="文件。 xt",
) == "/static/file.txt"
```
```python
sapp. rl_for(
    "static",
    name="上传",
    filename="image.png",
) == "/user/uploads/image.png"

```
````

.. tip::

````
如果你要多道`static()`路由，那么*强烈*建议你手动命名。 这几乎肯定会缓解发现缺陷的可能性。

```python
app.static("/user/uploads/", "/path/to/uploads/", name="上传")
app.static("/user/profile/", "/path/to/profile/", name="profile_pics")
```
````

#### 自动索引服务

.. 列:

```
如果你有一个静态文件目录，应该通过索引页面来使用，你可以提供索引的文件名。 现在，当到达该目录 URL 时，索引页面将被服务。
```

.. 列:

````
```python
app.static("/foo/", "/path/to/foo/", index="index.html")
```
````

_添加于 v23.3_

#### 文件浏览器

.. 列:

```
当使用静态处理器的目录时，Sanic可以被配置为显示基本文件浏览器，而不是使用 `directory_view=True`。
```

.. 列:

````
```python
app.static("/uploads/", "/path/to/dir", directory_view=True)

````

您的浏览器现在有一个可浏览的目录：

![image](/assets/images/directory-view.png)

_添加于 v23.3_

## 路由环境

.. 列:

```
当路由被定义时，您可以添加任何数量的关键字参数与 `ctx_` 前缀。 这些值将被注入到路由 `ctx` 对象中。
```

.. 列:

````
```python
@app.get("/1", ctx_label="something")
async def handler1(request):
    ...

@app.get("/2", ctx_label="something")
async def handler2(request):
    ...

@app.get("/99")
async def handler99(request):
    ...

@app.on_request
async def do_something(request):
    if request.route.ctx.label == "something":
        ...
```
````

_添加于 v21.12_
