---
title: 実行中のサニック
---

# 実行中のサニック

Sanicは独自の内部Webサーバーを搭載しています。 ほとんどの状況では、これはデプロイに最適な方法です。 また、SanicをASGI対応のWebサーバーにバンドルされたASGIアプリとしてデプロイすることもできます。

## Sanic Server

Sanicを走る主な方法は、付属の [CLI](#sanic-cli)を使うことです。

```sh
sanic path.to.server:app
```

この例では、Sanicは`path.to.server`というPythonモジュールを探すように指示されています。 このモジュールの中では、`app`という名前のグローバル変数を探します。これは、`Sanic(...)`のインスタンスでなければなりません。

```python
# ./path/to/server.py
from sanic import Sanic, Request, json

app = Sanic("TestApp")

@app.get("/")
async def handler(request: Request):
    return json({"foo": "bar"})
```

`app.run` をスクリプトとして呼び出すには、format@@0(#low-level-apprun) にドロップダウンすることもできます。 ただし、このオプションを選択した場合は、 `multiprocessing` で発生する可能性のある問題をより快適に処理する必要があります。

### Worker

.. 列::

```
デフォルトでは、Sanicはメインプロセスと単一のワーカープロセスを実行します([worker manager](./manager)を参照してください)。 d) 詳細については)。

ジュースをクランクアップするには、実行引数に含まれるワーカーの数を指定します。
```

.. 列::

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --works=4
```
````

Sanicは自動的に複数のプロセスとそれらの間のルートトラフィックを回します。 利用可能なプロセッサを持っている数だけの労働者をお勧めします。

.. 列::

```
最大CPUパフォーマンスを得る最も簡単な方法は、 `--fast` オプションを使用することです。 これは自動的にシステム制約を与えられたワーカーの最大数を実行します。

*v21.12* に追加されました
```

.. 列::

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --fast
```
````

バージョン22.9では、Sanicは開発サーバーと本番サーバーの間でより一貫性と柔軟性を提供する新しいワーカーマネージャを導入しました。 format@@0(./manager.md) を読んで、worker の詳細を確認してください。

.. 列::

```
Sanicを単一のプロセスでのみ実行したい場合は、run引数に`single_process`を指定します。 これは自動再読み込みを行い、ワーカーマネージャーが利用できなくなることを意味します。

*v22.9* に追加されました
```

.. 列::

````
```sh
sanic server:app --host=0.0.0.0 --port=1337 --single-process
```
````

### コマンドで実行

#### Sanic CLI

すべてのオプションを見るには `sanic --help` を使います。

.. attrs::
:title: Sanic CLI help output
:class: details

````
```text
$ sanic --help

   ▄███ █████ ██      ▄█▄      ██       █   █   ▄██████████
  ██                 █   █     █ ██     █   █  ██
   ▀███████ ███▄    ▀     █    █   ██   ▄   █  ██
               ██  █████████   █     ██ █   █  ▄▄
  ████ ████████▀  █         █  █       ██   █   ▀██ ███████

 To start running a Sanic application, provide a path to the module, where
 app is a Sanic() instance:

     $ sanic path.to.server:app

 Or, a path to a callable that returns a Sanic() instance:

     $ sanic path.to.factory:create_app --factory

 Or, a path to a directory to run as a simple HTTP server:

     $ sanic ./path/to/static --simple

Required
========
  Positional:
    module              Path to your Sanic app. Example: path.to.server:app
                        If running a Simple Server, path to directory to serve. Example: ./

Optional
========
  General:
    -h, --help          show this help message and exit
    --version           show program's version number and exit

  Application:
    --factory           Treat app as an application factory, i.e. a () -> <Sanic app> callable
    -s, --simple        Run Sanic as a Simple Server, and serve the contents of a directory
                        (module arg should be a path)
    --inspect           Inspect the state of a running instance, human readable
    --inspect-raw       Inspect the state of a running instance, JSON output
    --trigger-reload    Trigger worker processes to reload
    --trigger-shutdown  Trigger all processes to shutdown

  HTTP version:
    --http {1,3}        Which HTTP version to use: HTTP/1.1 or HTTP/3. Value should
                        be either 1, or 3. [default 1]
    -1                  Run Sanic server using HTTP/1.1
    -3                  Run Sanic server using HTTP/3

  Socket binding:
    -H HOST, --host HOST
                        Host address [default 127.0.0.1]
    -p PORT, --port PORT
                        Port to serve on [default 8000]
    -u UNIX, --unix UNIX
                        location of unix socket

  TLS certificate:
    --cert CERT         Location of fullchain.pem, bundle.crt or equivalent
    --key KEY           Location of privkey.pem or equivalent .key file
    --tls DIR           TLS certificate folder with fullchain.pem and privkey.pem
                        May be specified multiple times to choose multiple certificates
    --tls-strict-host   Only allow clients that send an SNI matching server certs

  Worker:
    -w WORKERS, --workers WORKERS
                        Number of worker processes [default 1]
    --fast              Set the number of workers to max allowed
    --single-process    Do not use multiprocessing, run server in a single process
    --legacy            Use the legacy server manager
    --access-logs       Display access logs
    --no-access-logs    No display access logs

  Development:
    --debug             Run the server in debug mode
    -r, --reload, --auto-reload
                        Watch source directory for file changes and reload on changes
    -R PATH, --reload-dir PATH
                        Extra directories to watch and reload on changes
    -d, --dev           debug + auto reload
    --auto-tls          Create a temporary TLS certificate for local development (requires mkcert or trustme)

  Output:
    --coffee            Uhm, coffee?
    --no-coffee         No uhm, coffee?
    --motd              Show the startup display
    --no-motd           No show the startup display
    -v, --verbosity     Control logging noise, eg. -vv or --verbosity=2 [default 0]
    --noisy-exceptions  Output stack traces for all exceptions
    --no-noisy-exceptions
                        No output stack traces for all exceptions

```
````

#### モジュールとして

.. 列::

```
Sanic アプリケーションはモジュールとして直接呼び出すこともできます。
```

.. 列::

````
```bash
python -m sanic server.app --host=0.0.0.0 --port=1337 --works=4
```
````

#### 工場の利用

非常に一般的な解決策は、アプリケーションをグローバル変数としてではなく\*開発することですが、代わりにファクトリパターンを使用することです。 この文脈で、"factory"とは、`Sanic(...)`のインスタンスを返す関数を意味します。

.. 列::

```
`server.py`にこれがあるとします。
```

.. 列::

````
```python
from sanic import Sanic

def create_app() -> Sanic:
    app = Sanic("MyApp")

    return app
```
````

.. 列::

```
このアプリケーションは、CLIで明示的にファクトリとして参照することで実行できます。
```

.. 列::

````
```sh
sanic server:create_app --factory
```
Or, explicitly like this:
```sh
sanic "server:create_app()"
```
Or, implicitly like this:
```sh
sanic server:create_app
```

*Implicit command added in v23.3*
````

### 低レベル `app.run`

`app.run`を使用する場合は、他のスクリプトと同様にPythonファイルを呼び出します。

.. 列::

```
`app.run` は name-main ブロックの中に正しく入れ子にする必要があります。
```

.. 列::

````
```python
# server.py
app = Sanic("MyApp")

if __name__ == "__main__":
    app.run()
```
````

.. 危険::

````
Be *careful* when using this pattern. A very common mistake is to put too much logic inside of the `if __name__ == "__main__":` block.

🚫 This is a mistake

```python
from sanic import Sanic
from my.other.module import bp

app = Sanic("MyApp")

if __name__ == "__main__":
    app.blueprint(bp)
    app.run()
```

If you do this, your [blueprint](../best-practices/blueprints.md) will not be attached to your application. This is because the `__main__` block will only run on Sanic's main worker process, **NOT** any of its [worker processes](../deployment/manager.md). This goes for anything else that might impact your application (like attaching listeners, signals, middleware, etc). The only safe operations are anything that is meant for the main process, like the `app.main_*` listeners.

Perhaps something like this is more appropriate:

```python
from sanic import Sanic
from my.other.module import bp

app = Sanic("MyApp")

if __name__ == "__mp_main__":
    app.blueprint(bp)
elif __name__ == "__main__":
    app.run()
```
````

低レベルの`run` APIを使用するには、`sanic.Sanic`のインスタンスを定義した後、以下のキーワード引数を使用してrunメソッドを呼び出すことができます。

|                   パラメータ                   |       デフォルト      | 説明                                                                           |
| :---------------------------------------: | :--------------: | :--------------------------------------------------------------------------- |
|                  **ホスト**                  |   `"127.0.0.1"`  | サーバーをホストするためのアドレス。                                                           |
|                  **ポート**                  |      `8000`      | サーバーをホストするためのポート。                                                            |
|                  **unix**                 |       `なし`       | (TCP の代わりに) サーバーをホストする Unix ソケット名。                        |
|                  **dev**                  |      `False`     | `debug=True`と`auto_reload=True`と同じです。                                        |
|                 **debug**                 |      `False`     | デバッグ出力を有効にします(サーバーを遅くします)。                                |
|                  **ssl**                  |       `なし`       | ワーカーの SSL 暗号化の SSLContext です。                                                |
|                  **sock**                 |       `なし`       | サーバーが接続を受け入れるソケット。                                                           |
|                 **works**                 |        `1`       | spawn するワーカープロセスの数。 高速では使用できません。                                             |
|                  **ループ**                  |       `なし`       | 非同期互換イベントループ。 何も指定されていない場合、Sanic は独自のイベントループを作成します。                          |
|                **protocol**               |  `HttpProtocol`  | asyncio.protocolのサブクラス。                                      |
|                 **バージョン**                 | `HTTP.VERSION_1` | 使用する HTTP バージョン (`HTTP.VERSION_1` または `HTTP.VERSION_3` )。 |
|    **access_log**    |      `True`      | リクエスト処理時にログを有効にします（サーバーが大幅に遅くなります）。                                          |
|    **auto_reload**   |       `なし`       | ソースディレクトリの自動リロードを有効にします。                                                     |
|    **reload_dir**    |       `なし`       | 自動リローダーが監視すべきディレクトリへのパスまたはリスト。                                               |
| **noisy_exceptions** |       `なし`       | 騒々しい例外をグローバルに設定するかどうか。 はいずれもデフォルトのままにします。                                    |
|                  **motd**                 |      `True`      | 起動時のメッセージを表示するかどうかを設定します。                                                    |
|   **motd_display**   |       `なし`       | スタートアップメッセージに表示する追加のキー/値情報を持つディクト                                            |
|                  **fast**                 |      `False`     | ワーカープロセスを最大化するかどうか。  ワーカーでは使用できません。                                          |
|               **verbosity**               |        `0`       | ログの詳細レベル。 最大は 2 です。                                                          |
|     **auto_tls**     |      `False`     | ローカル開発用の TLS 証明書を自動作成するかどうか。 生産のためではありません。                                   |
|  **single_process**  |      `False`     | 単一のプロセスでSanicを実行するかどうか。                                                      |

.. 列::

```
たとえば、パフォーマンスを向上させるためにアクセスログをオフにし、カスタムホストとポートにバインドすることができます。
```

.. 列::

````
```python
# server.py
app = Sanic("MyApp")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1337, access_log=False)
```
````

.. 列::

```
`app.run(...)`を持つPythonスクリプトを実行してください。
```

.. 列::

````
```sh
python server.py
```
````

もう少し高度な実装では、 `app.run` は `app.prepare` と `Sanic.serve` をフードの下で呼び出すことを知っておくと良いでしょう。

.. 列::

```
したがって、これらは等価です:
```

.. 列::

````
```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1337, access_log=False)
```
```python
if __name__ == "__main__":
    app.prepare(host='0.0.0.0', port=1337, access_log=False)
    Sanic.serve()
```
````

.. 列::

```
アプリケーションを複数のポートにバインドする必要がある場合に便利です。
```

.. 列::

````
```python
if __name__ == "__main__":
    app1.prepare(host='0.0.0.0', port=9990)
    app1.prepare(host='0.0.0.0', port=9991)
    app2.prepare(host='0.0.0.0', port=555555)
    Sanic.serve()
```
````

### Sanic Simple Server

.. 列::

```
場合によっては、提供する必要がある静的ファイルのディレクトリがあります。 特に、localhostサーバーを素早く立ち上げるのに便利です。 Sanic shipにはシンプルなサーバーがあり、ディレクトリにそれを指すだけで済みます。
```

.. 列::

````
```sh
sanic ./path/to/dir --simple
```
````

.. 列::

```
これは自動リロードと組み合わせることもできます。
```

.. 列::

````
```sh
sanic ./path/to/dir --simple -reload -reload-dir=./path/to/dir
```
````

_V21.6_に追加されました

### HTTP/3

Sanic server provides HTTP/3 support using [aioquic](https://github.com/aiortc/aioquic). HTTP/3を使用するには**インストールする必要があります**

```sh
pip install sanic aioquic
```

```sh
pip install sanic[http3]
```

HTTP/3 を開始するには、アプリケーションの実行時に明示的にリクエストする必要があります。

.. 列::

````
```sh
sanic path.to.server:app --http=3
```

```sh
sanic path.to.server:app -3
```
````

.. 列::

````
```python
app.run(version=3)
```
````

HTTP/3 と HTTP/1.1 の両方のサーバーを同時に実行するには、v22.3 で導入された [application multi-serve] (../release-notes/v22.3.html#application-multi-serve) を使用します。 これにより自動的に [Alt-Svc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Alt-Svc) ヘッダーがHTTP/1.1 リクエストに追加され、クライアントにHTTP/3 としても利用可能であることを知らせます。

.. 列::

````
```sh
sanic path.to.server:app --http=3 -http=1
```

```sh
sanic path.to.server:app -3 -1
```
````

.. 列::

````
```python
app.prepare(version=3)
app.prepare(version=1)
Sanic.serve()
```
````

HTTP/3 は TLS を必要とするため、TLS 証明書なしでは HTTP/3 サーバーを起動できません。 `DEBUG`モードの場合は、format@@0(../how-to/tls.html) または `mkcert` を使用してください。 現在、HTTP/3 に対する自動的な TLS 設定は `trustme` と互換性がありません。 詳細は [development](./development.md) を参照してください。

_v22.6_に追加されました

## ASGI

SanicもASGIに準拠しています。 つまり、ご希望のASGIウェブサーバーを使用してSanicを実行することができます。 ASGI の 3 つの主な実装は [Daphne](http://github.com/django/daphne), [Uvicorn](https://www.uvicorn.org/), および [Hypercorn](https://pgjones.gitlab.io/hypercorn/index.html) です。

.. 警告::

```
DaphneはASGIの`lifespan`プロトコルをサポートしていないため、Sanicを実行するために使用することはできません。詳細は[課題 264](https://github.com/django/daphne/issues/264)を参照してください。
```

適切な実行方法については、ドキュメントに従ってください。しかし、次のようになります。

```sh
uvicorn myapp:app
```

```sh
hypercorn myapp:app
```

ASGIを使用する場合、いくつか注意すべきことがあります:

1. Sanic ウェブサーバを使用する場合、websocketsは`websockets`パッケージを使用して実行されます。 ASGI モードでは、ウェブソケットは ASGI サーバで管理されるため、このパッケージは必要ありません。
2. ASGIの寿命プロトコル https://asgi.readthedocs.io/en/latest/specs/lifespan.htmlは、起動とシャットダウンの2つのサーバーイベントのみをサポートしています。 Sanicは、起動前、起動後、シャットダウン前、シャットダウン後の4つを持っています。 したがって、ASGIモードで 起動イベントとシャットダウンイベントは連続して実行され、実際にはサーバープロセスの開始と終了の周りには実行されません(それ以降はASGIサーバーによって制御されます)。 ですから、`after_server_start` と `before_server_stop` を使うのがベストです。

### トリオ

SanicはTrioでの実行を実験的にサポートしています。

```sh
hypercorn -k trio myapp:app
```

## グニコーン

[Gunicorn](http://gunicorn.org/) ("Green Unicorn") は UNIX ベースのオペレーティングシステム用の WSGI HTTP Server です。 これは、RubyのUnicornプロジェクトから移植されたpre-forkワーカーモデルです。

SanicalアプリケーションをGunicornで実行するには、 [uvicorn](https://www.uvicorn.org/)のアダプターで使用する必要があります。 uvicornがインストールされていることを確認し、Gunicorn.worker.UvicornWorker\`でGunicornワーカークラスの引数を実行します:

```sh
gunicorn myapp:app --bind 0.0.0.0.0:1337 --worker-class uvicorn.worker.UvicornWorker
```

詳細は [Gunicorn Docs](http://docs.gunicorn.org/en/latest/settings.html#max-requests) を参照してください。

.. 警告::

```
一般的には、必要な場合以外は `gunicorn` を使用しないことをお勧めします。 Sanic Serverは、本番環境でSanicを実行するためにプライミングされています。この選択を行う前に、慎重に考慮事項を検討してください。 Gunicornは多くの設定オプションを提供しますが、Sanicを最速で走らせるための最良の選択ではありません。
```

## パフォーマンスに関する考慮事項

.. 列::

```
本番環境で実行する場合は、`debug` をオフにしてください。
```

.. 列::

````
```sh
sanic path.to.server:app
```
````

.. 列::

```
`access_log` をオフにすると、Sanicも最速に動作します。

まだアクセスログが必要で、このパフォーマンスを向上させたい場合は、[Nginx をプロキシとして使用することを検討してください](。 nginx.md)、そしてアクセスログを処理させます。Pythonが扱えるどんなものよりもずっと速くなります。
```

.. 列::

````
```sh
sanic path.to.server:app --no-access-logs
```
````
