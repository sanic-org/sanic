---
title: 神经扩展 - 依赖注入量
---

# 依赖注入次数

依赖注入是基于定义函数签名向路由处理程序添加参数的方法。 具体而言，它看了处理器中参数的 **类型注释** 。 这在一些情况下可能是有用的，例如：

- 正在获取基于请求头的对象 (像当前会话用户)
- 将某些对象重置为特定类型
- 使用请求对象预获取数据
- 自动注入服务

`Extend`实例有两种基本方法用于依赖注入：较低级别的 `add_dependency`和较高级别的 `dependency`。

**较低级别**: `app.ext.add_dependency(...)`

- `type,`: 某些独特的类将是对象的类型
- `constructor: Optional[Callable[..., Any],` (OPTIONAL): 一个返回这种类型的函数

**更高级别**: `app.ext.dependency(...)`

- `obj: Any`: 任何你想要注入的对象
- `name: 可选的[str]`: 可以交替用作参考的一些名称

让我们在这里探索一些案例。

.. 警告：:

```
如果您在 v21.12之前使用依赖注入，较低级别的 API 方法被称为“注入”。 其后更名为`add_dependency`，并从v21开始。 2 `injection` 是一个 `add_dependency` 的别名。`injection` 方法已经不推荐在 v22.6 中移除。
```

## 基本执行

最简单的情况是只是重定一个数值。

.. 列:

```
如果你有一个模型，你想要根据匹配的路径参数生成，这可能是有用的。
```

.. 列:

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

.. 列:

```
将关键字参数传递给`type`参数的构造函数。前一个例子就是这个例子。
```

.. 列:

````
```python
flavor = IceCream(flavor="巧克力")
```
````

## 附加构造器

.. 列:

```
有时你可能也需要传递构造函数。这可能是一个函数，甚至可能是一个作为构造函数的类方法。 在这个例子中，我们正在创建一种叫做“人”的注射。 先得到`。

同样重要的是注意到这个示例。我们实际上正在注入**两个(2)** 对象！ 当然不需要这样做，但我们将根据函数签名注入物体。
```

.. 列:

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

当一个 `constructor` 传递到 `ext.add_dependency` (就像在这个例子中那样)时，它将被调用。 如果没有，则将通过调用 `type` 来创建对象。 有几件重要的事情要注意到一个\`构造器'：

1. 一个位置的 `request: Request' 参数是 *通常的*。 请参阅“人员”。 获取上面的方法作为示例使用 `request`和 [arbitrary-constructors](#arbitry-constructors) 来使用不需要`request\` 的电报。
2. 所有匹配的路径参数都作为关键字参数注入。
3. 依赖关系可以被链和嵌套。 请注意在前一个示例中，`Person` 数据集如何有一个 `PersonID` ？ 这意味着`PersonID`将首先被调用，并且在调用 `Person.create` 时将该值添加到关键字参数中。

## 任意构造器

.. 列:

```
有时您可能想要构建您注入的 _with_the `Request` 对象。 如果您有任意的类或函数创建您的对象，这是有用的。 如果传唤书中确实有任何必要的参数，那么传唤书本身应当是可以注射的物体。

如果您有服务或其他类型的对象只能在单个请求的一生中存在，这是非常有用的。 例如，您可以使用此模式从数据库池中拉取单个连接。
```

.. 列:

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

_添加于 v22.9_

## 来自 `Request` 的对象

.. 列:

````
有时您可能想要从请求中提取详细信息并预先处理。 例如，您可以将 JSON 投射到一个 Python 对象，然后添加一些基于数据库查询的附加逻辑。

... 警告：: 

    如果您计划使用此方法，， 您应该注意到注射实际上发生在*先于*圣诞老人有机会阅读请求身体之前。 头应该已经消耗。 所以，如果你想要访问身体，你需要手动消耗在这个例子中看到。

    ``python
        正在等待请求。 eceive_body()
    ```


    这可以用于否则你可能:

    - 使用中间件预处理并添加某些内容到 "请求"。 tx`
    - 使用装饰器预处理并注入参数到请求处理程序

    在此示例 我们正在使用 `compile_profile` 构造函数中的 `Request` 对象来运行一个假DB 查询来生成并返回一个 `UserProfile` 对象。
````

.. 列:

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

## 注射服务

创建数据库连接池并将其存储在`app.ctx`对象上是常见的模式。 这将使它们能够在您的整个应用程序中使用，这肯定是一种方便。 然而，一个缺点是你不再有一个要处理的打字对象。 您可以使用依赖注入来解决这个问题。 首先，我们将使用下级`add_dependency`来显示这个概念，就像我们在前面的例子中所使用的那样。 但是，可以更好地使用更高级别的 \`依赖' 方法。

### 使用 `add_dependency` 的较低级别 API

.. 列:

```
这个操作非常类似于[最后一个例子](#objects-frow-the-request) 的目标是从 `Request` 对象中提取某些东西。 在这个示例中，在 `app.ctx` 实例上创建了一个数据库对象，正在返回依赖注入构造器。
```

.. 列:

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

### 较高级别的 API 使用 `dependency`

.. 列:

```
由于我们在添加依赖注入时有一个可用的实际的 *对象*，我们可以使用更高级别的 "依赖" 方法。 这将使写入模式变得更容易。

当您想要注入在应用程序实例整个生命周期中存在而不是请求具体的东西时，这个方法应该始终使用。 它对服务、第三方客户和连接池非常有用，因为它们没有具体要求。
```

.. 列:

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

## 通用类型

使用[通用类型](https://docs.python.org/3/library/typing.html#typing.Generic)时小心谨慎。 Sanic依赖注入的方式是匹配整个类型的定义。 因此，`Foo`与`Foo[str] `不同。 当尝试使用 [更高级别的 '依赖' 方法](#the-high-level-api-using-dependency)时，这可能特别棘手，因为这种类型被推断。

.. 列:

```
例如，由于没有`测试[str] `的定义，**不** 会正常工作。
```

.. 列:

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

.. 列:

```
要使这个示例发挥作用，您需要为您打算注入的类型添加一个明确的定义。
```

.. 列:

````
```python
import
from sanic import Sanic, text

T = typing.TypeVar("T")

class Test(键入)。 enric[T]:
    test: T

app = Sanic("taspp")
_sinleton = Test()
app. xt.add_dependency(Test[str], lambda: _sinleton)

@app.get("/")
def 测试 (请求, test: 测试[str]):
    ...
```
````

## 配置

.. 列:

```
By default, dependencies will be injected after the `http.routing.after` [signal](../../guide/advanced/signals.md#built-in-signals). Starting in v22.9, you can change this to the `http.handler.before` signal.
```

.. 列:

````
```python
app.config.INJECTION_SIGAL = "http.handler.before"
```
````

_添加于 v22.9_
