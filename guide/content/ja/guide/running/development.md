# 開発

最初に言及すべきことは、Sanicに統合されているWebサーバーは開発サーバーだけではないということです。

_デバッグモード_で有効にしない限り、プロダクションはすぐにすぐに準備ができています。

## デバッグモード

デバッグモードを設定すると、Sanicは出力をより冗長にし、複数のランタイム最適化を無効にします。

```python
# server.py
from sanic import Sanic
from sanic.response import json

app = Sanic(__name__)

@app.route("/")
async def hello_world(request):
    return json({"hello": "world"})
```

```sh
sanic server:app --host=0.0.0 --port=1234 --debug
```

.. 危険::

```
Sanicのデバッグモードはサーバーのパフォーマンスを低下させ、本番環境向けではありません。

**本番環境でデバッグモードを有効にしないでください** 。
```

## 自動リローダー

.. 列::

```
Sanicは自動リロードを有効または無効にする方法を提供します。 それを有効にする最も簡単な方法は、CLIの`--reload`引数を使用して自動リロードを有効にすることです。 Pythonファイルが変更されるたびに、リローダーはアプリケーションを自動的に再起動します。 これは開発中に非常に便利です。

.. Note:: 

    このリローダーはSanicの[worker manager]()を使用している場合にのみ利用できます。 `--single-process` を使用して無効にした場合、再ローダーは利用できません。
```

.. 列::

````
```sh
sanic path.to:app --reload
```
簡体字プロパティ
```sh
sanic path.to:app -r
```
````

.. 列::

```
ファイル保存時に自動的にリロードしたい追加のディレクトリがある場合(例: HTML テンプレートのディレクトリ) `--reload-dir` を使用して追加できます。
```

.. 列::

````
```sh
sanic path.to:app --reload --reload-dir=/path/to/templates
```
Or multiple directories, shown here using the shorthand properties
```sh
sanic path.to:app -r -R /path/to/one -R /path/to/two
```
````

## 開発REPL

.. new:: v23.12

```
Sanic CLI には、アプリケーションとやり取りするために使用できる REPL (別名「read-eval-print loop」)が付属しています。 これはデバッグとテストに役立ちます。REPL は引数なしで `python` を実行するときに得られる対話型シェルです。
```

.. 列::

```
Sanic CLI に `--repl` 引数を渡すことで、REPL を開始できます。
```

.. 列::

````
```sh
sanic path.to.server:app --repl
```
````

.. 列::

```
もしくは、 `--dev`を実行すると、Sanicは自動的にREPLを開始します。 ただし、この場合、REPLを実際に開始する前に「ENTER」キーを押すように求められる場合があります。
```

.. 列::

````
```sh
sanic path.to.server:app --dev
```
````

![](/assets/images/repl.png)

上のスクリーンショットで見られるように、REPL は自動的にいくつかの変数をグローバル名前空間に追加します。 これらは次のとおりです。

- `app` - Sanic applicationインスタンス。 これは、`sanic` CLI に渡されるのと同じインスタンスです。
- `sanic` - `sanic`モジュール。 `import sanic` を実行したときにインポートされたモジュールと同じです。
- `do` - モック`Request`オブジェクトを作成し、アプリケーションに渡す関数。 これは、REPLからアプリケーションをテストする場合に便利です。
- `client` - アプリケーションへのリクエストを行うように設定された `httpx.Client` のインスタンス。 これは、REPLからアプリケーションをテストする場合に便利です。 **注意:** これはあなたの環境で `httpx` がインストールされている場合にのみ利用できます。

### Async/Await サポート

.. 列::

```
REPL は `async`/`await` 構文をサポートしています。つまり、REPL で `await` を使用して非同期操作が完了するまで待つことができます。 これは非同期コードのテストに便利です。
```

.. 列::

````
```python
>>> await app.ctx.db.fetchval("SELECT 1")
1 
```
````

### 変数 `app`

`app` 変数は、REPL が起動されたときに存在するため、アプリのインスタンスであることに注意してください。 これは、CLI コマンドを実行するときにロードされるインスタンスです。 つまり、ソースコードに加えられ、ワーカーにリロードされた変更は、 `app` 変数には反映されません。 リロードされたアプリケーション・インスタンスとやり取りしたい場合は、REPLを再起動する必要があります。

しかし、アドホックのテストとデバッグのためにREPLの元のアプリケーション・インスタンスにアクセスできることも非常に便利です。

### `client` 変数

