# 版本控制（Versioning）

在API构建的标准实践中，向路由入口添加版本是一种常见做法。 这样，当您在未来以破坏性方式更改API时，可以轻松区分不兼容的路由入口。

添加版本号将会在您的路由入口前加上 `/v{version}` 形式的URL前缀。

版本可以是 `int`、`float`、`str`类型 下列值都为有效值：

- `1`, `2`, `3`
- `1.1`, `2.25`, `3.0`
- `"1"`, `"v1"`, `"v1.1"`

## 单个路由（Per route）

.. column::

```
您可以直接向路由传递版本号。
```

.. column::

````
```python
# /v1/text
@app.route("/text", version=1)
def handle_request(request):
    return response.text("Hello world! Version 1")

# /v2/text
@app.route("/text", version=2)
def handle_request(request):
    return response.text("Hello world! Version 2")
```
````

## 单个蓝图（Per Blueprint）

.. column::

```
您还可以向蓝图传递版本号，这样该版本号将应用于该蓝图内的所有路由。
```

.. column::

````
```python
bp = Blueprint("test", url_prefix="/foo", version=1)

# /v1/foo/html
@bp.route("/html")
def handle_request(request):
    return response.html("<p>Hello world!</p>")
```
````

## 单个蓝图组（Per Blueprint Group）

.. column::

```
为了简化版本化蓝图的管理，您可以在蓝图组中提供一个版本号。如果蓝图在创建实例时未指定覆盖相同信息的值，那么同一版本号将自动应用于该蓝图组下的所有蓝图。

在使用蓝图组管理版本时，将按照以下顺序将Version前缀应用于正在注册的路由：

1. 路由级别的配置
2. 蓝图级别的配置
3. 蓝图组级别的配置

如果我们发现更具体的版本化规范，我们将优先选择它，而不是蓝图或蓝图组中提供的更通用的版本化规范。
```

.. column::

````
```python
from sanic.blueprints import Blueprint
from sanic.response import json

bp1 = Blueprint(
    name="blueprint-1",
    url_prefix="/bp1",
    version=1.25,
)
bp2 = Blueprint(
    name="blueprint-2",
    url_prefix="/bp2",
)

group = Blueprint.group(
    [bp1, bp2],
    url_prefix="/bp-group",
    version="v2",
)

# GET /v1.25/bp-group/bp1/endpoint-1
@bp1.get("/endpoint-1")
async def handle_endpoint_1_bp1(request):
    return json({"Source": "blueprint-1/endpoint-1"})

# GET /v2/bp-group/bp2/endpoint-2
@bp2.get("/endpoint-1")
async def handle_endpoint_1_bp2(request):
    return json({"Source": "blueprint-2/endpoint-1"})

# GET /v1/bp-group/bp2/endpoint-2
@bp2.get("/endpoint-2", version=1)
async def handle_endpoint_2_bp2(request):
    return json({"Source": "blueprint-2/endpoint-2"})
```
````

## 版本前缀(Version prefix)

如上所述，应用于路由的版本始终是生成URI路径中的第一个部分。 因此，为了能够在版本之前添加路径部分，您在传入版本参数的所有位置都可以同时传入`version_prefix`参数，从而实现这一目的。

`version_prefix` 参数可以定义于：

- `app.route` 和 `bp.route` 装饰器 (也包括所有便捷的装饰器）
- `Blueprint` 实例
- `Blueprint.group`  构造函数
- `BlueprintGroup` 实例
- `使用 `app.blueprint\` 注册蓝图时

如果有多个位置定义，较具体的定义会覆盖较一般的定义。 本列表提供了这一层级关系。

版本控制前缀`version_prefix`的默认值是 `/v`。

.. column::

```
一个常被要求的功能是在 `/api` 上挂载版本化的路由。这可以通过 `version_prefix` 轻松实现。
```

.. column::

````
```python
# /v1/my/path
app.route("/my/path", version=1, version_prefix="/api/v")
```
````

.. column::

```
或许一个更具说服力的用法是将所有 `/api` 路由加载到单个 `BlueprintGroup` 中。
```

.. column::

````
```python
# /v1/my/path
app = Sanic(__name__)
v2ip = Blueprint("v2ip", url_prefix="/ip", version=2)
api = Blueprint.group(v2ip, version_prefix="/api/version")

# /api/version2/ip
@v2ip.get("/")
async def handler(request):
    return text(request.ip)

app.blueprint(api)
```
````

因此我们可以得知，一个路由的 URI 是由下面基本构成的：

```
version_prefix + version + url_prefix + URI definition
```

.. tip:: 提示

````
就像 `url_prefix` 一样，在 `version_prefix` 内部定义路径参数也是可能的。这样做完全合理。但请记住，每个路由都会将该参数注入到处理器中。

```python
version_prefix="/<foo:str>/v"
```
````

\*添加于 v21.6 \*
