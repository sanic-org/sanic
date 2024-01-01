---
title: サニックエクステンション - はじめに
---

# はじめに

Sanic Extensionsは、SCOによって開発され、維持されている_公式にサポートされている_プラグインです。 このプロジェクトの主な目的は、Web API および Web アプリケーション開発を容易にする追加機能を追加することです。

## 特徴

- CORS保護
- 神社でテンプレートをレンダリングする
- ルートハンドラへの依存性インジェクション
- やり直しや Swagger を使用した OpenAPI ドキュメント
- 事前定義されたエンドポイント固有のレスポンスシリアライザー
- クエリクエストの引数と本文入力のバリデーションをリクエスト
- `HEAD`、`OPTIONS`、および `TRACE`エンドポイントを自動的に作成します

## 最低要件

- **Python**: 3.8+
- **Sanic**: 21.9+

## インストール

最良の方法は、Sanic自体と一緒にSanic Extensionsをインストールすることです:

```bash
pip install sanic[ext]
```

もちろん、単独でインストールすることもできます。

```bash
pip install sanic-ext
```

## アプリケーションを拡張

Sanic Extensionsは、すぐにたくさんの機能を利用できるようになります。

.. 列::

```
Sanic Extensions(v21.12+)をセットアップするには、次の手順を実行する必要があります。**何もありません**。環境内にインストールされている場合は、セットアップして準備が整います。

このコードは、[Sanic Getting Started page](../../guide/getting-started)のHello, world appです。 d) _何も変更せずに `sanic-ext` がバックグラウンドにインストールされた Sanic 拡張機能を使用します。
```

.. 列::

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

.. 列::

```
**_OLD DEPRECATED SETUP_**

In v21.9, the easiest way to get started is to instantiate it with `Extend`.

If you look back at the Hello, world app in the [Sanic Getting Started page](../../guide/getting-started.md), you will see the only additions here are the two highlighted lines.
```

.. 列::

````
```python
from sanic import Sanic
from sanic.response import text
from sanic_ext import Extend

app = Sanic("MyHelloWorldApp")
Extend(app)

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```
````

どのように設定されているかに関わらず、OpenAPI ドキュメントを表示し、動作中のいくつかの機能を確認できるようになりました: [http://localhost:8000/docs](http://localhost:8000/docs)。
