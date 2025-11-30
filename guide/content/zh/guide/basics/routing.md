# 路由(Routing)

.. column::

```
至今为止，我们已经看到了这个装饰器的不同形式。

但它究竟是什么？以及我们应该如何使用它呢？
```

.. column::

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

.. column::

```
将处理函数连接到路由入口的最基本方法是使用 `app.add_route()`。

详情请参考 [API 文档](https://sanic.readthedocs.io/en/stable/sanic/api_reference.html#sanic.app.Sanic.url_for)
```

.. column::

````
```python
async def handler(request):
    return text("OK")

app.add_route(handler, "/test")
```
````

.. column::

```
默认情况下，路由可通过 HTTP `GET` 请求访问。您可以更改处理函数，使其响应一种或多种 HTTP 方法。
```

.. column::

````
```python
app.add_route(
    handler,
    '/test',
    methods=["POST", "PUT"],
)
```
````

.. column::

```
使用装饰器语法，前面的例子等同于下面这样。
```

.. column::

````
```python
@app.route('/test', methods=["POST", "PUT"])
async def handler(request):
    return text('OK')
```
````

## HTTP 方法(HTTP methods)

每种标准 HTTP 方法都有一个便捷的装饰器。

### GET

```python
@app.get('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/GET)

### POST

```python
@app.post('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST)

### PUT

```python
@app.put('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/PUT)

### PATCH

```python
@app.patch('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/PATCH)

### DELETE

```python
@app.delete('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/DELETE)

### HEAD

```python
@app.head('/test')
async def handler(request):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD)

### OPTIONS

```python
@app.options('/test')
async def handler(request):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS)

.. warning:: 警告⚠

````
默认情况下，Sanic 只会在非安全 HTTP 方法（`POST`、`PUT`、`PATCH`、`DELETE`）上接受传入的请求正文。如果您想在任何其他方法上接收 HTTP 请求中的数据，您需要采取以下两种选项之一：

**选项 #1 - 使用 `ignore_body` 告诉 Sanic 去接受请求体**
```python
@app.request("/path", ignore_body=False)
async def handler(_):
    ...
```

**选项 #2 - 在处理函数中手动使用 `receive_body` 接受请求体**
```python
@app.get("/path")
async def handler(request: Request):
    await request.receive_body()
```
````

## 路径参数（Path parameters）

.. column::

```
Sanic 支持模式匹配，可以从 URL 路径中提取参数，并将这些参数作为关键字参数注入到路由处理函数中。
```

.. column::

````
```python
@app.get("/tag/<tag>")
async def tag_handler(request, tag):
    return text("Tag - {}".format(tag))
```
````

.. column::

```
您可以为参数声明一个类型。在匹配时，该类型将被强制执行，并且还会对该变量进行类型转换。
```

.. 列:

````
```python
@app.get("/foo/<foo_id:uuid>")
async def uuid_handler(request, foo_id: UUID):
    return text("UUID - {}".format(foo_id))
```
````

.. column::

```
对于一些标准类型，如 `str`、`int` 和 `UUID`，Sanic 可以从函数签名中推断路径参数的类型。这意味着在路径参数定义中不一定总是需要包含类型。
```

.. column::

````
```python
@app.get("/foo/<foo_id>")  # Notice there is no :uuid in the path parameter
async def uuid_handler(request, foo_id: UUID):
    return text("UUID - {}".format(foo_id))
```
````

### 支持的类型

### `str`

.. column::

```
**正则表达式**: `r"[^/]+"`  
**转换类型**: `str`  
**匹配案例**:  

- `/path/to/Bob`
- `/path/to/Python%203`

从 v22.3 版本开始，`str` 将不会匹配空字符串。对于这种行为，请参见 `strorempty`。
```

.. column::

````
```python
@app.route("/path/to/<foo:str>")
async def handler(request, foo: str):
    ...
```
````

### `strorempty`

.. column::

```
**正则表达式**: `r"[^/]*"`  
**转换类型**: `str`  
**匹配案例**:

- `/path/to/Bob`
- `/path/to/Python%203`
- `/path/to/`

与 `str` 路径参数类型不同，`strorempty` 也可以匹配空字符串路径段。

*添加于 v22.3*
```

.. column::

````
```python
@app.route("/path/to/<foo:strorempty>")
async def handler(request, foo: str):
    ...
```
````

### `int`

.. column::

```
**正则表达式**: `r"-?\d+"`  
**转换类型**: `int`  
**匹配案例**:  

- `/path/to/10`
- `/path/to/-10`

_不匹配浮点数(float)、十六进制(hex)、八进制(octal)等_
```

.. column::

````
```python
@app.route("/path/to/<foo:int>")
async def handler(request, foo: int):
    ...
```
````

### `float`

.. column::

```
**正则表达式**: `r"-?(?:\d+(?:\.\d*)?|\.\d+)"`  
**转换类型**: `float`  
**匹配案例**:  

- `/path/to/10`
- `/path/to/-10`
- `/path/to/1.5`
```

.. column::

````
```python
@app.route("/path/to/<foo:float>")
async def handler(request, foo: float):
    ...
```
````

### `alpha`

.. column::

```
**正则表达式**: `r"[A-Za-z]+"`  
**转换类型**: `str`  
**匹配实例**:  

- `/path/to/Bob`
- `/path/to/Python`

_不匹配数字(digit)、空格(space )或其他特殊字符(special character)_
```

.. column::

````
```python
@app.route("/path/to/<foo:alpha>")
async def handler(request, foo: str):
    ...
```
````

### `slug`

.. column::

```
**正则表达式**: `r"[a-z0-9]+(?:-[a-z0-9]+)*"`  
**转换类型**: `str`  
**匹配案例**:  

- `/path/to/some-news-story`
- `/path/to/or-has-digits-123`

*添加于v21.6*
```

.. column::

````
```python
@app.route("/path/to/<article:slug>")
async def handler(request, article: str):
    ...
```
````

### `path`

.. column::

```
**正则表达式**: `r"[^/].*?"`  
**转换类型**: `str`  
**匹配案例**:
- `/path/to/hello`
- `/path/to/hello.txt`
- `/path/to/hello/world.txt`
```

.. column::

````
```python
@app.route("/path/to/<foo:path>")
async def handler(request, foo: str):
    ...
```
````

.. warning:: 警告

```
由于 `path` 类型会匹配 `/` 符号，您应在使用 `path` 类型时务必小心，并彻底测试您的模式，以免捕获到原本打算发往其他端点的流量。另外，根据您如何使用这种类型，可能会在您的应用程序中引入路径遍历漏洞。防止此类漏洞是您的责任，但如有需要，请随时在我们的社区频道寻求帮助:)
```

### `ymd`

.. column::

```
**正则表达式**: `r"^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))"`  
**转换类型**: `datetime.date`  
**匹配案例**:  

