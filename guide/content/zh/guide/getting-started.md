# 正在开始

在我们开始之前，请确保您正在运行 Python 3.8或更高版本。 目前，Sanic正在与 Python 版本 3.8 - 3.11一起工作。

## 安装

```sh
pip 安装sanic
```

## 您好，全局应用程序

.. 列:

```
If you have ever used one of the many decorator based frameworks, this probably looks somewhat familiar to you.



.. note:: 

    If you are coming from Flask or another framework, there are a few important things to point out. Remember, Sanic aims for performance, flexibility, and ease of use. These guiding principles have tangible impact on the API and how it works.
```

.. 列:

````
```python
from sanic importing Sanic
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app. et("/")
async def hello_world(request):
    return text("Hello, world.")
```
````

### 重要的注意事项

- 每个请求处理程序都可以同步(`def hello_world`)，也可以同步(`async def hello_world`)。 除非你有明确的理由，否则总是使用 "async"。
- "request" 对象始终是你处理器的第一个参数。 其它框架在要导入的上下文变量中传递这一点。 在 "async" 世界中 这种情况不会很好地发挥作用，因此更容易(更干净和业绩更好)对此加以明确说明。
- 您**必须** 使用响应类型。 其他框架允许您有一个返回值，如：`return "Hello, world."` 或者 `return {"foo": "bar"}`。 但是，为了进行这种隐性的呼叫，链中的某个地方需要花费宝贵的时间来确定你的意思。 因此，萨尼克以牺牲这个容易为代价，决定要求明确呼叫。

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
