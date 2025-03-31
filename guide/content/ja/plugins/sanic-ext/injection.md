---
title: Sanic Extensions - 依存性インジェクション
---

# 依存性インジェクション

依存性インジェクションは、定義された関数署名に基づいてルートハンドラに引数を追加するメソッドです。 具体的には、ハンドラの引数の**型注釈**を見てみます。 これは以下のような場合に便利です。

- (現在のセッションユーザのような) リクエストヘッダに基づいてオブジェクトを取得しています
- 特定のオブジェクトを特定の型に再作成する
- リクエストオブジェクトを使用してデータを先読みする
- 自動注入サービス

`Extend` インスタンスには、依存注入に使用される2つの基本的なメソッドがあります。下位レベルの `add_dependency` と上位レベルの `dependency` です。

**低レベル**: `app.ext.add_dependency(...)`

- `type: Type,`: オブジェクトの型になるいくつかの一意のクラス。
- `constructor: Optional[Callable[..., Any]],` (OPTIONAL): その型を返す関数。

**より高いレベル**: `app.ext.dependency(...)`

- `obj: Any`: 注入したいすべてのオブジェクト
- `name: Optional[str]`: 参照として交互に使用できるいくつかの名前

ここでいくつかのユースケースを見てみましょう。

.. 警告::

```
v21.12 より前に依存性インジェクションを使用した場合、下位レベルの API メソッドは `injection` と呼ばれました。 それ以降、`add_dependency`に名前が変更され、v21で始まります。 2 `injection`は`add_dependency`のエイリアスです。`injection`メソッドはv22.6の削除のために非推奨となりました。
```

## 基本的な実装

最も単純なユースケースは、単に値を再キャストすることです。

.. 列::

```
これは、マッチしたパスパラメータに基づいて生成するモデルがある場合に便利です。
```

.. 列::

````
```python
@dataclass
class IceCream:
    flavor: str

    def __str__(self) -> str:
        return f"{self.flavor.title()} (Yum!)"

app.ext.add_dependency(IceCream)

@app.get("/<flavor:str>")
async def ice_cream(request, flavor: IceCream):
    return text(f"You chose: {flavor}")
```

```
$ curl localhost:8000/chocolate
You chose Chocolate (Yum!)
```
````

.. 列::

```
これは、`type`引数のコンストラクタにキーワード引数を渡すことで動作します。前の例はこれと同じです。
```

.. 列::

````
```python
flavor = IceCream(flavor="chocolate")
```
````

## 追加のコンストラクター

.. 列::

```
コンストラクタを渡す必要がある場合もあります。これは関数や、コンストラクタとして動作するclassメソッドであってもよいでしょう。 この例では、`Person を呼び出す注入を作成しています。 最初に「やり直す」。

この例でも重要なことは、実際に **two (2)** オブジェクトを注入していることです! もちろん、このようにする必要はありませんが、関数署名に基づいてオブジェクトを注入します。
```

.. 列::

````
```python
@dataclass
class PersonID:
    person_id: int

@dataclass
class Person:
    person_id: PersonID
    name: str
    age: int

    @classmethod
    async def create(cls, request: Request, person_id: int):
        return cls(person_id=PersonID(person_id), name="noname", age=111)


app.ext.add_dependency(Person, Person.create)
app.ext.add_dependency(PersonID)

@app.get("/person/<person_id:int>")
async def person_details(
    request: Request, person_id: PersonID, person: Person
):
    return text(f"{person_id}\n{person}")
```

```
$ curl localhost:8000/person/123
PersonID(person_id=123)
Person(person_id=PersonID(person_id=123), name='noname', age=111)
```
````

`constructor` が ext.add_dependency`(この例のように) に渡されたときに呼び出されます。 そうでない場合は、`type`を呼び出してオブジェクトを作成します。`constructor\`を渡すことについて、いくつかの重要なことに注意してください。

1. 位置`request: Request`引数は通常、期待されています。 `Person を見なさい。 上記の reate` メソッドは、`request` と format@@0(#arbitrary-constructors) を使用して、`request` を必要としない呼び出し元を使用する方法を例としています。
2. マッチしたパスパラメータはすべてキーワード引数として注入されます。
3. 依存関係はチェーンとネストが可能です。 前の例では、 `Person` dataclass が `PersonID` になっていることに注意してください。 つまり、 `PersonID` が最初に呼び出され、 `Person.create` を呼び出すときにその値がキーワード引数に追加されます。

## 任意のコンストラクター

.. 列::

```
時々、注入可能な _without_ を `Request` オブジェクトにしたいと思うかもしれません。 これは、オブジェクトを作成する任意のクラスや関数がある場合に便利です。 callable が必要な引数を持っている場合は、それ自体が注入可能なオブジェクトである必要があります。

これは、単一のリクエストの寿命のためにのみ存在すべきサービスやその他のタイプのオブジェクトがある場合に非常に便利です。 たとえば、このパターンを使用して、データベース プールから単一の接続をプルすることができます。
```

.. 列::

````
```python
class Alpha:
    ...

class Beta:
    def __init__(self, alpha: Alpha) -> None:
        self.alpha = alpha

app.ext.add_dependency(Alpha)
app.ext.add_dependency(Beta)

@app.get("/beta")
async def handler(request: Request, beta: Beta):
    assert isinstance(beta.alpha, Alpha)
