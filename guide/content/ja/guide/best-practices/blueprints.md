# 建設計画

## 概要

設計図は、アプリケーション内のサブルーティングに使用できるオブジェクトです。 アプリケーションインスタンスにルートを追加する代わりに、blueprintsはルートを追加するための同様のメソッドを定義します。 柔軟でプラガブルな方法でアプリケーションに登録されます

ブループリントは、アプリケーションのロジックをいくつかのグループまたは責任領域に分割することができる大規模なアプリケーションに特に便利です。

## 作成と登録

.. 列::

```
まず、青写真を作成する必要があります。同じデコレータの多くを持つ`Sanic()`アプリインスタンスと非常によく似たAPIを持っています。
```

.. 列::

````
```python
# ./my_blueprint.py
from sanic.response import json
from sanic import Blueprint

bp = Blueprint("my_blueprint")

@bp.route("/")
async def bp_root(request):
    return json({"my": "blueprint"})
```
````

.. 列::

```
次に、アプリインスタンスに登録します。
```

.. 列::

````
```python
from sanic import Sanic
from my_blueprint import bp

app = Sanic(__name__)
app.blueprint(bp)
```
````

ブループリントには、websocket()のデコレータとwebsocketを実装するための`add_websocket_route`メソッドもあります。

.. 列::

```
v21.12 以降では、オブジェクトを追加する前後にブループリントを登録することができます。 以前は、登録時にブループリントに添付されたオブジェクトのみがアプリケーションインスタンスにロードされていました。
```

.. 列::

````
```python
app.blueprint(bp)

@bp.route("/")
async def bp_root(request):
    ...
```
````

## コピー中

.. 列::

```
ブループリントとそれに付随するすべてのものは、 `copy()`メソッドを使用して新しいインスタンスにコピーできます。 唯一必要な引数は新しい`name`を渡すことです。 ただし、これを使用して、古い設計図から任意の値を上書きすることもできます。
```

.. 列::

````
```python
v1 = Blueprint("Version1", version=1)

@v1.route("/something")
def something(request):
    pass

v2 = v1.copy("Version2", version=2)

app.blueprint(v1)
app.blueprint(v2)
```

```
Available routes:
/v1/something
/v2/something

```
````

_v21.9_に追加されました

## 建設計画グループ

設計図は、リストやタプルの一部として登録することもできます。 登録者は再帰的に設計図の任意のサブシーケンスを循環し、それに応じて登録します。 ブループリント.groupメソッドは、このプロセスを簡素化するために提供されており、フロントエンドから見たものを模倣した「モック」バックエンドディレクトリ構造を可能にします。 これを考えてみましょう(かなり非対称な例)

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

.. 列::

```
#### 最初の建設計画
```

.. 列::

````
```python
# api/content/authors.py
from sanic import Blueprint

author = Blueprint("content_authors", url_prefix="/authors")
```
````

.. 列::

```
#### 2番目の建設計画
```

.. 列::

````
```python
# api/content/static.py
from sanic import Blueprint

static = Blueprint("content_static", url_prefix="/static")
```
````

.. 列::

```
#### ブループリントグループ
```

.. 列::

````
```python
# api/content/__init__.py
from sanic import Blueprint
from .static import static
from .authors import authors

content = Blueprint.group(static, authors, url_prefix="/content")
```
````

.. 列::

```
#### 3番目の建設計画
```

.. 列::

````
```python
# api/info.py
from sanic import Blueprint

info = Blueprint("info", url_prefix="/info")
```
````

.. 列::

```
#### ブループリントグループ
```

.. 列::

````
```python
# api/__init__.py
from sanic import Blueprint
from .content import content
from .info import info

api = Blueprint.group(content, info, url_prefix="/api")
```
````

.. 列::

```
#### メインサーバー

ブループリントがすべて登録されました
```

.. 列::

````
```python
# app.py
from sanic import Sanic
from .api import api

app = Sanic(__name__)
app.blueprint(api)
```
````

### ブループリントグループのプレフィックスとコンポジション

上のコードに示すように。 ブループリントのグループを作成するときは、`Blueprint に引数`url_prefix`を渡すことで、グループ内のすべてのブループリントのURLプレフィックスを拡張できます。 roup`メソッド。 これは、API のモックディレクトリ構造を作成するときに便利です。

さらに、`name_prefix`引数があり、設計図を再利用可能で構成可能にします。 これは、複数のグループに単一の設計図を適用するときに特に必要です。 これを行うことで、ブループリントは各グループごとに固有の名前で登録されます。 青写真を複数回登録しルートごとに固有の識別子で適切な名前を付けることができます

.. 列::

```
以下の例を考えてみましょう。
- `TestApp.group-a_bp1.route1`
- `TestApp.group-a_bp2.route2`
- `TestApp.group-a_bp1.route1`
- `TestApp.group-bp2.route2`
```

.. 列::

