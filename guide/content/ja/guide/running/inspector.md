# Inspector

Sanic Inspector は、Sanic Server の機能です。 Sanic を組み込みの format@@0(./manager.md) で実行している場合は _のみ_ 利用できます。

これは、アプリケーションの実行中のインスタンスと対話できるように、アプリケーションのバックグラウンドで_オプション_で動作するHTTPアプリケーションです。

.. tip:: INFO

```
インスペクターは v22.9 で限定的な容量で導入されましたが、このページのドキュメントでは、v22.12 以上を使用していることを前提としています。
```

## はじめに

インスペクターはデフォルトで無効になっています。 それを有効にするには、2つのオプションがあります。

.. 列::

```
アプリケーションインスタンスを作成するときにフラグを設定します。
```

.. 列::

````
```python
app = Sanic("TestApp", inspector=True)
```
````

.. 列::

```
または、設定値を設定します。
```

.. 列::

````
```python
app = Sanic("TestApp")
app.config.INSPECTOR = True
```
````

.. 警告::

```
設定値を使用している場合は、メインワーカープロセスが開始される前に *必ず* 設定を行わなければなりません。 これは、環境変数であるか、上記のようにアプリケーションインスタンスを作成した直後に設定する必要があることを意味します。
```

## インスペクターの使用

インスペクターが実行されると、CLI 経由または直接 Web API に HTTP 経由でアクセスできるようになります。

.. 列::

````
**CLI**
```sh
sanic inspect
```
````

.. 列::

````
**Via HTTP**
```sh
curl http://localhost:6457
```
````

.. note::

```
覚えておいてください、インスペクターはSanicアプリケーション上で実行されていません。それは分離されたアプリケーションであり、分離されたソケット上で公開されています。
```

## 内蔵コマンド

インスペクターには、次の組み込みコマンドが付属しています。

| CLIコマンド            | HTTP アクション                     | 説明                            |
| ------------------ | ------------------------------ | ----------------------------- |
| `inspect`          | `GET /`                        | 実行中のアプリケーションに関する基本的な詳細を表示します。 |
| `inspect reload`   | `POST /reload`                 | すべてのサーバワーカーのリロードをトリガーします。     |
| `inspect shutdown` | `POST /shutdown`               | すべてのプロセスをシャットダウンします。          |
| `inspect scale N`  | `POST /scale`<br>`{"レプリカ": N}` | ワーカーの数を調整します。 `N`がレプリカの対象数です。 |

## カスタムコマンド

インスペクターは簡単に拡張でき、カスタムコマンド(およびエンドポイント)を追加できます。

.. 列::

```
`Inspector` クラスをサブクラス化し、任意のメソッドを作成します。 メソッド名の前にアンダースコア(`_`)がない限り、 そして、このメソッドの名前は、インスペクタの新しいサブコマンドになります。
```

.. 列::

````
```python
from sanic import json
from sanic.worker.inspector import Inspector

class MyInspector(Inspector):
    async def something(self, *args, **kwargs):
        print(args)
        print(kwargs)

app = Sanic("TestApp", inspector_class=MyInspector, inspector=True)
```
````

これは一般的なパターンでカスタムメソッドを公開します。

- CLI: `健全な検査 <method_name>`
- HTTP: `POST /<method_name>`

新しいメソッドが受け取る引数は、コマンドの使用方法に基づいていることに注意することが重要です。 例えば、上記の `something` メソッドは、すべての位置とキーワードベースのパラメータを受け取ります。

.. 列::

```
CLIでは、位置パラメータとキーワードパラメータが、メソッドに位置引数またはキーワード引数として渡されます。 すべての値は次の例外を持つ`str`になります:

- 代入されていないキーワードパラメータは次のようになります: `True`
- パラメータが`no`で始まる場合を除きます。 次のようになります: `False`
```

.. 列::

````
```sh
sanic inspect something one two three --four --no-five --six=6
```
In your application log console, you will see:
```
('one', 'two', 'three')
{'four': True, 'five': False, 'six': '6'}
```
````

.. 列::

```
APIを直接押すことでも同様です。JSONペイロードで公開することでメソッドに引数を渡すことができます。 唯一の注意点は、位置引数は `{"args": [...] }` として公開されるべきであるということです。
```

.. 列::

````
```sh
curl http://localhost:6457/something \
  --json '{"args":["one", "two", "three"], "four":true, "five":false, "six":6}'
```
In your application log console, you will see:
```
('one', 'two', 'three')
{'four': True, 'five': False, 'six': 6}
```
````

## プロダクションでの使用

.. 危険::

```
製品のインスペクターを公開する前に、このセクションのすべてのオプションを注意深く検討してください。
```

リモート本番インスタンスでインスペクターを実行する場合、TLS 暗号化を要求し、API キー認証を必要とすることでエンドポイントを保護できます。

### TLS 暗号化

.. 列::

```
TLS を介してインスペクタの HTTP インスタンスには、証明書と鍵へのパスを渡します。
```

.. 列::

````
```python
app.config.INSPECTOR_TLS_CERT = "/path/to/cert.pem"
app.config.INSPECTOR_TLS_KEY = "/path/to/key.pem"
```
````

.. 列::

```
`--secure` フラグまたは `https://` を使用する必要があります。
```

.. 列::

````
```sh
sanic inspect --secure --host=<somewhere>
```
```sh
curl https://<somewhere>:6457
```
````

### API キー認証

.. 列::

```
Bearer token authenticationでAPIをセキュリティ保護できます。
```

.. 列::

````
```python
app.config.INSPECTOR_API_KEY = "Super-Secret-200"
```
````

.. 列::

```
これには`--api-key` パラメータまたはベアラートトークン認証ヘッダが必要です。
```

.. 列::

````
```sh
sanic inspect --api-key=Super-Secret-200
```
```sh
curl http://localhost:6457 -H "Authorization: Bearer Super-Secret-200"
```
````

## 設定

[configuration](./configuration.md) を参照してください。
