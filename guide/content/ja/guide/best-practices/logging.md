# ログ

Sanicはformat@@0(https://docs.python.org/3/howto/logging.html)に基づいてリクエストの異なるタイプのログ(アクセスログ、エラーログ)を行うことができます。 新しい設定を作成したい場合は、Pythonロギングに関する基本的な知識を持っている必要があります。

## クイックスタート

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

if __name__ == "__main__":
  app.run(debug=True, access_log=True)
```
````

サーバーが実行されると、このようなログが表示されます。

```text
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2021-01-04 15:26:26 +0200] [1929659] [INFO] Starting worker [1929659]
```

サーバーにリクエストを送信すると、ログメッセージが出力されます。

```text
[2021-01-04 15:26:28 +0200] [1929659] [INFO] ログ
[2021-01-04 15:26:28 +0200] - (sanic.access)[INFO][127.0.0.1:44228]: http://localhost:8000/ 200 -1
```

## サイニックロガーの変更

独自のロギング設定を使用するには、`logging.config.dictConfig` を使用するか、Sanic アプリを初期化する際に `log_config` を使用します。

```python
app = Sanic('logging_example', log_config=LOGGING_CONFIG)

if __name__ == "__main__":
  app.run(access_log=False)
```

.. tip:: FYI

```
Logging in Python is a relatively cheap operation. However, if you are serving a high number of requests and performance is a concern, all of that time logging out access logs adds up and becomes quite expensive.  

This is a good opportunity to place Sanic behind a proxy (like nginx) and to do your access logging there. You will see a *significant* increase in overall performance by disabling the `access_log`.  

For optimal production performance, it is advised to run Sanic with `debug` and `access_log` disabled: `app.run(debug=False, access_log=False)`
```

## 設定

Sanic のデフォルトのロギング設定は `sanic.log.LOGGING_CONFIG_DEFAULTS` です。

.. 列::

```
There are three loggers used in sanic, and must be defined if you want to create your own logging configuration:

| **Logger Name** | **Use Case**                  |
|-----------------|-------------------------------|
| `sanic.root`    | Used to log internal messages. |
| `sanic.error`   | Used to log error logs.       |
| `sanic.access`  | Used to log access logs.      |
```

.. 列::

### ログの形式

Python(`asctime`, `levelname`, `message`)で提供されるデフォルトのパラメータに加えて、Sanicはアクセスロガーの追加パラメータを提供しています。

| ログのコンテキストパラメータ | パラメータの値                              | Datatype |
| -------------- | ------------------------------------ | -------- |
| `host`         | `request.ip`                         | `str`    |
| `request`      | `request.method + " " + request.url` | `str`    |
| `status`       | `response`                           | `int`    |
| `byte`         | `len(response.body)`                 | `int`    |

デフォルトのアクセスログ形式は以下の通りです:

```text
%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: %(request)s %(message)s %(status)d %(byte)d
```