```
````

_v22.9_に追加されました

## `Request`からのオブジェクト

.. 列::

````
Sometimes you may want to extract details from the request and preprocess them. You could, for example, cast the request JSON to a Python object, and then add some additional logic based upon DB queries.

.. warning:: 

    If you plan to use this method, you should note that the injection actually happens *before* Sanic has had a chance to read the request body. The headers should already have been consumed. So, if you do want access to the body, you will need to manually consume as seen in this example.

    ```python
        await request.receive_body()
    ```


    This could be used in cases where you otherwise might:

    - use middleware to preprocess and add something to the `request.ctx`
    - use decorators to preprocess and inject arguments into the request handler

    In this example, we are using the `Request` object in the `compile_profile` constructor to run a fake DB query to generate and return a `UserProfile` object.
````

.. 列::

````
```python
@dataclass
class User:
    name: str

@dataclass
class UserProfile:
    user: User
    age: int = field(default=0)
    email: str = field(default="")

    def __json__(self):
        return ujson.dumps(
            {
                "name": self.user.name,
                "age": self.age,
                "email": self.email,
            }
        )

async def fake_request_to_db(body):
    today = date.today()
    email = f'{body["name"]}@something.com'.lower()
    difference = today - date.fromisoformat(body["birthday"])
    age = int(difference.days / 365)
    return UserProfile(
        User(body["name"]),
        age=age,
        email=email,
    )

async def compile_profile(request: Request):
    await request.receive_body()
    profile = await fake_request_to_db(request.json)
    return profile

app.ext.add_dependency(UserProfile, compile_profile)

@app.patch("/profile")
async def update_profile(request, profile: UserProfile):
    return json(profile)
```

```
$ curl localhost:8000/profile -X PATCH -d '{"name": "Alice", "birthday": "2000-01-01"}'
{
    "name":"Alice",
    "age":21,
    "email":"alice@something.com"
}
```
````

## 注入サービス

データベース接続プールのようなものを作成し、 `app.ctx` オブジェクトに保存するのは一般的なパターンです。 これにより、アプリケーション全体で利用可能になります。これは確かに便利です。 しかし欠点の一つは、もはや一緒に作業する型付けされたオブジェクトを持っていないことです。 依存性注入を使用してこれを修正できます。 最初に、先ほどの例で使ったように、下位レベルの `add_dependency` を使ってコンセプトを示します。 しかし、より高いレベルの `dependency` メソッドを使うより良い方法があります。

### `add_dependency`を使用する下位レベルのAPI。

.. 列::

```
これは format@@0(#objects-from-the-request) に非常によく似ています。目的は `Request` オブジェクトから何かを抽出することです。 この例では、データベースオブジェクトが `app.ctx` インスタンス上に作成され、依存性インジェクションコンストラクタで返されます。
```

.. 列::

````
```python
class FakeConnection:
    async def execute(self, query: str, **arguments):
        return "result"

@app.before_server_start
async def setup_db(app, _):
    app.ctx.db_conn = FakeConnection()
    app.ext.add_dependency(FakeConnection, get_db)

def get_db(request: Request):
    return request.app.ctx.db_conn



@app.get("/")
async def handler(request, conn: FakeConnection):
    response = await conn.execute("...")
    return text(response)
```
```
$ curl localhost:8000/
result
```
````

### `dependency`を使用するより高いレベルのAPI。

.. 列::

```
依存性注入を追加するときに利用できる実際の *object* があるので、より高いレベルの `dependency` メソッドを使用できます。 これにより、パターンが書けるようになります。

アプリケーションインスタンスの寿命を通じて存在し、特定の要求ではない何かを注入する場合は、このメソッドを常に使用する必要があります。 特定の要求ではないため、サービス、サードパーティクライアント、および接続プールに非常に便利です。
```

.. 列::

````
```python
class FakeConnection:
    async def execute(self, query: str, **arguments):
        return "result"

@app.before_server_start
async def setup_db(app, _):
    db_conn = FakeConnection()
    app.ext.dependency(db_conn)

@app.get("/")
async def handler(request, conn: FakeConnection):
    response = await conn.execute("...")
    return text(response)
```
```
$ curl localhost:8000/
result
```
````

## 一般的なタイプ

format@@0(https://docs.python.org/3/library/typing.html#typing.Generic)を使用するときは、気をつけてください。 Sanicの依存性注入が機能する方法は、型の定義全体に一致することです。 したがって、`Foo` は `Foo[str] ` と同じではありません。 型が推測されるので、format@@0(#the-higher-level-api-using-dependency) を使用しようとすると、これは特に難しいことがあります。

.. 列::

```
例えば、`Test[str] `の定義がないため、これは **期待通りに動作しません** 。
```

.. 列::

````
```python
import typing
from sanic import Sanic, text

T = typing.TypeVar("T")

class Test(typing.Generic[T]):
    test: T

app = Sanic("testapp")
app.ext.dependency(Test())

@app.get("/")
def test(request, test: Test[str]):
    ...
```
````

.. 列::

```
この例を動作させるには、注入するタイプの明示的な定義を追加する必要があります。
```

.. 列::

````
```python
import typing
from sanic import Sanic, text

T = typing.TypeVar("T")

class Test(typing.Generic[T]):
    test: T

app = Sanic("testapp")
_singleton = Test()
app.ext.add_dependency(Test[str], lambda: _singleton)

@app.get("/")
def test(request, test: Test[str]):
    ...
```
````

## 設定

.. 列::

```
デフォルトでは、依存関係は `http.routing.after` [signal](../../guide/advanced/signals.md#built-in-signals) の後に注入されます。v22.9 以降は、`http.handler.before` 信号に変更できます。
```

.. 列::

````
```python
app.config.INJECTION_SIGNAL = "http.handler.before"
```
````

_v22.9_に追加されました