- `/path/to/2021-03-28`
```

.. column::

````
```python
@app.route("/path/to/<foo:ymd>")
async def handler(request, foo: datetime.date):
    ...
```
````

### `uuid`

.. column::

```
**正则表达式**: `r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}"`  
**转换类型**: `UUID`  
**匹配案例**:  

- `/path/to/123a123a-a12a-1a1a-a1a1-1a12a1a12345`
```

.. column::

````
```python
@app.route("/path/to/<foo:uuid>")
async def handler(request, foo: UUID):
    ...
```
````

### ext

.. column::

```
**正则表达式**: n/a
**转换类型**: *varies*
**匹配案例**:
```

.. column::

````
```python
@app.route("/path/to/<foo:ext>")
async def handler(request, foo: str, ext: str):
    ...
```
````

| 定义                                                                                   | 示例                                                          | 文件名      | 扩展                          |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------- | -------- | --------------------------- |
| \<file:ext>                                | page.txt                                    | `"page"` | `"txt"`                     |
| \<file:ext=jpg>                            | cat.jpg                                     | `"cat"`  | \`"jpg""                    |
| \<file:ext=jpg\\\|png\\\|gif\\\|svg> | cat.jpg                                     | `"cat"`  | \`"jpg""                    |
| <file=int:ext>                              | 123.txt                                     | `123`    | `"txt"`                     |
| <file=int:ext=jpg\\|png\\|gif\\|svg>     | 123.svg                                     | `123`    | `"svg"`                     |
| <file=float:ext=tar.gz>     | 3.14.tar.gz | `3.14`   | \`"tar.gz"" |

可以通过特殊的 ext 参数类型来匹配文件扩展名。 它采用一种特殊格式，允许您指定其他类型的参数作为文件名，并如上文示例表格所示，指定一个或多个特定扩展名。

它**不支持** `path` 参数类型。

_添加于 v22.3_

### 正则表达式

.. column::

```
**正则表达式**: _whatever you insert_  
**转换类型**: `str`  
**匹配案例**:  

