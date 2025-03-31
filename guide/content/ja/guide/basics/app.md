---
title: サニック・アプリケーション
---

# サニック・アプリケーション

API ドキュメント: [sanic.app](/api/sanic.app) を参照してください。

## インスタンス

.. 列::

```
最も基本的なビルディングブロックは、 :class:`sanic.app.Sanic`インスタンスです。 これは必須ではありませんが、カスタムは `server.py` という名前のファイルでインスタンス化します。
```

.. 列::

````
```python
# /path/to/server.py

from sanic import Sanic

app = Sanic("MyHelloWorldApp")
```
````

## アプリケーションのコンテキスト

ほとんどのアプリケーションは、コードベースの異なる部分にわたってデータやオブジェクトを共有/再利用する必要があります。 Sanicはアプリケーションインスタンスに`ctx`オブジェクトを提供するのに役立ちます。 開発者がアプリケーションの寿命を通じて存在すべきあらゆるオブジェクトやデータを添付するための空き領域です。

.. 列::

```
最も一般的なパターンは、アプリケーションにデータベース・インスタンスをアタッチすることです。
```

.. 列::

````
```python
app = Sanic("MyApp")
app.ctx.db = Database()
```
````

.. 列::

```
While the previous example will work and is illustrative, it is typically considered best practice to attach objects in one of the two application startup [listeners](./listeners).
```

.. 列::

````
```python
app = Sanic("MyApp")

@app.before_server_start
async def attach_db(app, loop):
    app.ctx.db = Database()
```
````

## アプリのレジストリ

.. 列::

```
Sanicインスタンスをインスタンス化すると、Sanicアプリレジストリから後で取得できます。 たとえば、Sanicインスタンスにアクセスする必要がある場合には、Sanicインスタンスにアクセスできない場合などに便利です。
```

.. 列::

````
```python
# ./path/to/server.py
from sanic import Sanic

app = Sanic("my_awesome_server")

# ./path/to/somewhere_else.py
from sanic import Sanic

app = Sanic.get_app("my_awesome_server")
```
````

.. 列::

```
存在しないアプリで `Sanic.get_app("non-existing")` を呼び出すと、 :class:`sanic.exceptions が発生します。 anicException`はデフォルトです。代わりに、その名前を持つSanicの新しいインスタンスを強制的に返すことができます。
```

.. 列::

````
```python
app = Sanic.get_app(
    "non-existing",
    force_create=True,
)
```
````

.. 列::

```
Sanic インスタンスが登録されている場合は、引数のない`Sanic.get_app()`を呼び出すと、そのインスタンスが返されます。
```

.. 列::

````
```python
Sanic("My only app")

app = Sanic.get_app()
```
````

## 設定

.. 列::

```
Sanicは`Sanic`インスタンスの`config`属性の設定を保持しています。設定は辞書のようにドット表記を使って**どちらか**変更できます。
```

.. 列::

````
```python
app = Sanic('myapp')

app.config.DB_NAME = 'appdb'
app.config['DB_USER'] = 'appuser'

db_settings = {
    'DB_HOST': 'localhost',
    'DB_NAME': 'appdb',
    'DB_USER': 'appuser'
}
app.config.update(db_settings)
```
````

.. Note:: Heads Up

````
設定キー _should_ は大文字ですが、これは主に規則によって行われ、小文字はほとんどの場合動作します。
```python
app.config.GOOD = "yay!"
app.config.bad = "boo"
```
````

後ほど、format@@0(../running/configuration.md) があります。

## 出荷時のパターン

これらのドキュメントの多くの例では、 :class:`sanic.appのインスタンス化が表示されます。 グローバルスコープ内の `server.py` というファイル内の anic` インスタンス（すなわち関数内ではない）。 これは非常に単純な "hello world" スタイルのアプリケーションでは一般的なパターンですが、代わりにファクトリパターンを使用することはしばしば有益です。

"factory" は、使用したいオブジェクトのインスタンスを返す関数です。 これにより、オブジェクトのインスタンス化を抽象化できますが、アプリケーションインスタンスを簡単に分離できるようになります。

.. 列::

```
超単純なファクトリパターンは次のようになります:
```

.. 列::

````
```python
# ./path/to/server.py
from sanic import Sanic
from .path.to.config import MyConfig
from .path.to.some.blueprint import bp


def create_app(config=MyConfig) -> Sanic:
    app = Sanic("MyApp", config=config)
    app.blueprint(bp)
    return app
```
````

.. 列::

```
Sanic を後で実行すると、Sanic CLI がこのパターンを検出し、アプリケーションを実行するために使用できることがわかります。
```

.. 列::

````
```sh
sanic path.to.server:create_app
```
````

## カスタマイズ

Sanicアプリケーションインスタンスは、インスタンス化時にさまざまな方法でアプリケーションのニーズに合わせてカスタマイズできます。

