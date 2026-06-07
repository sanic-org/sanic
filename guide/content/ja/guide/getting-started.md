# はじめに

始める前に、Python 3.9 以上を実行していることを確認してください。 現在、SanicはPythonバージョン3.9 – 3.13で動作しています。

## インストール

```sh
pip install sanic
```

## こんにちは、世界のアプリケーション

.. 列::

```
If you have ever used one of the many decorator based frameworks, this probably looks somewhat familiar to you.



.. note:: 

    If you are coming from Flask or another framework, there are a few important things to point out. Remember, Sanic aims for performance, flexibility, and ease of use. These guiding principles have tangible impact on the API and how it works.
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

### ご注意ください

- 各リクエストハンドラーは、sync (`def hello_world`) または async (`async def hello_world`) のいずれかになります。 明確な理由がない限り、常に `async` を使用します。
- `request` オブジェクトは常にハンドラの最初の引数です。 他のフレームワークは、インポートされるコンテキスト変数にこれを渡します。 `async` ワールドで うまくいかないし、明らかにするのははるかに簡単です(クリーナーやパフォーマンスの向上は言うまでもありません)。
- 応答タイプを**使用する必要があります**。 他の多くのフレームワークでは、`return "Hello, world."` または: `return {"foo": "bar"}` のような戻り値を持つことができます。 しかしこの暗黙の呼び出しを行うためには、チェーン内のどこかで、あなたが何を意味するのかを判断するために貴重な時間を費やす必要があります。 したがって、これを犠牲にして、Sanicは明示的な呼び出しを要求することにしました。

### 実行中

.. 列::

```
上記のファイルを `server.py` として保存して起動しましょう。
```

.. 列::

````
```sh
sanic server
```
````

.. note::

```
この**別の**重要な区別。他のフレームワークには開発用サーバーが組み込まれており、開発用のものであることを明示的に示しています。 

**パッケージ化されたサーバーは準備ができています。**
```

## サニックエクステンション

Sanicは、意図的にクリーンで不要なフィーチャーリストを目指しています。 プロジェクトは、特定の方法でアプリケーションを構築する必要はありませんし、特定の開発パターンを処方しないようにしようとします。 コミュニティによって構築され、維持されているいくつかのサードパーティーのプラグインがあります, それ以外の場合、コアリポジトリの要件を満たしていない追加の機能を追加します.

しかし、**API 開発者を助けるために**ために、Sanic Organization は [Sanic Extensions](../plugins/sanic-ext/getting-started.md) と呼ばれる公式プラグインを管理し、以下を含むあらゆる種類のグッズを提供します。

- **OpenAPI** Redoc や Swagger 付きドキュメント
- **CORS** 保護
- ルートハンドラへの**依存性注入**
- クエリの引数と本文入力**バリデーション**
- `HEAD`、`OPTIONS`、および `TRACE`エンドポイントを自動的に作成します
- 事前定義されたエンドポイント固有のレスポンスシリアライザー

設定するにはSanicと一緒にインストールする方法が推奨されますが、独自にパッケージをインストールすることもできます。

.. 列::

````
```sh
pip install sanic[ext]
```
````

.. 列::

````
```sh
pip install sanic sanic-ext
```
````

同じ環境であれば、Sanicは自動的にSanic Extensionをv21.12から設定します。 2つの追加アプリケーションプロパティにもアクセスできます。

- `app.extend()` - Sanic Extensionsの設定に使用
- `app.ext` - アプリケーションに追加された `Extend` インスタンス

プラグインの使用方法と操作方法については、format@@0(../plugins/sanic-ext/getting-started.md) を参照してください。
