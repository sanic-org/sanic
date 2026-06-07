---
title: Sanic 测试-入门开始
---

# 正在开始

Sanic Testing 是 _official_ 测试Sanic 客户。 它的主要用途是为萨尼克项目本身的测试提供动力。 然而，它也是一个易于使用的客户端，可以让您的 API 测试升级并快速运行。

## 最低要求

- **Python**: 3.7+
- **Sanic**: 21.3+

年龄在21岁以上的Sanic版本将此模块并入Sanic本身，作为“sanic.testing”。

## 安装

可从 PyPI 安装Sanic 测试：

```
pip 安装卫生测试
```

## 基本用法

只要`sanic-testing`软件包处于环境中，你就不需要开始使用它。

### 写入同步测试

为了使用测试客户端，您只需要在您的应用程序实例中访问属性 'test_client' ：

```python
从 sanic import Sanic, 导入 pytest
，响应

@pytest。 ixture
def app():
    sanic_app = Sanic("TestSanic")

    @sanic_app. et("/")
    def basic(request):
        return response. ext("foo")

    return sanic_app

def test_basic_test_client(app):
    request, response = app.test_client. et("/")

    passage request.method.lower() == "get"
    signing response。 did == b"foo"
    passage response.status == 200
```

### 写入异步测试

为了使用 pytest`中的 async 测试客户端，您应该安装`pytest-asyncio\` 插件。

```
pip install pest-asyncio
```

然后您可以创建异步测试并使用 ASGI 客户端：

```python
import pytest
from sanic import Sanic, response

@pytest.fixture
def app():
    sanic_app = Sanic(__name__)

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app

@pytest.mark.asyncio
async def test_basic_asgi_client(app):
    request, response = await app.asgi_client.get("/")

    assert request.method.lower() == "get"
    assert response.body == b"foo"
    assert response.status == 200
```