詳細については、[API docs](/api/sanic.app) を参照してください。

### カスタム構成

.. 列::

```
This simplest form of custom configuration would be to pass your own object directly into that Sanic application instance

If you create a custom configuration object, it is *highly* recommended that you subclass the :class:`sanic.config.Config` option to inherit its behavior. You could use this option for adding properties, or your own set of custom logic.

*Added in v21.6*
```

.. 列::

````
```python
from sanic.config import Config

class MyConfig(Config):
    FOO = "bar"

app = Sanic(..., config=MyConfig())
```
````

.. 列::

```
この機能の有用な例として、 [supported]とは異なる形式で設定ファイルを使用したい場合があります。 /running/configuration.md#using-sanicupdateconfig).
```

.. 列::

````
```python
from sanic import Sanic, text
from sanic.config import Config

class TomlConfig(Config):
    def __init__(self, *args, path: str, **kwargs):
        super().__init__(*args, **kwargs)

        with open(path, "r") as f:
            self.apply(toml.load(f))

    def apply(self, config):
        self.update(self._to_uppercase(config))

    def _to_uppercase(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        retval: Dict[str, Any] = {}
        for key, value in obj.items():
            upper_key = key.upper()
            if isinstance(value, list):
                retval[upper_key] = [
                    self._to_uppercase(item) for item in value
                ]
            elif isinstance(value, dict):
                retval[upper_key] = self._to_uppercase(value)
            else:
                retval[upper_key] = value
        return retval

toml_config = TomlConfig(path="/path/to/config.toml")
app = Sanic(toml_config.APP_NAME, config=toml_config)
```
````

### カスタム コンテキスト

.. 列::

```
デフォルトでは、アプリケーションのコンテキストは[`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types)です。 任意のプロパティを設定することができます。 ただし、任意のオブジェクトを渡すオプションもあります。

*v21.6*に追加されました
```

.. 列::

````
```python
app = Sanic(..., ctx=1)
```

```python
app = Sanic(..., ctx={})
```

```python
class MyContext:
    ...

app = Sanic(..., ctx=MyContext())
```
````

### カスタムリクエスト

.. 列::

```
It is sometimes helpful to have your own `Request` class, and tell Sanic to use that instead of the default. One example is if you wanted to modify the default `request.id` generator.



.. note:: Important

    It is important to remember that you are passing the *class* not an instance of the class.
```

.. 列::

````
```python
import time

from sanic import Request, Sanic, text

class NanoSecondRequest(Request):
    @classmethod
    def generate_id(*_):
        return time.time_ns()

app = Sanic(..., request_class=NanoSecondRequest)

@app.get("/")
async def handler(request):
    return text(str(request.id))
```
````

### カスタムエラーハンドラの設定

.. 列::

```
詳細については format@@0(../best-practices/exceptions.md#custom-error-handling) を参照してください。
```

.. 列::

````
```python
from sanic.handlers import ErrorHandler

class CustomErrorHandler(ErrorHandler):
    def default(self, request, exception):
        ''' handles errors that have no error handlers assigned '''
        # You custom error handling logic...
        return super().default(request, exception)

app = Sanic(..., error_handler=CustomErrorHandler())
```
````

### カスタムダンプ 関数

.. 列::

```
JSONデータにオブジェクトをシリアライズするカスタム関数を提供することが必要な場合や望ましい場合もあります。
```

.. 列::

````
```python
import ujson

dump = partial(ujson.dumps, escape_forward_slashes=False)
app = Sanic(__name__, dumps=dumps)
```
````

.. 列::

```
または、おそらく別のライブラリを使用するか、独自のライブラリを作成します。
```

.. 列::

````
```python
from orjson import dump

app = Sanic("MyApp", dumps=dumps)
```
````

### カスタム読み込み機能

.. 列::

```
`dumps`と同様に、データをデシリアライズするためのカスタム関数を提供することもできます。

*v22.9*に追加されました
```

.. 列::

````
```python
from orjson import loads

app = Sanic("MyApp", loads=loads)
```
````

### カスタムタイプされたアプリケーション

デフォルトの Sanic アプリケーションインスタンスの正しい型アノテーションは v23.6 で始まります。

```python
sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]
```

2つの一般的な型を指します。

1. 最初は、構成オブジェクトのタイプです。 デフォルトでは、 :class:`sanic.config.Config` になっていますが、そのサブクラスにすることができます。
2. 二つ目はアプリケーションコンテキストのタイプです。 デフォルトは [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) ですが、上記のように**任意のオブジェクト** にできます。

型がどのように変化するかの例を見てみましょう。

.. 列::

```
:class:`sanic.config.Config` のカスタムサブクラスとカスタムコンテキストオブジェクトを渡す例を考えてみましょう。
```

.. 列::

````
```python
from sanic import Sanic
from sanic.config import Config

class CustomConfig(Config):
    pass