- `/path/to/2021-01-01`

这样您就可以自由地为您的应用场景定义特定的匹配模式。

在所示示例中，我们正在查找符合 `YYYY-MM-DD` 格式的日期。
```

.. column::

````
```python
@app.route(r"/path/to/<foo:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))>")
async def handler(request, foo: str):
    ...
```
````

### 正则表达式匹配

相比于复杂的路由，上述例子往往过于简单，我们采用了完全不同的路由匹配模式，因此这里将详细解释正则表达式匹配的高级用法。

有时，您可能只想匹配路由的一部分：

```text
/image/123456789.jpg
```

如果你想要匹配包含文件模式，并仅捕获其中的数字部分，那么确实需要运用一些正则表达式的技巧 😄：

```python
app.route(r"/image/<img_id:(?P<img_id>\d+)\.jpg>")
```

此外，所有以下这些匹配项也都是可以的：

```python
@app.get(r"/<foo:[a-z]{3}.txt>")                # matching on the full pattern
@app.get(r"/<foo:([a-z]{3}).txt>")              # defining a single matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).txt>")       # defining a single named matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).(?:txt)>")   # defining a single named matching group, with one or more non-matching groups
```

另外，如果使用命名匹配组，其名称必须与段标签相同。

```python
@app.get(r"/<foo:(?P<foo>\d+).jpg>")  # OK
@app.get(r"/<foo:(?P<bar>\d+).jpg>")  # NOT OK
```

有关更多常规正则表达式用法，请参考 [正则表达式操作](https://docs.python.org/3/library/re.html) 。

## 动态访问(Generating a URL)

.. column::

```
Sanic 提供了一种基于处理程序方法名称生成 URL 的方法：`app.url_for()`。当您希望避免在应用中硬编码 URL 路径时，这非常有用；您可以仅引用处理程序名称即可。
```

.. column::

````
```python
@app.route('/')
async def index(request):
    # generate a URL for the endpoint `post_handler`
    url = app.url_for('post_handler', post_id=5)

    # Redirect to `/posts/5`
    return redirect(url)

@app.route('/posts/<post_id>')
async def post_handler(request, post_id):
    ...
```
````

.. column::

```
您可以传递任意数量的关键字参数。任何不是请求参数的项都将作为查询字符串的一部分实现。
```

.. column::

````
```python
assert app.url_for(
    "post_handler",
    post_id=5,
    arg_one="one",
    arg_two="two",
) == "/posts/5?arg_one=one&arg_two=two"
```
````

.. column::

```
同样支持对单一查询键传入多个值。
```

.. column::

````
```python
assert app.url_for(
    "post_handler",
    post_id=5,
    arg_one=["one", "two"],
) == "/posts/5?arg_one=one&arg_one=two"
```
````

### 特殊关键字参数

See API 文档 for more details.

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

### 自定义路由名称(Customizing a route name)

.. column::

```
可以通过在注册路由时传递 `name` 参数来自定义路由名称。
```

.. column::

````
```python
@app.get("/get", name="get_handler")
def handler(request):
    return text("OK")