[httpx](https://www.python-httpx.org/) があなたの環境にインストールされている場合、`client` 変数はREPLで利用可能になります。 これは実行中のアプリケーションへのリクエストを行うように設定された `httpx.Client` のインスタンスです。

.. 列::

```
これを使用するには、クライアントの HTTP メソッドのいずれかを呼び出してください。詳細については、[httpx documentation](https://www.python-httpx.org/api/#client) を参照してください。
```

.. 列::

````
```python
>>> client.get("/")
<Response [200 OK]>
```
````

### `do` 関数

上で説明したように、REPLが開始された時と同様に、`app` インスタンスが存在し、REPL内で変更されました。 サーバーを再ロードさせるインスタンスへの変更は、 `app` 変数には反映されません。 `do`関数が入ってくるところです。

新しいルートを追加するために REPL 内のアプリケーションを変更したとします。

```python
>>> @app.get("/new-route")
... async def new_route(request):
... return sanic.json({"hello": "world"})
...
 >>format@@4
```

`do` 関数を使ってリクエストをモックし、アプリケーションに実際の HTTP リクエストのように渡すことができます。 これにより、REPLを再起動せずに新しいルートをテストすることができます。

```python
>>> await do("/new-route")
Result(request=<Request: GET /new-route>, response=<JSONResponse: 200 application/json>)
```

`do` 関数は、アプリケーションから返された `Request` と `Response` オブジェクトを含む `Result` オブジェクトを返します。 `NamedTuple`ですので、名前で値にアクセスできます:

```python
>>> result = await do("/new-route")
>>> result.request
<Request: GET /new-route>
>>response
<JSONResponse: 200 application/json>
```

または、タプルを分割することによって:

```python
>>> リクエスト、応答 = await do("//new-route")
>>> リクエスト
<Request: GET /new-route>
>>応答
<JSONResponse: 200 application/json>
```

### `do` vs `client` はいつ使えばいいですか？

.. 列::

```
**Use `do` when ...**

- You want to test a route that does not exist in the running application
- You want to test a route that has been modified in the REPL
- You make a change to your application inside the REPL
```

.. 列::

```
**Use `client` when ...**

- You want to test a route that already exists in the running application
- You want to test a route that has been modified in your source code
- You want to send an actual HTTP request to your application
```

_v23.12_ に追加されました

## 開発モードを完了

.. 列::

```
デバッグモードにしたい場合は、自動リロードを実行している**と**、`dev=True`を渡すことができます。 これは**debug + auto reload**と同等です。

*v22.3*に追加されました
```

.. 列::

````
```sh
sanic path.to:app --dev
```
簡体字プロパティ
```sh
sanic path.to:app -d
 ``` も使用できます。
````

.. new:: v23.12

```
`--dev` フラグに v23.12 を追加すると、REPLを開始することができます。format@@0()を参照してください。 詳細は development.md#development-repl) セクションを参照してください。

V23 の時点。 2, `--dev` フラグは `--debug --reload --repl` とほぼ同じです。 `--dev` を使用すると、明示的に `--repl` フラグを渡すと、REPL を開始する必要があります。
```

.. 列::

```
`--dev`フラグを使用してREPLを無効にしたい場合は、`--no-repl`を渡すことができます。
```

.. 列::

````
```sh
sanic path.to:app --dev --no-repl
```
````

## 自動 TLS 証明書

`DEBUG`モードで実行している場合、Sanicに、localhostの一時的なTLS証明書の設定を処理するよう依頼できます。 これは、`https://`でローカル開発環境にアクセスしたい場合に役立ちます。

この機能は [mkcert](https://github.com/FiloSottile/mkcert) または [trustme](https://github.com/python-trio/trustme) のいずれかで提供されています。 どちらも良い選択ですが、いくつかの違いがあります。 `trustme`はPythonライブラリで、`pip`を使って環境にインストールできます。 これにより、envrionment の処理が簡単になりますが、HTTP/3 サーバーの実行時は互換性がありません。 `mkcert` はインストールプロセスにより複雑なものかもしれませんが、ローカルの CA をインストールして使いやすくすることができます。

.. 列::

```
`config.LOCAL_CERT_CREATOR` を設定することで、使用するプラットフォームを選択できます。`"auto"`に設定すると、可能な場合は `mkcert` を優先して、どちらかのオプションを選択します。
```

.. 列::

````
```python
app.config.LOCAL_CERT_CREATOR = "auto"
app.config.LOCAL_CERT_CREATOR = "mkcert"
app.config.LOCAL_CERT_CREATOR = "trustme"
```
````

.. 列::

```
Sanic サーバーの実行時間で自動的な TLS を有効にできます。
```

.. 列::

````
```sh
sanic path.to.server:app --auto-tls --debug
```
````

.. 警告::

```
ローカルホストの TLS 証明書 (`mkcert` と `trustme` の両方によって生成された証明書) は、本番環境には適していません。 *real* TLS 証明書の取得方法がわからない場合は、[How to...](../how-to/tls.md) セクションをチェックしてください。
```

_v22.6_に追加されました
