---
title: ワーカーマネージャー
---

# ワーカーマネージャー

Worker マネージャーとその機能はバージョン 22.9 で導入されました。

_このセクションの詳細は、より高度な使用を目的としています。開始するのに必要なものではありません。_

マネージャーの目的は、開発環境と生産環境の間の一貫性と柔軟性を創造することです。 単一のワーカーを実行するか、複数のワーカーを実行するかに関わらず、自動再ロードの有無に関わらず、経験は同じになります。

一般的には以下のようになります:

![](https://user-images.githubusercontent.com/166269/17677618-3b4089c3-6c6a-4ecc-8d7a-7eba2a7f29b0.png)

Sanic を実行すると、メインプロセスは `WorkerManager` をインスタンス化します。 そのマネージャーは1つ以上の `WorkerProcess` の実行を担当しています。 一般的には2種類のプロセスがあります。

- サーバープロセスと
- 非サーバー プロセス

ユーザーガイドでは、一般的にサーバープロセスを意味する「ワーカー」または「ワーカープロセス」という用語を使用します。 「マネージャー」とは、メインプロセスで実行されている単一のワーカーマネージャーを意味します。

## Sanic Server がプロセスを開始する方法

Sanic は [spawn](https://docs.python.org/3/library/multiprocessing.html#context-and-start-methods) を使用してプロセスを開始します。 つまり、プロセス/ワーカーごとに、アプリケーションのグローバルスコープが独自のスレッドで実行されます。 あなたがCLIを使ってSanicを実行しない場合\*この実際的な影響。 `__main__`でのみ実行されるように、ブロックの中に実行コードを入れ子にする必要があります。

```python
if __name__ == "__main__":
    app.run()
```

しない場合は、次のようなエラーメッセージが表示される可能性があります。

```
sanic.exceptions.ServerError: Sanic server could not start: [Errno 98] Address already in use.

This may have happened if you are running Sanic in the global scope and not inside of a `if __name__ == "__main__"` block.

See more information: https://sanic.dev/en/guide/deployment/manager.html#how-sanic-server-starts-processes
```

この問題を解決するには、`__name__ == "__main__"`ブロックの中に Sanic runを入れ子にする必要があります。 ネストの後にこのメッセージを受信し続ける場合、または CLI の使用中にこのメッセージが表示される場合。 使おうとしているポートはマシン上では利用できない 別のポートを選択しなければならない

### ワーカーを開始

すべてのワーカープロセスは開始時に確認を送信する必要があります。 これはボンネットの下で起こり、開発者としてあなたは何もする必要はありません。 ただし、1人以上のワーカーがメッセージを送信しない場合、マネージャーはステータスコード`1`で終了します。 またはワーカープロセスは、起動中に例外をスローします。 例外が発生しない場合、マネージャーは承認のために最大30秒間待機します。

.. 列::

```
あなたが開始するために多くの時間が必要になることを知っている状況では、マネージャーをmonkeypatch ことができます。 しきい値はリスナーの中には含まれません。 アプリケーションのグローバルな範囲内のすべての実行時間に制限されます。

この問題に遭遇した場合、起動が遅い原因について詳しく調べる必要がある可能性があります。
```

.. 列::

````
```python
from sanic.worker.manager import WorkerManager

WorkerManager.THRESHOLD = 100 # Value is in 0.1s
```
````

詳細は format@@0(#worker-ack) を参照してください。

.. 列::

```
上記のように、Sanic は [spawn](https://docs.python.org/3/library/multiprocessing.html#context-and-start-methods) を使用してワーカープロセスを開始します。 この動作を変更し、異なるstart メソッドを使用することの影響を認識したい場合は、ここに示すように変更できます。
```

.. 列::

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

### Worker ack

すべてのワーカーがサブプロセスで実行されている場合、潜在的な問題が生じます:デッドロック。 これは子プロセスが機能を停止した場合に発生することがありますが、メインプロセスはこれが起こったことを認識していません。 したがって、Sanicサーバーは起動後にメインプロセスに自動的に`ack`メッセージ（確認のための略）を送信します。

バージョン22.9では、`ack`のタイムアウトは短く、`5s`に制限されていました。 バージョン 22.12 では、タイムアウトは `30s` に延長されました。 アプリケーションが30秒後にシャットダウンする場合、このしきい値を手動で増やす必要があるかもしれません。

.. 列::

```
`WorkerManager.THRESHOLD` の値は `0.1s` 単位です。したがって1分に設定するには、値を `600` に設定してください。

この値は、アプリケーションで可能な限り早期に設定する必要があり、理想的にはグローバルスコープで設定する必要があります。 メインプロセスが開始された後に設定することはできません。
```

.. 列::

````
```python
from sanic.worker.manager import WorkerManager

WorkerManager.THRESHOLD = 600
```
````

### ゼロダウンタイムの再起動

デフォルトでは、ワーカーを再起動すると、Sanicは新しいプロセスを開始する前に既存のプロセスを最初に分解します。

本番環境で再起動機能を使用しようとしている場合は、ゼロダウンタイムのリロードに興味があるかもしれません。 これは、新しいプロセスを開始するために、再ローダーを強制的に変更することによって達成することができます。 [ack](#worker-ack) まで待ってから、古いプロセスを分解します。

.. 列::

```
マルチプレクサから`zero_downtime`引数を使います。
```

.. 列::

````
```python
app.m.restart(zero_downtime=True)
```
````

_v22.12_ に追加されました

## ワーカープロセス間で共有コンテキストを使用する

Python provides a few methods for [exchanging objects](https://docs.python.org/3/library/multiprocessing.html#exchanging-objects-between-processes), [synchronizing](https://docs.python.org/3/library/multiprocessing.html#synchronization-between-processes), and [sharing state](https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes) between processes. これには通常、 `multiprocessing` と `ctypes` モジュールのオブジェクトが含まれます。

あなたがこれらのオブジェクトとそれらの操作方法に精通しているなら Sanicはこれらのオブジェクトをワーカープロセス間で共有するためのAPIを提供しています。 慣れていない場合は、 上記のリンク先の Python ドキュメントを読んで、共有コンテキストの実装を進める前にいくつかの例を試してみることをお勧めします。

format@@0(../basics/app.md#application-context) と同様に、アプリケーションの寿命にわたってアプリケーションが `app と状態を共有することができます。 tx`は、上記の特別なオブジェクトに対して共有コンテキストを提供します。 このコンテキストは `app.shared_ctx` として利用できます。この目的のためにオブジェクトを共有するために **ONLY** を使用します。

`shared_ctx` は次のようになります:

- _NOT_ `int` や `dict` や `list` などの通常のオブジェクトを共有していません
- _違う_マシン上で実行されているSanicインスタンス間での状態の共有
- _NOT_ 状態をワーカー以外のプロセスと共有
- **のみ** 同じマネージャーによって管理されたサーバーワーカー間の状態を共有

`shared_ctx` に不適切なオブジェクトを追加すると警告になり、エラーにならない可能性があります。 `shared_ctx` に誤って安全でないオブジェクトを追加しないように注意してください。 これらの警告が原因でここに指示された場合、`shared_ctx` で安全でないオブジェクトを誤って使用した可能性があります。

.. 列::

```
共有オブジェクトを作成するには、メインプロセスで作成し、 `main_process_start` リスナーの中に添付する必要があります。
```

.. 列::

````
```python
from multiprocessing import Queue

@app.main_process_start
async def main_process_start(app):
    app.shared_ctx.queue = Queue()
```
````

このリスナーの外で `shared_ctx` オブジェクトにアタッチしようとすると、 `RuntimeError` になります。

.. 列::

```
`main_process_start` リスナーでオブジェクトを作成し、`shared_ctx` にアタッチした後 アプリケーションインスタンスが利用可能な場所(例:リスナー、ミドルウェア、リクエストハンドラ)は、ワーカー内で利用可能になります。
```

.. 列::

````
```python
from multiprocessing import Queue

@app.get(char@@2)
async def handler(request):
    request.app.shared_ctx.queue.put(1)
    ...
```
````

## マルチプレクサへのアクセス

アプリケーションインスタンスは、Manager や他のワーカープロセスとの相互作用へのアクセスを提供するオブジェクトへのアクセス権を持っています。 オブジェクトは `app.multiple` プロパティとしてアタッチされますが、`app.m` は別名でアクセスしやすくなります。

.. 列::

```
たとえば、現在のワーカーの状態にアクセスできます。
```

.. 列::

````
```python
@app.on_request
async def print_state(request: Request):
    print(request.app.m.name)
    print(request.app.m.pid)
    print(request.app.m.state)
```
```
Sanic-Server-0-0
99999
{'server': True, 'state': 'ACKED', 'pid': 99999, 'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), 'starts': 2, 'restart_at': datetime.datetime(2022, 10, 1, 0, 0, 12, 861332, tzinfo=datetime.timezone.utc)}
```
````

.. 列::

```
`multiplace`は、マネージャーを終了するか、ワーカープロセスを再起動するためのアクセス権を持っています
```

.. 列::

````
```python
# shutdown the entire application and all processes
app.m.name.terminate()

# restart the current worker only
app.m.name.restart()

# restart specific workers only (comma delimited)
app.m.name.restart("Sanic-Server-4-0,Sanic-Server-7-0")

# restart ALL workers
app.m.name.restart(all_workers=True)  # Available v22.12+
```
````

## ワーカーの状態

.. 列::

```
上に示すように、`multiplace` は現在の実行中のワーカーの状態を報告するためにアクセスできます。 しかし、それはまた、実行されているすべてのプロセスのための状態を含みます。
```

.. 列::

````
```python
@app.on_request
async def print_state(request: Request):
    print(request.app.m.workers)
```
```
{
    'Sanic-Main': {'pid': 99997},
    'Sanic-Server-0-0': {
        'server': True,
        'state': 'ACKED',
        'pid': 9999,
        'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
        'starts': 2,
        'restart_at': datetime.datetime(2022, 10, 1, 0, 0, 12, 861332, tzinfo=datetime.timezone.utc)
    },
    'Sanic-Reloader-0': {
        'server': False,
        'state': 'STARTED',
        'pid': 99998,
        'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
        'starts': 1
    }
}
```
````

可能な状態は次のとおりです。

- `NONE` - 作業者が作成されましたが、プロセスはまだありません。
- `IDLE` - プロセスは作成されましたが、まだ実行されていません
- `STARTING` - プロセスが開始されています
- `STARTED` - プロセスが開始されました
- `ACKED` - プロセスが開始され、承認を送信しました (通常はサーバーのプロセスのみ)
- `JOINED` - プロセスが終了し、メインプロセスに参加しました
- `TERMINATED` - プロセスが終了し、終了しました
- `RESTARTING` - プロセスが再起動しています
- `FAILED` - プロセスが例外に遭遇し、実行されなくなりました
- `COMPLETED` - プロセスが完了し、終了しました

## 組み込みの非サーバー プロセス

前述のように、マネージャーは非サーバプロセスを実行することもできます。 Sanicには2種類の非サーバープロセスが組み込まれており、format@@0(#running-custom-processes) を使用できます。

二つの組み込みプロセスは

- [auto-reloader](./development.md#automatic-reloader) は、ファイルシステムの変更を監視し、再起動をトリガーするために必要に応じて有効になります
- [inspector](#inspector) オプションで実行中のインスタンスの状態への外部アクセスを提供することができます

## Inspector

Sanicは、CLIに「multiplane」の状態と機能を公開する能力を持っています。 現在、実行中のSanicインスタンスと同じマシン上でCLIコマンドを実行する必要があります。 デフォルトではインスペクターは無効になっています。

.. 列::

```
有効にするには、設定値を `True` に設定します。
```

.. 列::

````
```python
app.config.INSPECTOR = True
```
````

これで、これらの CLI コマンドのいずれかを実行することができます。

```
健全な検査 reload サーバワーカーのリロードをトリガーする
sanic inspect shutdown the application and all processes
sanic inspect scale N ワーカー数を N
sanic inspect <custom>                    カスタムコマンドを実行
```

![](https://user-images.githubusercontent.com/166269/190099384-2f2f3fae-22d5-4529-b279-8446f6b5f9bd.png)

.. 列::

```
これは、マシン上の小さなHTTPサービスを公開することで動作します。設定値を使用して場所を制御できます。
```

.. 列::

````
```python
app.config.INSPECTOR_HOST = "localhost"
app.config.INSPECTOR_PORT = 6457
```
````

format@@0(./inspector.md) は、インスペクターで何が可能かを知ることができます。

## カスタムプロセスの実行

Sanicで管理されたカスタムプロセスを実行するには、呼び出し可能ファイルを作成する必要があります。 そのプロセスが長時間実行されることを意図している場合は、`SIGINT`または`SIGTERM`信号によるシャットダウンコールを処理する必要があります。

.. 列::

```
Pythonでそれを行う最も簡単な方法は、`KeyboardInterrupt`でループをラップすることです。

ボットのような別のアプリケーションを実行する場合。 この信号を処理する能力を持っている可能性があります おそらく何もする必要はありません
```

.. 列::

````
```python
from time import slep

def my_process(foo):
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("done")
```
````

.. 列::

```
その呼び出し可能ファイルは `main_process_ready` リスナーに登録する必要があります。 重要なのは、format@@0(#using-shared-context-between-worker-processes) オブジェクトを登録するのと同じ場所ではないことです。
```

.. 列::

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
#   app.manager.manage(<name>, <callable>, <kwargs>)
    app.manager.manage("MyProcess", my_process, {"foo": "bar"})
```
````

### Transient v.耐久性のあるプロセス

.. 列::

```
`manage` メソッドでプロセスを管理する場合は、プロセスをトランジェントまたは耐久性にするオプションがあります。 一時的なプロセスは、オートリローダーによって再起動され、耐久性のあるプロセスは実行されません。

デフォルトでは、すべてのプロセスは耐久性があります。
```

.. 列::

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manage(
        "MyProcess",
        my_process,
        {"foo": "bar"},
        transitent=True,
    )
```
````

### 追跡されていないプロセス

Sanicは全プロセスの状態を追跡します。 これは、 [multiplexer](./manager.md#access-to-the-multiplexer) オブジェクト、または [Inspector](./manager.md#inspector) からプロセスの状態にアクセスできることを意味します。

詳細は [worker state](./manager.md#worker-state) を参照してください。

バックグラウンドプロセスが長時間実行されていない場合もあります。 完了まで一度実行し、それらは終了します。 完了すると `FAILED` または `COMPLETED` のいずれかになります。

.. 列::

```
長時間実行されていないプロセスを実行している場合は、`manage`メソッドに`tracked=False`を設定することでトラッキングを解除できます。 これは、プロセスが完了すると、追跡されたプロセスのリストから削除されることを意味します。 実行中のプロセスの状態のみを確認できます。
```

.. 列::

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manage(
        "OneAndDone",
        do_once,
        {},
        tracked=False,
    )
```
````

_v23.12_ に追加されました

### 再起動可能なカスタムプロセス

トランジェントであるカスタムプロセスは、**常に**再び起動可能になります。 つまり、自動再起動は想定どおりに動作します。 ただし、プロセスを手動で再起動できますが、オートリローダーで再起動できない場合はどうなりますか?

.. 列::

```
このシナリオでは、`manage`メソッドで`restartable=True`を設定できます。 これにより、手動でプロセスを再起動することができますが、自動再起動では再起動しません。
```

.. 列::

````
```python
@app.main_process_ready
async def ready(app: Sanic, _):
    app.manager.manage(
        "MyProcess",
        my_process,
        {"foo": "bar"},
        restartable=True,
    )
```
````

.. 列::

```
マルチプレクサから手動でそのプロセスを再起動できるようになりました。
```

.. 列::

````
```python
@app.get("/restart")
async def restart_handler(request: Request):
    request.app.m.restart("Sanic-MyProcess-0")
    return json({"foo": request.app.m.name})
```
````

_v23.12_ に追加されました

### オンザフライプロセス管理

カスタムプロセスは通常 `main_process_ready` リスナーに追加されます。 ただし、アプリケーションの開始後にプロセスを追加したい場合があります。 たとえば、リクエストハンドラからプロセスを追加したい場合があります。 マルチプレクサはこれを行う方法を提供します。

.. 列::

```
マルチプレクサへの参照ができたら、プロセスを追加するために `manage` を呼び出すことができます。 マネージャーの `manage` メソッドと同じ動作をします。
```

.. 列::

````
```python
@app.post("/start")
async def start_handler(request: Request):
    request.app.m.manage(
        "MyProcess",
        my_process,
        {"foo": "bar"},
        workers=2,
    )
    return json({"foo": request.app.m.name})
```
````

_v23.12_ に追加されました

## シングルプロセスモード

.. 列::

```
複数のプロセスの実行をオプトアウトしたい場合は、1つのプロセスでのみSanicを実行できます。 この場合、マネージャーは実行されません。 また、プロセスを必要とする機能(自動リロード、インスペクタなど)にもアクセスできません。
```

.. 列::

````
```sh
sanic path.to.server:app --single-process
```
```python
if __name__ == "__main__":
    app.run(single_process=True)
```
```python
if __name__ == "__main__":
    app.prepare(single_process=True)
    Sanic.serve_single()
```
````

## Sanic and multiprocessing

Sanic は [`multiprocessing` module](https://docs.python.org/3/library/multiprocessing.html) を使用してワーカープロセスを管理します。 通常、Sanic の機能を妨げる可能性があるため、このモジュールの低レベル使用(start メソッドの設定など)は避けるべきです。

### Pythonでメソッドを開始

Sanicが何をしようとしているのかを説明する前に、`start_method`とは何か、なぜそれが重要なのかを理解することが重要です。 Python では一般的に、プロセスを開始するための 3 つの異なるメソッドが使用できます。

- `fork`
- `spawn`
- `forkserver`

`fork` と `forkserver` メソッドは Unix システムでのみ使用でき、`spawn` は Windows で利用できる唯一のメソッドです。 選択肢がある Unix システムでは、`fork` は一般的にデフォルトのシステムメソッドです。

これらのメソッドの違いについては、format@@0(https://docs.python.org/3/library/multiprocessing.html#context-and-start-methods)を参照してください。 ただし、重要なことは、基本的に親プロセスのメモリ全体を子プロセスにコピーすることです。 `spawn` は新しいプロセスを作成し、そのプロセスにアプリケーションをロードします。 CLIを使っていない場合は、`__name__ == "__main__"`ブロックの中に、Sanic `run` を入れ子にする必要があります。

### サニックメソッドと開始方法

デフォルトでは、Sanicはstartメソッドとして`spawn`を使用します。 これは、Windows で利用可能な唯一の方法であり、Unix システムで最も安全な方法であるためです。

.. 列::

```
もしあなたが Unix システムで Sanic を実行していて、代わりに `fork` を使用したい場合。 `Sanic`クラスに`start_method`を設定することで可能です。 他のモジュールをインポートする前に、アプリケーションで可能な限り早期にこれを行い、グローバルスコープで理想的にこれを行う必要があります。
```

.. 列::

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

### `RuntimeError`をクリアする

次のような `RuntimeError` を受け取ったかもしれません。

```
RuntimeError: Startメソッド'spawn'が要求されましたが、'fork'は既に設定されていました。
```

そうであれば、アプリケーションのどこかでSanicがやろうとしていることと競合するstartメソッドを設定しようとしていることを意味します。 これを解決するにはいくつかのオプションがあります。

.. 列::

```
**OPTION 1:** Sanicに、startメソッドが設定されており、再度設定しないようにすることができます。
```

.. 列::

````
```python
from sanic import Sanic

Sanic.START_METHOD_SET = True
```
````

.. 列::

```
**OPTION 2:** Sanicに、 `fork` を使うつもりで、 `spawn` を使わないように伝えることができます。
```

.. 列::

````
```python
from sanic import Sanic

Sanic.start_method = "fork"
```
````

.. 列::

```
**OPTION 3:** `multiprocessing` start メソッドを設定することで、`fork` の代わりに `spawn` を使用するようにPythonに指示できます。
```

.. 列::

````
```python
import multiprocessing

multiprocessing.set_start_method("spawn")
```
````

これらのいずれかのオプションでは、アプリケーションでできるだけ早くこのコードを実行する必要があります。 具体的なシナリオによっては、いくつかのオプションを組み合わせる必要がある場合があります。

.. note::

````
The potential issues that arise from this problem are usually easily solved by just allowing Sanic to be in charge of multiprocessing. This usually means making use of the `main_process_start` and `main_process_ready` listeners to deal with multiprocessing issues. For example, you should move instantiating multiprocessing primitives that do a lot of work under the hood from the global scope and into a listener.

```python
# This is BAD; avoid the global scope
from multiprocessing import Queue

q = Queue()
```

```python
# This is GOOD; the queue is made in a listener and shared to all the processes on the shared_ctx
from multiprocessing import Queue

@app.main_process_start
async def main_process_start(app):
    app.shared_ctx.q = Queue()
```
````
