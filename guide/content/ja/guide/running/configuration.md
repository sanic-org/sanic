# 設定

## 基本

.. 列::

```
Sanic はアプリケーションオブジェクトの config 属性に設定を保持します。 構成オブジェクトは、ドット表記または辞書のように変更できるオブジェクトにすぎません。
```

.. 列::

````
```python
app = Sanic("myapp")
app.config.DB_NAME = "appdb"
app.config["DB_USER"] = "appuser"
```
````

.. 列::

```
`update()`メソッドは、通常の辞書と同様に使用することもできます。
```

.. 列::

````
```python
db_settings = {
    'DB_HOST': 'localhost',
    'DB_NAME': 'appdb',
    'DB_USER': 'appuser'
}
app.config.update(db_settings)
```
````

.. note::

```
Sanicでは標準的な方法で、設定値を**大文字**で指定します。 確かに、大文字と小文字の名前を混ぜ始めると、奇妙な動作が発生することがあります。
```

## 読み込み中

### 環境変数

.. 列::

```
SANIC_`プレフィックスで定義された環境変数は、Sanicの設定に適用されます。 例えば、`SANIC_REQUEST_TIMEOUT` を設定すると、アプリケーションが自動的にロードされ、 `REQUEST_TIMEOUT` 設定変数に与えられます。
```

.. 列::

````
```bash
$ export SANIC_REQUEST_TIMEOUT=10
```
```python
>>> print(app.config.REQUEST_TIMEOUT)
10
```
````

.. 列::

```
Sanicが起動時に期待しているプレフィックスを変更できます。
```

.. 列::

````
```bash
$ export MYAPP_REQUEST_TIMEOUT=10
```
```python
>>> app = Sanic(__name__, env_prefix='MYAPP_')
>>> print(app.config.REQUEST_TIMEOUT)
10
```
````

.. 列::

```
環境変数の読み込みを完全に無効にすることもできます。
```

.. 列::

````
```python
app = Sanic(__name__, load_env=False)
```
````

### Sanic.update_config の使用

`Sanic`インスタンスは、config: `app.update_config`をロードするための_very_汎用的なメソッドを持っています。 ファイル、辞書、クラス、またはその他のあらゆる種類のオブジェクトにパスを与えることができます。

#### ファイルから

.. 列::

```
たとえば、次のような `my_config.py` ファイルがあるとします。
```

.. 列::

````
```python
# my_config.py
A = 1
B = 2
```
````

.. 列::

```
`app.update_config`にパスを渡すことで、これを設定値としてロードできます。
```

.. 列::

````
```python
>>> app.update_config("/path/to/my_config.py")
>>> print(app.config.A)
1
```
````

.. 列::

```
このパスは、bash スタイルの環境変数も受け付けます。
```

.. 列::

````
```bash
$ export my_path="/path/to"
```
```python
app.update_config("${my_path}/my_config.py")
```
````

.. note::

```
ただ、`${environment_variable}`形式で環境変数を指定する必要があり、`$environment_variable`は展開されていないことを覚えておいてください（「プレーン」テキストとして扱われます）。
```

#### 辞書から

.. 列::

```
`app.update_config` メソッドはプレーン辞書でも動作します。
```

.. 列::

````
```python
app.update_config({"A": 1, "B": 2})
```
````

#### クラスまたはオブジェクトから

.. 列::

```
独自の設定クラスを定義し、`app.update_config`に渡すことができます。
```

.. 列::

````
```python
class MyConfig:
    A = 1
    B = 2

app.update_config(MyConfig)
```
````

.. 列::

```
インスタンス化することもできます
```

.. 列::

````
```python
app.update_config(MyConfig())
```
````

### 鋳造タイプ

環境変数から読み込むとき、Sanicは期待されるPython型に値をキャストしようとします。 これは特に以下に該当します：

- `int`
- `float`
- `bool`

`bool`に関しては、以下の_大文字小文字を区別しません。

- **`True`**: `y`, `yes`, `yep`, `yep`, `yup`, `true`, `on`, `enable`, `enabled`, `1`
- **`False`**: `n`, `no`, `f`, `nope`, `false`, `off`, `disabled`, `0`

値をキャストできない場合、デフォルトは `str` になります。

.. 列::

```
さらに、Sanicは追加の型コンバータを使用して追加の型をキャストするように設定できます。 値を返したり、`ValueError` を発生させたりする任意の呼び出し可能である必要があります。

*v21.12* に追加されました
```

.. 列::

````
```python
app = Sanic(..., config=Config(converters=[UUID]))
```
````

#### 高度な型コンバータ

.. 列::

```
For more sophisticated conversion logic that needs access to the full environment variable context, you can use `DetailedConverter`. This abstract base class provides access to the full environment variable key, the raw value, and the current config defaults.