app = Sanic("test", config=CustomConfig())
reveal_type(app) # N: Revealed type is "sanic.app.Sanic[main.CustomConfig, types.SimpleNamespace]"
```
```
sanic.app.Sanic[main.CustomConfig, types.SimpleNamespace]
```
````

.. 列::

```
同様に、カスタムコンテキストオブジェクトを渡す場合、型はそれを反映するように変更されます。
```

.. 列::

````
```python
from sanic import Sanic

class Foo:
    pass

app = Sanic("test", ctx=Foo())
reveal_type(app)  # N: Revealed type is "sanic.app.Sanic[sanic.config.Config, main.Foo]"
```
```
sanic.app.Sanic[sanic.config.Config, main.Foo]
```
````

.. 列::

```
もちろん、設定とコンテキストの両方をカスタムタイプに設定できます。
```

.. 列::

````
```python
from sanic import Sanic
from sanic.config import Config

class CustomConfig(Config):
    pass

class Foo:
    pass

app = Sanic("test", config=CustomConfig(), ctx=Foo())
reveal_type(app)  # N: Revealed type is "sanic.app.Sanic[main.CustomConfig, main.Foo]"
```
```
sanic.app.Sanic[main.CustomConfig, main.Foo]
```
````

このパターンは、アプリケーションインスタンスにカスタム型エイリアスを作成し、リスナーやハンドラに注釈を付けるために使用する場合に特に便利です。

```python
# ./path/to/types.py
from sanic.app import Sanic
from sanic.config import Config
from myapp.context import MyContext
from typing import TypeAlias

MyApp = TypeAlias("MyApp", Sanic[Config, MyContext])
```

```python
# ./path/to/listeners.py
from myapp.types import MyApp

def add_listeners(app: MyApp):
    @app.before_server_start
    async def before_server_start(app: MyApp):
        # do something with your fully typed app instance
        await app.ctx.db.connect()
```

```python
# ./path/to/server.py
from myapp.types import MyApp
from myapp.context import MyContext
from myapp.config import MyConfig
from myapp.listeners import add_listeners

app = Sanic("myapp", config=MyConfig(), ctx=MyContext())
add_listeners(app)
```

_V23.6_に追加されました

### カスタムタイプのリクエスト

Sanicでは、リクエストオブジェクトのタイプをカスタマイズすることもできます。 これは、リクエストオブジェクトにカスタムプロパティを追加する場合に便利です。 または型付けされたアプリケーションインスタンスのカスタムプロパティにアクセスできます。

サイニックリクエストインスタンスの正しいデフォルトタイプは次のとおりです:

```python
sanic.request.Request[
    sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace],
    types.SimpleNamespace
]
```

2つの一般的な型を指します。

1. 最初はアプリケーションインスタンスのタイプです。 デフォルトは `sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]` ですが、そのサブクラスは任意です。
2. 二つ目は、リクエストコンテキストのタイプです。 デフォルトは `types.SimpleNamespace` ですが、上記の [custom requests](#custom-requests) で表示されるように、 **任意のオブジェクト** にすることができます。

型がどのように変化するかの例を見てみましょう。

.. 列::

```
カスタマイズされたアプリケーションインスタンスに型エイリアスがある上記の完全な例を展開します 同じタイプの注釈にアクセスできるようにカスタムリクエストタイプを作成することもできます

もちろん、これを動作させるためにタイプエイリアスは必要ありません。 私たちは、表示されているコードの量を削減するためにそれらをここに示しているだけです。
```

.. 列::

````
```python
from sanic import Request
from myapp.types import MyApp
from types import SimpleNamespace

def add_routes(app: MyApp):
    @app.get("/")
    async def handler(request: Request[MyApp, SimpleNamespace]):
        # do something with your fully typed app instance
        results = await request.app.ctx.db.query("SELECT * FROM foo")
```
````

.. 列::

```
カスタムコンテキストオブジェクトを生成するカスタムリクエストオブジェクトがあるかもしれません。 ここに示すように、注釈を入力してIDEでこれらのプロパティに適切にアクセスできます。
```

.. 列::

````
```python
from sanic import Request, Sanic
from sanic.config import Config

class CustomConfig(Config):
    pass

class Foo:
    pass

class RequestContext:
    foo: Foo

class CustomRequest(Request[Sanic[CustomConfig, Foo], RequestContext]):
    @staticmethod
    def make_context() -> RequestContext:
        ctx = RequestContext()
        ctx.foo = Foo()
        return ctx

app = Sanic(
    "test", config=CustomConfig(), ctx=Foo(), request_class=CustomRequest
)

@app.get("/")
async def handler(request: CustomRequest):
    # Full access to typed:
    # - custom application configuration object
    # - custom application context object
    # - custom request context object
    pass
```
````

format@@0(./request#custom-request-context) セクションを参照してください。

_V23.6_に追加されました