````
```python
bp1 = Blueprint("bp1", url_prefix="/bp1")
bp2 = Blueprint("bp2", url_prefix="/bp2")

bp1.add_route(lambda _: ..., "/", name="route1")
bp2.add_route(lambda _: ..., "/", name="route2")

group_a = Blueprint.group(
    bp1, bp2, url_prefix="/group-a", name_prefix="group-a"
)
group_b = Blueprint.group(
    bp1, bp2, url_prefix="/group-b", name_prefix="group-b"
)

app = Sanic("TestApp")
app.blueprint(group_a)
app.blueprint(group_b)
```
````

_v23.6_ にプレフィックスが追加されました

## ミドルウェア

.. 列::

```
ブループリントはエンドポイントのみに特別に登録されているミドルウェアを持つこともできます。
```

.. 列::

````
```python
@bp.middleware
async def print_on_request(request):
    print("I am a spy")

@bp.middleware("request")
async def halt_request(request):
    return text("I halted the request")

@bp.middleware("response")
async def halt_response(request, response):
    return text("I halted the response")
```
````

.. 列::

```
同様に、青写真グループを使用して、入れ子になった設計図のグループ全体にミドルウェアを適用することができます。
```

.. 列::

````
```python
bp1 = Blueprint("bp1", url_prefix="/bp1")
bp2 = Blueprint("bp2", url_prefix="/bp2")

@bp1.middleware("request")
async def bp1_only_middleware(request):
    print("applied on Blueprint : bp1 Only")

@bp1.route("/")
async def bp1_route(request):
    return text("bp1")

@bp2.route("/<param>")
async def bp2_route(request, param):
    return text(param)

group = Blueprint.group(bp1, bp2)

@group.middleware("request")
async def group_middleware(request):
    print("common middleware applied for both bp1 and bp2")

# Register Blueprint group under the app
app.blueprint(group)
```
````

## 例外

.. 列::

```
他のformat@@0(./exception handling)と同様に、ブループリント固有のハンドラを定義できます。
```

.. 列::

````
```python
@bp.exception(NotFound)
def ignore_404s(request, exception):
    return text("Yep, I find the page: {}".format(request.url))
```
````

## 静的ファイル

.. 列::

```
設計図は、独自の静的ハンドラを持つこともできます。
```

.. 列::

````
```python
bp = Blueprint("bp", url_prefix="/bp")
bp.static("/web/path", "/folder/to/serve")
bp.static("/web/path", "/folder/to/server", name="uploads")
```
````

.. 列::

```
これは `url_for()` を使用して取得できます。詳細は [routing](/guide/basics/routing.md) を参照してください。
```

.. 列::

````
```python
>>> print(app.url_for("static", name="bp.uploads", filename="file.txt"))
'/bp/web/path/file.txt'
```
````

## リスナー

.. 列::

```
ブループリントは [listeners](/guide/basics/listeners.md) も実装できます。
```

.. 列::

````
```python
@bp.listener("before_server_start")
async def before_server_start(app, loop):
    ...

@bp.listener("after_server_stop")
async def after_server_stop(app, loop):
    ...
```
````

## Versioning

[versioning section](/guide/advanced/version.md) で説明されているように、設計図は異なるバージョンの Web API を実装するために使用できます。

.. 列::

```
`version`はルートの前に`/v1`または`/v2`などとなります。
```

.. 列::

````
```python
auth1 = ブループリント("auth", url_prefix="/auth", version=1)
auth2 = ブループリント("auth", url_prefix="/auth", version=2)
```
````

.. 列::

```
アプリにブループリントを登録すると、ルート`/v1/auth`と`/v2/auth`が個々のブループリントを示すようになります。 APIバージョンごとにサブサイトを作成することができます。
```

.. 列::

````
```python
from auth_blueprints import auth1, auth2

app = Sanic(__name__)
app.blueprint(auth1)
app.blueprint(auth2)
```
````

.. 列::

```
また、 `BlueprintGroup` エンティティの下で設計図をグループ化し、それらの複数を
同時にバージョン化することもできます。
```

.. 列::

````
```python
auth = Blueprint("auth", url_prefix="/auth")
metrics = Blueprint("metrics", url_prefix="/metrics")

group = Blueprint.group(auth, metrics, version="v1")

# This will provide APIs prefixed with the following URL path
# /v1/auth/ and /v1/metrics
```
````

## 作成可能

`Blueprint` は複数のグループに登録することができ、`BlueprintGroup` 自体はそれぞれ登録して入れ子にすることができます。 これにより、無限の可能性をもたらす「設計図」構図が作成されます。

_V21.6_に追加されました

.. 列::

```
この例を見て、2つのハンドラが実際に5つの(5)の異なるルートとしてどのようにマウントされているかを見てください。
```

.. 列::

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

## URLの生成

`url_for()` でURLを生成する場合、エンドポイント名は以下のようになります。

```text
{blueprint_name}.{handler_name}
```
