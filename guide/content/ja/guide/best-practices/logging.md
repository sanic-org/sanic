# ログ

Sanicはformat@@0(https://docs.python.org/3/howto/logging.html)に基づいてリクエストの異なるタイプのログ(アクセスログ、エラーログ)を行うことができます。 新しい設定を作成したい場合は、Pythonロギングに関する基本的な知識を持っている必要があります。

しかし、Sanicは、箱の中からいくつかの賢明なロギングデフォルトで出荷されます。 デバッグモードであるかどうかに応じてログをフォーマットする `AutoFormatter` を使用します。 これを後で強制する方法をお見せします。

## クイックスタート

まずは、ローカル開発におけるロギングの様子を見てみましょう。 このために、Sanicが提供するデフォルトのロギング設定を使用し、開発モードでSanicを実行するようにします。

.. 列::

```
デフォルト設定を使用した簡単な例は次のようになります。
```

.. 列::

````
```python
from sanic import Sanic
from sanic.log import logger
from sanic.response import text

app = Sanic('logging_example')

@app.route('/')
async def test(request):
    logger.info('Here is your log')
    return text('Hello World!')
```
````

.. 列::

```
開発ログを確認しようとしているので、Sanicを必ず開発モードで実行します。
```

.. 列::

````
```sh
sanic path.to.server:app --dev
```    
````

サーバーが実行されると、このようなログが表示されます。

![Sanic Logging Start](/assets/images/logging-debug-start.png)

サーバーにリクエストを送信すると、ログメッセージが出力されます。

![Sanic Logging Access](/assets/images/logging-debug-access.png)

注意すべきいくつかの重要なポイント:

- **production** モードのデフォルトのログレベルは `INFO` です。
- **debug** モードのデフォルトのログレベルは `DEBUG` です。
- **debug** モードの場合、ログメッセージにタイムスタンプはありません(アクセスログを除く)。
- Sanicはターミナルがそれをサポートしている場合、ログを色付けしようとします。 Docker で docker-compose を実行している場合は、`docker-compose.yml` ファイルに `tty: true` を設定して色を確認する必要があります。

## Sanicのロガー

サニック号には5つのロガーが搭載されています。

| **Logger Name**    | **ユースケース**               |
| ------------------ | ------------------------ |
| `sanic.root`       | 内部メッセージのログに使用されます。       |
| `sanic.error`      | エラーログを記録するために使用されます。     |
| `sanic.access`     | アクセスログを記録するために使用されます。    |
| `sanic.server`     | サーバログのログに使用します。          |
| `sanic.websockets` | ウェブソケットのログを記録するために使用します。 |

.. 列::

```
これらのロガーを自分で使いたい場合は、 `sanic.log` からインポートできます。
```

.. 列::

````
```python
from sanic.log import logger, error_logger, access_logger, server_logger, websockets_logger

logger.info('This is a root logger message')
```
````

.. 警告::

```
ルートロガーとエラーロガーを自由に使用してください。 ただし、アクセスロガー、サーバーロガー、またはwebsocketsロガーを直接使用したくない場合があります。 これらはSanicによって内部で使用され、特定の方法でログインするように設定されています。 これらのロガーのログの方法を変更したい場合は、ログの設定を変更する必要があります。
```

## デフォルトのログ設定

Sanic は、独自のロギング設定を提供しない場合に使用されるデフォルトのロギング設定を持っています。 この設定は `sanic.log.LOGGING_CONFIG_DEFAULTS` に保存されます。

```python
{
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'sanic.root': {'level': 'INFO', 'handlers': ['console']},
        'sanic.error': {
            'level': 'INFO',
            'handlers': ['error_console'],
            'propagate': True,
            'qualname': 'sanic.error'
        },
        'sanic.access': {
            'level': 'INFO',
            'handlers': ['access_console'],
            'propagate': True,
            'qualname': 'sanic.access'
        },
        'sanic.server': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
            'qualname': 'sanic.server'
        },
        'sanic.websockets': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
            'qualname': 'sanic.websockets'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': sys.stdout
        },
        'error_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': sys.stderr
        },
        'access_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'stream': sys.stdout
        }
    },
    'formatters': {
        'generic': {'class': 'sanic.logging.formatter.AutoFormatter'},
        'access': {'class': 'sanic.logging.formatter.AutoAccessFormatter'}
    }
}
```

## サイニックロガーの変更

.. 列::

```
独自のロギング設定を使用するには、`logging.config.dictConfig` を使用するか、Sanic アプリを初期化する際に `log_config` を使用します。
```

.. 列::

````
```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
    app.run(access_log=False)
```
````

.. 列::

```
しかし、ロギングを完全に制御したくない場合は、例えばフォーマッタを変更してください。 ここでは、デフォルトのロギング設定をインポートし、常に`ProdFormatter`を使用するように強制する部分(例えば)のみを変更します。
```

.. 列::

````
```python
from sanic.log import LOGGING_CONFIG_DEFAULTS

LOGGING_CONFIG_DEFAULTS['formatters']['generic']['class'] = 'sanic.logging.formatter.ProdFormatter'
LOGGING_CONFIG_DEFAULTS['formatters']['access']['class'] = 'sanic.logging.formatter.ProdAccessFormatter'

app = Sanic('logging_example', log_config=LOGGING_CONFIG_DEFAULTS)
```
````

.. tip:: FYI

```
Logging in Python is a relatively cheap operation. However, if you are serving a high number of requests and performance is a concern, all of that time logging out access logs adds up and becomes quite expensive.  

This is a good opportunity to place Sanic behind a proxy (like nginx) and to do your access logging there. You will see a *significant* increase in overall performance by disabling the `access_log`.  

For optimal production performance, it is advised to run Sanic with `debug` and `access_log` disabled: `app.run(debug=False, access_log=False)`
```

## アクセスロガーの追加パラメータ

Sanicはアクセスロガーに追加のパラメータを提供します。

| ログのコンテキストパラメータ | パラメータの値                              | Datatype |
| -------------- | ------------------------------------ | -------- |
| `host`         | `request.ip`                         | `str`    |
| `request`      | `request.method + " " + request.url` | `str`    |
| `status`       | `response`                           | `int`    |
| `byte`         | `len(response.body)`                 | `int`    |
| `duration`     | <calculated>                         | `float`  |

## レガシーログ

Sanic 24.3では多くのロギング変更が導入されました。 主な変更点は、ロギングフォーマットに関連していました。 従来のログ形式を使用する場合は、`sanic.logging.formatter.LegacyFormatter.LegacyFormatter` と `sanic.logging.formatter.LegacyAccessFormatter` 形式を使用します。