This is useful when you need to:
- Cast values to the type of their defaults
- Perform validation based on the variable name pattern
- Use default values for fallback logic
- Access configuration context during conversion
```

.. 列::

````
```python
from sanic.config import DetailedConverter

class DefaultsTypeCastingConverter(DetailedConverter):
    def __call__(self, full_key: str, config_key: str, value: str, defaults: dict):
        try:
            if config_key in defaults:
                return type(defaults[config_key])(value)
        except (ValueError, TypeError) as e:
            raise TypeError(f"Configuration environment variable '{full_key}' type mismatch: expected"
                            f" {type(defaults[config_key]).__name__}, got {type(value).__name__}") from e

app = Sanic(..., config=Config(converters=[DefaultsTypeCastingConverter()]))
```
````

.. 列::

```
The `DetailedConverter.__call__` method receives four parameters:

- `full_key`: The full environment variable name with prefix (e.g., "SANIC_DATABASE_URL")
- `config_key`: The config key without prefix (e.g., "DATABASE_URL")
- `value`: The raw string value from the environment
- `defaults`: The current default configuration values
```

.. 列::

````
```python
class ValidationConverter(DetailedConverter):
    def __call__(self, full_key: str, config_key: str, value: str, defaults: dict):
        if config_key.endswith('_PORT'):
            port = int(value)
            if not 1 <= port <= 65535:
                raise ValueError(f"Invalid port: {port}")
            return port
        raise ValueError  # Let other converters handle it
