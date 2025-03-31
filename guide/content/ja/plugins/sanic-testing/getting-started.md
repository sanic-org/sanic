---
title: サニックテスト - はじめに
---

# はじめに

Sanic Testingは、Sanicの_公式_テストクライアントです。 その主な使用は、Sanicプロジェクト自体のテストに電力を供給することです。 ただし、APIテストをすばやく実行するための使いやすいクライアントとしても意味されます。

## 最低要件

- **Python**: 3.7+
- **Sanic**: 21.3+

21.3より古いSanicのバージョンは、このモジュールをSanic自体に`sanic.testing`として統合しています。

## インストール

PyPI からテストをインストールすることができます。

```
pip install sanic-testing
```

## 基本的な使用法

`sanic-testing`パッケージが環境の中にある限り、使い始める必要はありません。

### 同期テストを書く

テストクライアントを使用するには、アプリケーションインスタンスの `test_client` プロパティにアクセスするだけです。

```python
import pytest
from sanic import Sanic, response

@pytest.fixture
def app():
    sanic_app = Sanic("TestSanic")

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app

def test_basic_test_client(app):
    request, response = app.test_client.get("/")

    assert request.method.lower() == "get"
    assert response.body == b"foo"
    assert response.status == 200
```

### 非同期テストを書く

`pytest`でasyncテストクライアントを使用するには、`pytest-asyncio`プラグインをインストールしてください。

```
pip install pytest-asyncio
```

非同期テストを作成し、ASGI クライアントを使用できます。

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
