# 快速上手

Before we begin, make sure you are running Python 3.9 or higher. Currently, Sanic is works with Python versions 3.9 – 3.13.

## 安装（Install）

```sh
pip install sanic
```

## Helloworld案例

.. column::

```
如果你之前有使用过基于装饰器的web应用，那么Sanic的语法可能对你来说会很亲切。


.. 注意:: 

    如果您来自 Flask 或其他框架，有一些重要的事情需要指出。 请记住，Sanic 的目标是性能(performance)、灵活性(flexibility) 和易用性(ease of use)。 这些指导原则对 API 及其工作方式产生了切实的影响。
```

.. column::

````
```python
from sanic import Sanic
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```
````

### 重要提示

- 每一个请求响应函数都可以使用同步方式（`def hello_world`）和异步方式（`async def hello_world`）进行声明。 除非您有一个明确的需求和完善的使用方法，否则的话，请尽量使用 async 来声明响应函数。
- `request` 对象始终是响应函数的第一个参数。 其他框架在需要导入的上下文变量中进行传递。 在 `async`的世界里，如果使用隐式传递，那么它将无法完美的运行，更何况还要兼顾简洁且高效的表现形式。
- 您 必须 使用 <code>Response</code> 或继承自 <code>Response</code> 的类作为响应类型。 在许多其他框架中，它们允许您使用诸如 `return "Hello World"` 或者 `return {"foo":"bar"}` 的方式来进行返回， 但是为了执行这类隐式调用，需要在响应流程中的某个位置花费大量的时间来确定您到底想要表达什么意思。 因此，在Sanic的返回语句中，需要明确的指定返回的数据类型（eg `return json({"foo":"bar"})` 或 `return text("Hello world")`）

### 运行(Running)

.. column::

```
让我们把上面的文件保存为 `server.py`。然后启动它。
```

.. column::

````
```sh
sanic server
```
````

.. note::

```
这**另一个**重要的区别。其它框架包含在开发服务器中，并明确表示它仅用于开发用途。 Sanic的情况正好相反。 

**Sanic内置的web服务器是生产就绪的。**
```

## Sanic 拓展

Sanic 有意打造一个干净且不带偏见的功能列表。 该项目不想要求您以某种方式构建应用程序，并试图避免指定特定的开发模式。 有许多由社区构建和维护的第三方插件，用于添加不符合核心库要求的附加功能。

但是，为了**帮助API开发者**，Sanic 组织维护了一个名为[Sanic Extensions](../plugins/sanic-ext/getting-started.md)的官方插件，提供各种各样的常见解决方案，其中包括：

- 使用 **Redoc** 和/或 **Swagger** 编写 OpenAPI 文档
- **CORS** 保护
- 将其他对象通过 **Dependency injection** （依赖注入）到路由处理程序中
- 请求查询参数和正文输入的**验证器**（validation）
- **自动创建** HEAD、OPTIONS 和 TRACE 入口（auto create）
- - 预先定义好的**序列化函数**(eg `json` `text`)、作用于不同的路由入口（serializers）

最好的安装方式就是在安装 Sanic 的同时一并安装 Sanic 拓展，当然，您也可以独立安装：

.. column::

````
```sh
pip install sanic[ext]
```
````

.. column::

````
```sh
pip install sanic sanic-ext
```
````

从 v21.12 开始，如果处于同一环境中，Sanic 将自动安装 Sanic 扩展。 您可以通过以下的两个属性来进行访问拓展功能:

- `app.extend()` - 用于配置 Sanic 扩展
- `app.ext` - 注入到应用程序的扩展实例

请参阅[插件文档](../plugins/sanic-ext/getting-started.md) 了解如何使用和使用插件的更多信息
