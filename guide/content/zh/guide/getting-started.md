# 快速上手

在我们开始之前，请确保您正在运行 Python 3.8或更高版本。 目前，Sanic可以运行在Python 版本 3.8 - 3.11上。

## 安装

```sh
pip install sanic
```

## Hello, world 应用案例

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

### 正在运行

.. 列:

```
让我们把上面的文件保存为 `server.py`。然后启动它。
```

.. 列:

````
```sh
sanic server
```
````

.. 注：

```
这**另一个**重要的区别。其它框架包含在开发服务器中，并明确表示它仅用于开发用途。 Sanic的情况正好相反。 

**打包服务器已准备就绪。**
```

## 无声扩展

无知的特色清单的目的是要有一个清洁和无见解的特色清单。 该项目不想要求您以某种方式构建您的应用程序，并试图避免指定特定的开发模式。 有一些第三方插件由社区构建和维护，用于添加额外的功能，这些功能不符合核心存储库的要求。

但是，为了帮助API开发者\*\*，Sanic 组织维持一个名为[Sanic Extensions](../plugins/sanic-ext/getting-started.md)的官方插件，提供各种各样的谷物，其中包括：

- **OpenAPI** 文档与 Redoc 或 Swagger
- **CORS** 保护
- **依赖注入** 对路由处理程序
- 请求查询参数和正文输入 **验证**
- 自动创建 `HEAD`, `OPTIONS` 和 `TRACE` 终点
- 预定义的端点特定响应序列转换器

设置它的首选方法是与 Sanic 一起安装，但你也可以自己安装这个软件包。

.. 列:

````
```sh
pip install sanic[ext]
```
````

.. 列:

````
```sh
pip install sanic sanic-ext
```
````

从 v21.12开始，萨尼语将在同一环境中自动设置萨尼克扩展。 您还可以访问另外两个应用程序属性：

- `app.extend()` - 用于配置 Sanic 扩展
- `app.ext` - 附加到应用程序的`Extend`实例

请参阅[插件文档](../plugins/sanic-ext/getting-started.md) 了解如何使用和使用插件的更多信息