```
````

.. column::

```
现在，可以使用这个自定义名称来检索 URL。
```

.. column::

````
```python
assert app.url_for("get_handler", foo="bar") == "/get?foo=bar"
```
````

## Websockets 路由（Websockets routes）

.. column::

```
WebSocket 路由的工作方式与 HTTP 方法类似。
```

.. column::

````
```python
async def handler(request, ws):
    message = "Start"
    while True:
        await ws.send(message)
        message = await ws.recv()

app.add_websocket_route(handler, "/test")
```
````

.. column::

```
它还提供了一个便捷装饰器。
```

.. column::

````
```python
@app.websocket("/test")
async def handler(request, ws):
    message = "Start"
    while True:
        await ws.send(message)
        message = await ws.recv()
```
````

阅读[websockets部分](../advanced/websockets.md) 以了解更多关于它们如何工作的信息。

## 严格匹配分隔符(Strict slashes)

.. column::

```
Sanic 路由可以根据 URL 是否包含尾部斜杠（/）进行严格的匹配配置。这一配置可以在以下几个层级进行，并遵循以下优先级顺序：

1. 路由（Route）
2. 蓝图（Blueprint）
3. 蓝图组（BlueprintGroup）
4. 应用程序（Application）
```

.. column::

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

## 静态文件(Static files)

.. column::

```
为了在 Sanic 中提供静态文件服务，请使用 `app.static()` 方法。

参数的顺序很重要：

1. 文件将被服务的路由地址
2. 服务器上的文件实际路径

欲了解更多信息，请参阅 [API 文档](https://sanic.readthedocs.io/en/stable/sanic/api/app.html#sanic.app.Sanic.static)。
```

.. column::

````
```python
app.static("/static/", "/path/to/directory/")
```
````

.. tip::

```
通常最好以尾部斜杠（/）结束您的目录路径（如 `/this/is/a/directory/`）。这样做能够更明确地消除歧义。
```

.. column::

```
您也可以单独提供单个文件的服务。
```

.. column::

````
```python
app.static("/", "/path/to/index.html")
```
````

.. column::

```
有时为你指定入口提供一个名称也会有所帮助。
```

.. column::

````
```python
app.static(
    "/user/uploads/",
    "/path/to/uploads/",
    name="uploads",
)
```
````

.. column::

```
获取 URL 的工作方式与处理程序类似。但是，当我们需要获取目录中的特定文件时，还可以添加 `filename` 参数。
```

.. column::

````
```python
assert app.url_for(
    "static",
    name="static",
    filename="file.txt",
) == "/static/file.txt"
```
```python
assert app.url_for(
    "static",
    name="uploads",
    filename="image.png",
) == "/user/uploads/image.png"

```
````

.. tip::

````
如果您打算设置多个 `static()` 路由，强烈建议您手动为它们命名。这样做几乎可以肯定能缓解潜在的难以发现的错误问题。

```python
app.static("/user/uploads/", "/path/to/uploads/", name="uploads")
app.static("/user/profile/", "/path/to/profile/", name="profile_pics")
```
````

#### 自动索引服务（Auto index serving）

.. column::

```
如果您有一目录静态文件应通过索引页面提供服务，您可以提供该索引页面的文件名。这样一来，当访问该目录 URL 时，系统将会自动提供索引页面服务。
```

.. column::

````
```python
app.static("/foo/", "/path/to/foo/", index="index.html")
```
````

_添加于 v23.3_

#### 文件浏览器（File browser）

.. column::

```
当从静态处理器提供目录服务时，可以配置 Sanic 使用 `directory_view=True` 来显示一个基本的文件浏览器。
```

.. column::

````
```python
app.static("/uploads/", "/path/to/dir", directory_view=True)
```
````

现在您可以在 Web 浏览器中浏览该目录了：

![image](/assets/images/directory-view.png)

_添加于 v23.3_

## 路由上下文(Route context)

.. column::

```
在定义路由时，您可以添加任意数量以 `ctx_` 前缀的关键字参数。这些值将被注入到路由的 `ctx` 对象中。
```

.. column::

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
