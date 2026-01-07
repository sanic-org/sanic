# 蓝图 (Blueprints)

## 概览(Overview)

蓝图是可以在应用程序内用于子路由的对象。 蓝图不是将路线添加到应用程序实例中，而是定义了类似的添加路线的方法， 然后以灵活和可搭配的方式在申请中登记。

蓝图对于更大的应用程序特别有用，您的应用程序逻辑可以分成几组或几个责任领域。

## 创建和注册

.. 列:

```
首先，您必须创建一个蓝图。它有一个非常相似的 API 与 `Sanic()` 应用实例与许多相同的装饰师相同。
```

.. 列:

````
```python
# ./my_bluprint.py
from sanic.response import json
from sanic import Blueprint

bp = Blueprint(“my_bluprint")

@bp. oute("/")
async def bp_root(request):
    return json({"my": "blueprint"})
```
````

.. 列:

```
接下来，你在应用实例中注册它。
```

.. 列:

````
```python
from sanic import Sanic
from my_blueprint import bp

app = Sanic(__name__)
app.blueprint(bp)
```
````

蓝图也有相同的`websocket()`装饰器和`add_websocket_route`方法实现websocket。

.. 列:

```
从 v21.12开始，蓝图可以在添加对象之前或之后注册。 以前，只有注册时附于蓝图的对象才会被加载到应用程序实例。
```

.. 列:

````
```python
app.bluprint(bp)

@bp.route("/")
async def bp_root(request):
    ...
```
````

## 正在复制

.. 列:

```
蓝图以及附加到它们的所有内容都可以使用 `copy()` 方法复制到新的实例。 唯一需要的参数是通过一个新的 `name` 。 然而，您也可以使用这个来覆盖旧蓝图中的任何值。
```

.. 列:

````
```python
v1 = Blueprint("Version1", version=1)

@v1.route("/something")
def something(request):
    passe

v2 = v1.copy("Version2", version=2)

app. lueprint(v1)
app.bluprint(v2)
```

```
可用路径：
/v1/some
/v2/some

```
````

\*添加于 v21.9 \*

## 蓝图组

蓝图也可以作为列表或管道的一部分注册 如果登记员将通过任何次级蓝图序列递归循环，并相应地进行登记。 提供了蓝图群组方法来简化这个过程，允许“模拟”后端目录结构模仿从前端看到的东西。 请考虑这个(相当构思) 示例：

```text
api/
├──content/
│ ├──authors.py
│ ├──static.py
│ └──__init__.py
├──info.py
└──__init__.py
app.py
```

.. 列:

```
#### 第一张蓝图
```

.. 列:

````
```python
# api/content/authors.py
from sanic import Blueprint

作者 = Bluprint("content_authors", url_prefix="/authors")
```
````

.. 列:

```
#### 第二张蓝图
```

.. 列:

````
```python
# api/content/static.py
from sanic import Blueprint

static = Bluprint("content_static", url_prefix="/static")
```
````

.. 列:

```
#### 蓝图组
```

.. 列:

````
```python
# api/content/__init__.py
from sanic import Blueprint
from .static import static
from .authors import authors

content = Blueprint.group(static, authors, url_prefix="/content")
```
````

.. 列:

```
#### 第三张蓝图
```

.. 列:

````
```python
# api/info.py
from sanic importer

info = Bluprint("info", url_prefix="/info")
```
````

.. 列:

```
#### 另一个蓝图组
```

.. 列:

````
```python
# api/__init__.py
from sanic import Blueprint
from .content import content
from .info import info

api = Blueprint.group(content, info, url_prefix="/api")
```
````

.. 列:

```
#### 主要服务器

所有蓝图已注册
```

.. 列:

````
```python
# app.py
from sanic import Sanic
from .api import api

app = Sanic(__name__)
app.blueprint(api)
```
````

### 蓝图组前缀和可编辑性

如上面的代码所示， 当你创建一个蓝图组时，你可以通过将 `url_prefix` 参数传递到 \`Blueprint，将该组中所有蓝图的 URL 前缀扩展到该组。 路由方法 这有助于为您的 API 创建模拟目录结构。

此外，还有一个“name_prefix”参数可用来使蓝图可重新使用和复制。 在对多个群组应用单一蓝图时是特别必要的。 通过这样做，蓝图将被注册为每个组的唯一名称。 它允许蓝图多次注册，并且每个路径都有一个唯一的标识符。

.. 列:

```
考虑这个示例。已生成的路由将被命名如下：
- `TestAppp.group-a_bp1.route1`
- `TestAppp.group-a_bp2.route2`
- `TestAppp.group-b_bp1.route1`
- `TestApp.group-b_bp2.route2`
```

.. 列:

````
```python
bp1 = Blueprint("bp1", url_prefix="/bp1")
bp2 = Blueprint("bp2", url_prefix="/bp2")

bp1。 dd_route(lambda _ : ..., "/", name="route1")
bp2.add_route(lambda _: ..., "/", name="route2")

group_a = Bluprint。 roup(
    bp1, bp2, url_prefix="/group-a", name_prefix="group-a"
)
group_b = 蓝图。 roup(
    bp1, bp2, url_prefix="/group-b", name_prefix="group-b"
)

