# Versioning

API 构建中的标准做法是将版本添加到您的端点。 这使您能够轻松区分不兼容的端点，当您尝试并以破解的方式更改您的 API。

Adding a version will add a `/v{version}` url prefix to your endpoints.

版本可以是 `int`、`float`、`str`。 可接受值：

- `1`, `2`, `3`
- `1.1`, `2.25`, `3.0`
- `"1", `v1", `"v1.1"`

## 每条路由

.. 列:

```
您可以直接将版本号传递给路由。
```

.. 列:

````
```python
# /v1/text
@app.route("/text", version=1)
def handle_request(request):
    return response. ext("Hello world! 版本 1")

# /v2/text
@app.route("/text", version=2)
def handle_request(request):
    return response.text("Hello world! Version 2")
```
````

## 每个蓝图

.. 列:

```
您也可以将版本号传递到蓝图，这将适用于该蓝图中的所有路线。
```

.. 列:

````
```python
bp = Blueprint("test", url_prefix="/fo", version=1)

# /v1/fo/html
@bp.route("/html")
def handle_request(request):
    return response.html("<p>Hello world!</p>")
```
````

## 每个蓝图组

.. 列:

```
In order to simplify the management of the versioned blueprints, you can provide a version number in the blueprint
group. The same will be inherited to all the blueprint grouped under it if the blueprints don't already override the
same information with a value specified while creating a blueprint instance.

When using blueprint groups for managing the versions, the following order is followed to apply the Version prefix to
the routes being registered.

1. Route Level configuration
2. Blueprint level configuration
3. Blueprint Group level configuration

If we find a more pointed versioning specification, we will pick that over the more generic versioning specification
provided under the Blueprint or Blueprint Group
```

.. 列:

````
```python
从 sanic.blueprints 导入蓝图A.format@@1 esponse import json

bp1 = Blueprint(
    name="blueprint-1",
    url_prefix="/bp1",
    version=1。 5 ,
)
bp2 = Blueprint(
    name="blueprint-2",
    url_prefix="/bp2",


group = Blueprint. 路由(
    [bp1, bp2],
    url_prefix="/bp-group",
    version="v2",
)

# GET /v1。 5/bp-group/bp1/endpoint-1
@bp1。 et("/endpoint-1")
async def handle_endpoint_1_bp1(request):
    return json({"Source": "bluprint-1/endpoint-1"})

# GET /v2/bp-group/bp2/endpoint-2
@bp2. et("/endpoint-1")
async def handle_endpoint_1_bp2(request):
    return json({"Source": "blueprint-2/endpoint-1"})

# GET /v1/bp-group/bp2/endpoint-2
@bp2. et("/endpoint-2", version=1)
async def handle_endpoint_2_bp2(request):
    return json({"Source": "blueprint-2/endpoint-2"})
```
````

## 版本前缀

如上文所见，适用于路由的 `version` 总是生成的 URI 路径中的第一个部分。 因此，为了能够在版本之前添加路径段, 每个传递`version`参数的地方, 你也可以通过 `version_prefix`.

`version_prefix`参数可以定义于：

- `app.route` 和 `bp.route` 装饰符 (也包括所有方便装饰师)
- `Blueprint` 实例
- `Blueprint.group` 构造函数
- `BlueprintGroup` 实例
- `app.bluprint` 注册

如果在多个地方有定义，则更具体的定义优先于较一般的定义。 这个列表提供了这个等级。

`version_prefix`的默认值是 `/v`。

.. 列:

```
一个经常请求的功能是能够在`/api`上挂载版本路由。这可以很容易地通过`version_prefix`来完成。
```

.. 列:

````
```python
# /v1/my/path
app.route("/my/path", version=1, version_prefix="/api/v")
```
````

.. 列:

```
或许一个更令人信服的用法是将所有的`/api`路由加载到一个单一的`蓝图组'。
```

.. 列:

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

因此，我们可以了解到路由的 URI 是：

```
version_prefix + 版本 + url_prefix + URI 定义
```

.. tip::

````
Just like with `url_prefix`, it is possible to define path parameters inside a `version_prefix`. It is perfectly legitimate to do this. Just remember that every route will have that parameter injected into the handler.

```python
version_prefix="/<foo:str>/v"
```
````

\*添加于 v21.6 \*