```
````

## 組み込み値

| **変数**                                                       | **デフォルト**            | **説明**                                                                                       |
| ------------------------------------------------------------ | -------------------- | -------------------------------------------------------------------------------------------- |
| ACCESS_LOG                              | True                 | アクセスログを無効または有効にする                                                                            |
| 拡張されました。                                                     | True                 | [Sanic Extensions](../../plugins/sanic-ext/getting-started.md) が既存の仮想環境にある場合にロードされるかどうかを制御する |
| AUTO_RELOAD                             | True                 | ファイルが変更されたときにアプリケーションが自動的にリロードされるかどうかを制御します                                                  |
| number@@0 自動登録                     | True                 | 存在しない信号で `app.event()` メソッドを使用して `True` を使用すると自動的に作成され、例外は発生しません。                            |
| FORMAT                                                       | html                 | 例外がキャッチされて処理されていない場合のエラー応答のフォーマット                                                            |
| 前に進みました。                                                     | X-Forwarded-For      | クライアントとプロキシIPを含むHTTPヘッダー「X-Forwarded-For」の名前                                                 |
| FORWARDED_SECRET                        | なし                   | 特定のプロキシ サーバーを安全に識別するために使用します (下記参照)                                       |
| タイムアウト                                                       | 15.0 | アイドル状態でない接続を強制終了するまで待機する時間 (秒)                                            |
| 検査                                                           | False                | インスペクタを有効にするかどうか                                                                             |
| INSPECTOR_HOST                          | localhost            | インスペクタのホスト                                                                                   |
| インポートします。                                                    | 6457                 | インスペクターのポート                                                                                  |
| キー                                                           | -                    | インスペクタの TLS キー                                                                               |
| INSPECTOR_TLS_CERT | -                    | インスペクタの TLS 証明書                                                                              |
| INSPECTOR_API_KEY  | -                    | インスペクタの API キー                                                                               |
| ALIVE_TIMEOUT                           | 120                  | TCPコネクションを保持する期間 (秒)                                                      |
| 保持します。                                                       | True                 | Falseのときは生き残りを無効にします                                                                         |
| MOTD                                                         | True                 | 起動時にMOTD (メッセージ) を表示するかどうか                                                |
| MOTD_表示                                 | {}                   | MOTD に追加の任意のデータを表示するキー/値のペア                                                                  |
| NOISY_EXCEPTIONS                        | False                | すべての `quiet` 例外をログに記録する                                                                      |
| PROXIES_COUNT                           | なし                   | アプリの前にあるプロキシサーバーの数（例：nginx、下記参照）                                                             |
| REAL_IP_HEADER     | なし                   | 実際のクライアントIPを含むHTTPヘッダーの名前                                                                    |
| 登録                                                           | True                 | アプリレジストリを有効にするかどうか                                                                           |
| リクエストのBUFF_サイズ                          | 65536                | リクエストを一時停止する前のリクエストバッファサイズ。デフォルトは64KBです。                                                     |
| リクエストID                                                      | X-リクエストID            | リクエスト/相関IDを含む "X-Request-ID" HTTP ヘッダーの名前                                                    |
| 最大サイズ                                                        | 100000000            | リクエストの大きさ（バイト）は100メガバイトです                                                                    |
| 要求される最大ヘッダのサイズ                                               | 8192                 | リクエストヘッダがどれくらい大きいか(バイト)、デフォルトは8192バイト                                     |
| 要求時間                                                         | 60                   | リクエスト到着までにかかる時間 (秒)                                                       |
| タイムアウト                                                       | 60                   | 応答の処理にかかる時間 (秒)                                                           |
| UVLoopを使用します。                                                | True                 | `uvloop` を使用するループポリシーをオーバーライドします。 `app.run`でのみサポートされています。                                    |
| 最大サイズ                                                        | 2^20                 | 受信メッセージの最大サイズ (バイト)                                                       |
| Ping_INTERVAL                           | 20                   | Pingフレームは、ping_interval 秒ごとに送信されます。                                     |
| ping_timeout                            | 20                   | ping_timeout 秒後に Pong が受信されなかった場合、接続は切断されます                             |

.. tip:: FYI

```
- The `USE_UVLOOP` value will be ignored if running with Gunicorn. Defaults to `False` on non-supported platforms (Windows).
- The `WEBSOCKET_` values will be ignored if in ASGI mode.
- v21.12 added: `AUTO_EXTEND`, `MOTD`, `MOTD_DISPLAY`, `NOISY_EXCEPTIONS`
- v22.9 added: `INSPECTOR`
- v22.12 added: `INSPECTOR_HOST`, `INSPECTOR_PORT`, `INSPECTOR_TLS_KEY`, `INSPECTOR_TLS_CERT`, `INSPECTOR_API_KEY`
```

## タイムアウト

### 要求時間

リクエストタイムアウトは、新しいオープンTCP接続が
Sanicバックエンドサーバに渡された瞬間の時間を測定します。 そして全体の HTTP リクエストが受信された瞬間です。 If the time taken exceeds the
`REQUEST_TIMEOUT` value (in seconds), this is considered a Client Error so Sanic generates an `HTTP 408` response
and sends that to the client. クライアントが非常に大きなリクエストペイロード
を日常的に渡したり、リクエストを非常にゆっくりアップロードした場合、このパラメータの値を高く設定します。

### タイムアウト

応答タイムアウトは、Sanic サーバーが HTTP リクエストを Sanic App に渡す瞬間の時間を測定します。 クライアントにHTTPレスポンスが送信されます。 経過時間が `RESPONSE_TIMEOUT` 値を超えた場合 (秒数) これはサーバーエラーと見なされるため、Sanic は `HTTP 503` レスポンスを生成してクライアントに送信します。 アプリケーションが、応答の
生成を遅らせる長時間のプロセスを持つ可能性がある場合、このパラメータの値を大きく設定します。

### ALIVE_TIMEOUT

#### Keep Aliveとは何ですか? そして、Keep Alive Timeoutの価値は何ですか?

`Keep-Alive`は、`HTTP 1.1`で導入されたHTTP機能です。 HTTP リクエストを送信するとき クライアント(通常はウェブブラウザアプリケーション)は、レスポンスを送信した後にTCPコネクションを閉じないように、httpサーバー(SANC)を示す「Keep-Alive」ヘッダを設定できます。 これにより、クライアントは既存の TCP コネクションを再利用して、後続の HTTP リクエストを送信することができます。 クライアントとサーバーの両方で、より効率的なネットワークトラフィックを確保します。

デフォルトでは、`KEEP_ALIVE`設定変数は、Sanicでは`True`に設定されています。 アプリケーションでこの機能を必要としない場合 応答が送信された直後にすべてのクライアント接続が閉じられるようにするには、 `False` に設定します。 リクエストの `Keep-Alive` ヘッダーに関係なく。

サーバーがTCP接続を開いている時間は、サーバー自身によって決まります。 Sanic では、その値は `KEEP_ALIVE_TIMEOUT` 値を使用して設定されます。 デフォルトでは、**120秒**に設定されています。 これは、クライアントが `Keep-Alive` ヘッダーを送信した場合、サーバーは応答を送信した後 120 秒間、TCP コネクションを保持します。 クライアントはその時間内に別の HTTP リクエストを送信するために接続を再利用できます。

参考:

- Apache サーバのデフォルトの keepalving timeout = 5 秒
- Nginx サーバーのデフォルトの keepalving タイムアウト = 75 秒
- Nginx パフォーマンスチューニングガイドラインでは、keepliving = 15 seconds
- キャディサーバーのデフォルトキープサバイバルタイムアウト = 120 秒
- IE (5-9) クライアントハードキープアライブ制限 = 60秒
- Firefox クライアントのハードキープサバイバル制限 = 115 秒
- Opera 11 クライアントのハードキープサバイバル制限 = 120 秒
- Chrome 13+クライアントキープサバイバル制限 > 300秒以上

## プロキシ設定

[プロキシ設定セクション](../advanced/proxy-headers.md) を参照してください。
