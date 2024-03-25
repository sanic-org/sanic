---
title: Sanic 应用程序
---

# Sanic 应用程序

请参阅API文档： [sanic.app](/api/sanic.app)

## 实例(Instance)

.. column::

```
最基本的构建块是 :class: `sanic.app.Sanic` 实例。这不是必需的，但习惯是在名为 `server.py` 的文件中实例化它。
```

.. column::

````
```python
# /path/to/server.py

from sanic import Sanic

app = Sanic("MyHelloWorldApp")
```
````

## 应用上下文(Application context)

大多数应用程序都需要跨代码库的不同部分共享/重用数据或对象。 Sanic 帮助在应用程序实例上提供 `ctx` 对象。 它是开发者附加应用整个生命周期中应该存在的任何对象或数据的可用空间。

.. column::

```
最常见的模式是将数据库实例附加到应用程序中。
```

.. column::

````
```python
app = Sanic("MyApp")
app.ctx.db = Database()
```
````

.. 列:

```
虽然前面的示例可以工作并且具有说明性，但通常将对象在应用的开始或结束的生命周期里添加是比较合适的
```

.. column::

````
```python
app = Sanic("MyApp")

@app.before_server_start
async def attach_db(app, loop):
    app.ctx.db = Database()
```
````

## App 注册表(App Registry)

.. column::

```
当您实例化一个 Sanic 实例时，它可以稍后从 Sanic 应用程序注册表中检索。 例如，如果您需要从无法访问的地方访问您的 Sanic 实例，这可能是有用的。
```

.. column::

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

.. column::

```
If you call `Sanic.get_app("non-existing")` on an app that does not exist, it will raise :class:`sanic.exceptions.SanicException` by default. You can, instead, force the method to return a new instance of Sanic with that name.
```

.. 列:

````
```python
app = Sanic.get_app(
    "不存在",
    force_create=True,
)
```
````

.. 列:

```
如果有 **只有** 个Sanic 实例注册，那么调用 `Sanic.get_app()` 但没有参数将返回这个实例
```

.. 列:

````
```python
Sanic("我唯一的应用")

app = Sanic.get_app()
```
````

## 配置

.. 列:

```
Sanic 持有`Sanic` 实例的 `config` 属性中的配置。配置可以像字典一样使用 do-notation **OR** 进行修改。
```

.. 列:

````
```python
app = Sanic('myapp')

app.config.DB_NAME = 'appdb'
app.config['DB_USER'] = 'appuser'

db_setting= {
    'DB_HOST': 'localhost',
    'DB_NAME': 'appdb',
    'DB_USER': 'appuser'
}
app.config.update(db_settings)
```
````

.. 注：浮动通知

````
config key _should_ 是上层的，但这主要是通过公约进行的，小写将大部分时间起作用。
```python
app.config.GOD = "yay!"
app.config.bad = "board"
```
````

稍后会有很多[更详细的配置](../running/configuration.md)。

## 工厂模式

Many of the examples in these docs will show the instantiation of the :class:`sanic.app.Sanic` instance in a file called `server.py` in the "global scope" (i.e. not inside a function). 这是非常简单的“hello world”风格应用程序的常见模式，但使用工厂模式往往是有益的。

"工厂" 只是一个函数返回你想要使用的对象的实例。 这允许您抽象对象的实例化, 但也可能使它更容易隔离应用程序实例。

.. 列:

```
超级简单的出厂模式看起来像这样：
```

.. 列:

````
```python
# ./path/to/server.py
从.path.to.config 从.path.to.some中导入 Sanic
中导入MyConfig
lueprint导入bp


def create_app(config=MyConfig) -> Sanic:
    app = Sanic("MyApp", config=config)
    app. lueprint(bp)
    return app
```
````

.. 列:

```
当我们稍后开始运行 Sanic时，你会知道Sanic CLI 可以检测到这种模式并使用它来运行你的应用程序。
```

.. 列:

````
```sh
sanic path.to.server:create_app
```
````

## 自定义

Sanic 应用程序实例可以通过各种不同的实例实例为您的应用程序需要量身定制的。

详情请查看[API 文档](/api/sanic.app)。

### 自定义配置

.. 列:

```
This simplest form of custom configuration would be to pass your own object directly into that Sanic application instance

If you create a custom configuration object, it is *highly* recommended that you subclass the :class:`sanic.config.Config` option to inherit its behavior. You could use this option for adding properties, or your own set of custom logic.

*Added in v21.6*
```

.. 列:

````
```python
from sanic.config 导入配置

class MyConfig(Config):
    FOO = "bar"

app = Sanic(..., config=MyConfig())
```
````

.. 列:

```
此功能的一个有用例子是如果您想使用一个格式不同于 [supported]的配置文件 (. /running/configuration.md#using-sanicupdateconfig)。
```

.. 列:

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

### 自定义环境

.. 列:

```
By default, the application context is a [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) that allows you to set any properties you want on it. However, you also have the option of passing any object whatsoever instead.

*Added in v21.6*
```

.. 列:

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

### 自定义请求

.. 列:

```
有时有你自己的 `Request` 类并告诉Sanic 使用它而不是默认值是有帮助的。 一个例子是如果您想修改默认“请求”。 d`生成器。



... 注意：重要的

    必须记住，您正在通过 *class* 而不是类的实例。
```

.. 列:

````
```python
导入时间

from sanic import Request, Sanic, 文本

class NanoSecondRequest(请求):
    @classmethodology
    def generate_id(*_):
        返回时间 ime_ns()

app = Sanic(..., request_class=NanoSecondRequest)

@app.get("/")
async def handler(request):
    retext(str(request.id))
```
````

### 自定义错误处理程序

.. 列:

```
查看[异常处理](../best practices/exceptions.md#custom-error-handling)
```

.. 列:

````
```python
来自病原体。 andlers 导入 ErrorHandler

class CustomErrorHandler(ErrorHandler):
    def default(自己，请求，请求) 异常:
        '' 处理错误, 没有分配给'''
        # 你自定义错误处理逻辑。 ..
        return super().default(请求，异常)

app = Sanic(..., error_handler=CustomErrorHandler())
```
````

### 自定义转储函数

.. 列:

```
有时可能需要或需要提供一个自定义函数来序列一个 JSON 数据对象。
```

.. 列:

````
```python
import ujson

dumps = partial(ujson.dumps, escape_forward_slashes=False)
app = Sanic(__name__, dumps=dumps)
```
````

.. 列:

```
或者，或许使用另一个库或创建您自己的库。
```

.. 列:

````
```python
from orjson import dumps

app = Sanic("MyApp", dumps=dumps)
```
````

### 自定义负载函数

.. 列:

```
类似于“dumps”，您也可以为反序列化数据提供自定义函数。

*添加于v22.9*
```

.. 列:

````
```python
from orjson import load

app = Sanic("MyApp", loads=loads)
```
````

### 自定义类型的应用程序

从 v23.6开始，默认Sanic 应用程序实例的正确类型注释是：

```python
sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]
```

它指的是两种一般类型：

1. 第一个是配置对象的类型。 It defaults to :class:`sanic.config.Config`, but can be any subclass of that.
2. 第二种是应用程序上下文的类型。 它默认了 [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace)，但上面显示的 **任何对象** 。

让我们看看如何改变类型的一些例子。

.. 列:

```
Consider this example where we pass a custom subclass of :class:`sanic.config.Config` and a custom context object.
```

.. 列:

````
```python
从病原体导入Sanic
onfig importing config

clusive Config(Config):
    pass

appp = Sanic("test", config=CustomConfig())
reenal_type(app) # N: 公开类型是 "sanic" pp.Sanic[main.CustomConfig, types.SimpleNamespace]"
```
```
sanic.app.Sanic[main.CustomConfig, types.SimpleNamespace]
```
````

.. 列:

```
同样，当传递自定义上下文对象时，类型将会改变以反映这一点。
```

.. 列:

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

.. 列:

```
当然，您可以将配置和上下文设置为自定义类型。
```

.. 列:

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

如果您为应用程序实例创建一个自定义类型别名，以便您可以使用它来批注听器和处理器，此模式就特别有用。

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
from myapp.types importing MyApp

def add_listeners(app: MyApp):
    @app. efor_server_start
    async def before_server_start(app: MyApp):
        # 使用您完全输入的应用程序实例
        正在等待应用。 tx.db.connect()
```

```python
# ./path/to/server.py
从 myapp.types 导入 MyApp
从myapp.context 从myapp 导入 MyContext
onfig importer MyConfig
from myapp.listeners importing add_listeners

app = Sanic("myapp", config=MyConfig(), ctx=MyContext())
add_listeners(app)
```

_添加于 v23.6_

### 自定义已输入请求

Sanic还允许您自定义请求对象的类型。 如果您想要将自定义属性添加到请求对象，这是有用的， 或者能够访问您输入的应用程序实例的自定义属性。

Sanic 请求实例的正确、默认类型是：

```python
sanic.request.Request[
    sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace],
    types.SimpleNamespace
]
```

它指的是两种一般类型：

1. 第一个是应用程序实例的类型。 默认为`sanic.app.Sanic[sanic.config.Config、types.SimpleNamespace]`，但可以是这个分类中的任何一个子类。
2. 第二种是请求上下文的类型。 它默认了 `types.SimpleNamespace`，但可以在 [自定义请求](#custom-requests) 中显示**任何对象** 。

让我们看看如何改变类型的一些例子。

.. 列:

```
扩展到上面的完整示例，在这个示例中有一个自定义应用程序实例的类型别名， 我们还可以创建一个自定义请求类型，以便我们可以访问这些类型的注释。

当然，您不需要输入别名才能工作。 我们只是在这里显示它们来削减显示的代码数量。
```

.. 列:

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

.. 列:

```
也许您有一个生成自定义上下文对象的自定义请求对象。 您可以输入注解来正确访问这些属性，如这里所示。
```

.. 列:

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

在[自定义请求上下文](./request#custom-request-context)部分查看更多信息。

_添加于 v23.6_
