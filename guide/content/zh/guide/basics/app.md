---
title: Sanic 应用程序
---

# Sanic 应用程序

请参阅API文档： [sanic.app](/api/sanic.app)

## 实例（Instance）

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

大多数应用程序都需要跨代码库的不同部分共享/重用数据或对象。 Sanic 帮助在应用程序实例上提供 `ctx` 对象。 它是开发者可以在应用程序整个生命周期中附加任何应存在的对象或数据的自由空间。

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

.. column::

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

## App 注册(App Registry)

.. column::

```
当您实例化一个 Sanic 类时，它可以稍后从 `Sanic` 提供的方法`get_app()`中获取到这个实例。 例如，如果您需要从无法访问的地方访问您的 Sanic 实例，这可能是有用的。
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
如果您调用 Sanic.get_app("non-existing") 尝试去获取一个不存在的实例时，默认情况下它将引发 :class:`sanic.exceptions.SanicException`。但是，您也可以通过指定`force_create=True`强制该方法返回具有该名称的 Sanic 的新实例。
```

.. column::

````
```python
app = Sanic.get_app(
    "non-existing",
    force_create=True,
)
```
````

.. column::

```
如果有 **只有** 一个Sanic 实例，那么不带参数，直接调用 `Sanic.get_app()` 将返回这个实例
```

.. column::

````
```python
Sanic("My only app")

app = Sanic.get_app()
```
````

## 配置(Configuration)

.. 列:

```
Sanic 将所有的配置文件存储在`Sanic`实例的`config`属性当中，你可以通过`.`点的方式或者直接把`Sanic.config`当作一个数组去修改配置
```

.. column::

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

.. note:: 注意一下

````
通常来说，Config 的键应该是大写的，但是多数情况下，小写也能正常工作
```python
app.config.GOOD = "yay!"
app.config.bad = "boo"
```
````

这里有更多关于配置的使用方法[更详细的配置](../running/configuration.md)。

## 工厂模式(Factory pattern)

文档中大多数案例都是在`server.py`的顶层（不是在一个函数中）实例化Sanic这个对象 :class:`sanic.app.Sanic`  这是非常简单的“hello world”风格应用程序的常见形式，但使用工厂模式往往具有更高的扩展性。

"工厂" 只是一个函数返回你想要使用的对象的实例。 这允许您抽象对象的实例化, 但也可能使它更容易隔离应用程序实例。

.. column::

```
一个简单的出厂模式看起来像这样：
```

.. column::

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

.. column::

```
当我们稍后开始运行 Sanic时，你会知道Sanic CLI 可以检测到这种模式并使用它来运行你的应用程序。
```

.. column::

````
```sh
sanic path.to.server:create_app
```
````

## 自定义(Customization)

在实例化阶段，可以根据您的应用程序需求以多种方式自定义 Sanic 应用程序实例。

详情请查看[API 文档](/api/sanic.app)。

### 自定义配置(Custom configuration)

.. column::

```
这种最简单的自定义配置形式是将您自己的对象直接传递到该 Sanic 应用程序实例中

如果您创建自定义配置对象，*强烈*建议您对 :class:`sanic.config.Config` 选项进行子类化以继承其行为。 您可以使用此选项添加属性或您自己的一组自定义逻辑。

*在 v21.6 中添加*
```

.. column::

````
```python
from sanic.config import Config

class MyConfig(Config):
    FOO = "bar"

app = Sanic(..., config=MyConfig())
```
````

.. column::

```
此功能的一个有用例子是如，果您想使用一个格式不同于 [supported]的配置文件 (. /running/configuration.md#using-sanicupdateconfig)。
```

.. column::

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

### 自定义上下文

.. column::

```
默认情况下，应用程序上下文是一个 [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace)，它允许您设置您想要的任何属性。 但是，您也可以选择传递任何对象。

*在 v21.6 中添加*
```

.. column::

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

.. column::

```
有时拥有自己的“Request”类会很有帮助，并告诉 Sanic 使用它而不是默认的。 一个例子是，如果您想修改默认的“request.id”生成器。



.. note:: 重点

重要的是要记住，您传递的是 *class* 而不是该类的实例。
```

.. column::

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

### 自定义错误响应函数(Custom error handler)

.. column::

```
查看[异常处理](../best practices/exceptions.md#custom-error-handling) 获取更多信息
```

.. column::

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

### 自定义dumps函数

.. column::

```
有时可能需要或需要提供一个自定义函数来序列一个 JSON 数据对象。
```

.. column::

````
```python
import ujson

dumps = partial(ujson.dumps, escape_forward_slashes=False)
app = Sanic(__name__, dumps=dumps)
```
````

.. column::

```
或者，或许使用另一个库或创建您自己的库。
```

.. column::

````
```python
from orjson import dumps

app = Sanic("MyApp", dumps=dumps)
```
````

### 自定义loads函数

.. column::

```
类似于“dumps”，您也可以为反序列化数据提供自定义函数。

*添加于v22.9*
```

.. column::

````
```python
from orjson import loads

app = Sanic("MyApp", loads=loads)
```
````

### 自定义类型的应用程序

从 v23.6开始，默认Sanic 应用程序实例的正确类型注释是：

```python
sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]
```

它指的是两种一般类型：

1. 第一个是配置对象的类型。 它默认为 :class: `sanic.config.Config`，但可以是它的任何子类。
2. 第二种是应用程序上下文的类型。 它默认了 [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace)，但上面显示的 **任何对象** 。

让我们看看如何改变类型的一些例子。

.. column::

```
考虑这个示例，其中我们传递了 :class:`sanic.config.Config` 的自定义子类和自定义上下文对象。
```

.. column::

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

.. column::

```
同样，当传递自定义上下文对象时，类型将会改变以反映这一点。
```

.. column::

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

.. column::

```
当然，您可以将配置和上下文设置为自定义类型。
```

.. column::

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

如果为应用程序实例创建了自定义类型别名，则这种模式特别有用，因为您可以使用它来注解监听器和处理器。

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

_添加于 v23.6_

### 自定义request请求

Sanic还允许您自定义请求对象的类型。 如果您想向请求对象添加自定义属性，或者能够访问具有类型的应用程序实例的自定义属性，这将非常有用。

Sanic 请求实例的正确、默认类型是：

```python
sanic.request.Request[
    sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace],
    types.SimpleNamespace
]
```

它指的是两种一般类型：

1. 第一个是应用程序实例的类型。 默认为`sanic.app.Sanic[sanic.config.Config、types.SimpleNamespace]`，但可以是这个分类中的任何一个子类。
2. 第二种是请求上下文的类型。 默认为`types.SimpleNamespace`，但可以是如上所示 [自定义请求](#custom-requests) 中的**任何对象**。

让我们看看如何改变类型的一些例子。

.. column::

```
在上述包含自定义应用程序实例类型别名的完整示例基础上，我们还可以创建自定义请求类型，以便访问相同的类型注解。

当然，要实现这一功能并不需要类型别名。此处仅展示它们是为了减少显示的代码量。
```

.. column::

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

.. column::

```
也许您有一个生成自定义上下文对象的自定义请求对象。您可以像这里所示那样通过类型注解正确地使用 IDE 访问这些属性。
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

在[自定义请求上下文](./request.md#custom-request-context)部分查看更多信息。

_添加于 v23.6_