app = Sanic("TestApp")
app.bluprint(troup_a)
app.bluprint(group_b)
```
````

_在 v23.6_ 中添加的名称前缀

## 中间件

.. 列:

```
蓝图也可以有只为其端点注册的中间件.
```

.. 列:

````
```python
@bp.middleware
async def print_on_request(request):
    print("我是一个间谍")

@bp. iddleware("request")
async def halt_request(request):
    return text("我停止请求")

@bp. iddleware("响应")
async def halt_response(request, response):
    return text("我已停止响应")
```
````

.. 列:

```
同样，使用蓝图组可以将中间件应用到整个一组嵌套蓝图。
```

.. 列:

````
```python
bp1 = Blueprint("bp1", url_prefix="/bp1")
bp2 = Blueprint("bp2", url_prefix="/bp2")

@bp1。 iddleware("request")
async def bp1_only_middleware(request):
    print("applied on 蓝图: bp1 only")

@bp1。 oute("/")
async def bp1_route(request):
    return text("bp1")

@bp2。 oute("/<param>")
async def bp2_route(request, param):
    return text(param)

group = Bluprint.group(bp1, bp2)

@group。 iddleware("request")
async def group_middleware(request):
    print("common middleware applied for bp1 and bp2")

# 注册应用程序
app之下的蓝图组。 lueprint(group)
```
````

## 例外

.. 列:

```
就像其他[异常处理](./exceptions.md)一样，您可以定义蓝图特定处理器。
```

.. 列:

````
```python
@bp.exception(NotFound)
def ignorre_404s(请求, 异常):
    return text("Yep, 我完全发现页面: {}".format (crequest.url))
```
````

## 静态文件

.. 列:

```
蓝图也可以有自己的静态处理程序
```

.. 列:

````
```python
bp = Blueprint("bp", url_prefix="/bp")
bp.static("/web/path", "/folder/to/serve")
bp.static("/web/path", "/folder/to/server", name="上传")
```
````

.. 列:

```
然后可以通过 `url_for()`检索。更多信息请见 [routing](../basics/routing.md)。
```

.. 列:

````
```python
>> > print(app.url_for("static", name="bp.uploads", filename="file.txt"))
'/bp/web/path/file.txt'
```
````

## 监听器

.. 列:

```
蓝图也可以实现 [listeners](../basics/listeners.md)。
```

.. 列:

````
```python
@bp.listener("before_server_start")
async def before_server_start(app, loop):


@bp.listener("after_server_stop")
async def after _server_stop(app, loop):
    ...
```
````

## Versioning

正如在[版本部分](../advanced/versioning.md)中所讨论的那样，蓝图可以用于实现不同版本的Web API。

.. 列:

```
`version`将作为`/v1`或`/v2`等添加到路线上。
```

.. 列:

````
```python
auth1 = Blueprint("auth", url_prefix="/auth", version=1)
auth2 = Blueprint("auth", url_prefix="/auth", version=2)
```
````

.. 列:

```
当我们在应用上注册我们的蓝图时，路由`/v1/auth`和`/v2/auth`将指向个别的蓝图， 允许为每个API版本创建子站点。
```

.. 列:

````
```python
from auth_blueprints import auth1, auth2

app = Sanic(__name__)
app.blueprint(auth1)
app.blueprint(auth2)
```
````

.. 列:

```
同时也可以将蓝图归类到 '蓝图组' 实体，并且同时将它们的多个版本一起使用
。
```

.. 列:

````
```python
auth = Blueprint("auth", url_prefix="/auth")
metrics = Blueprint("metrics", url_prefix="/metrics")

group = Blueprint. roup(aut, meters, version="v1")

# 这将为API提供以下URL路径
# /v1/auth/ 和 /v1/metrics
```
````

## 可合成的

“蓝图”可以注册到多个组，每个“蓝图组”本身都可以注册和嵌套。 这就创造了无限的 `Blueprint` 组成。

\*添加于 v21.6 \*

.. 列:

```
看看这个示例，并看看这两个处理程序如何实际装载为五(5)条不同的路径。
```

.. 列:

````
```python
app = Sanic(__name__)
blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")
group = Blueprint.group(
    blueprint_1,
    blueprint_2,
    version=1,
    version_prefix="/api/v",
    url_prefix="/grouped",
    strict_slashes=True,
)
primary = Blueprint.group(group, url_prefix="/primary")

@blueprint_1.route("/")
def blueprint_1_default_route(request):
    return text("BP1_OK")

@blueprint_2.route("/")
def blueprint_2_default_route(request):
    return text("BP2_OK")

app.blueprint(group)
app.blueprint(primary)
app.blueprint(blueprint_1)

# The mounted paths:
# /api/v1/grouped/bp1/
# /api/v1/grouped/bp2/
# /api/v1/primary/grouped/bp1
# /api/v1/primary/grouped/bp2
# /bp1

```
````

## 正在生成 URL

当生成一个 url_for()\`的URL时，端点名称将是表单的：

```text
{blueprint_name}.{handler_name}
```
