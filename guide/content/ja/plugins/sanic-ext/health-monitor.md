---
title: サニックエクステンション - ヘルスモニター
---

# ヘルスモニター

ヘルスモニターには、`sanic>=22.9` と `sanic-ext>=22.9` の両方が必要です。

Sanic Extensionsを設定して、作業工程の健全性を監視できます。 format@@0(../../guide/deployment/manager.md#single-process-mode) ではないことが必要です。

## セットアップ

.. 列::

```
ヘルスモニターは無効になっています。使用したい場合はオプトインしてエンドポイントを有効にする必要があります。
```

.. 列::

````
```python
app.config.HEALTH = True
app.config.HEALTH_ENDPOINT = True
```
````

## どのように機能します

モニターは新しいバックグラウンドプロセスを設定し、それぞれのワーカープロセスから定期的に活気を認識します。 ワーカープロセスがレポートを何度も見逃した場合、モニターはそのワーカーを再起動します。

## 診断エンドポイント

.. 列::

```
ヘルスモニターは、[worker state](../../guide/deployment/manager)を出力する診断エンドポイントも有効にします。 d#worker-state). デフォルトではIDが無効になっています。

.. danger:: 

    診断エンドポイントはセキュリティ保護されていません。 本番環境でデプロイする場合は、プロキシサーバーを使用して保護する手順を実行する必要があります。 そうでない場合は、サーバーの状態に関する詳細が漏れるため、本番環境でこの機能を無効にすることを検討することをお勧めします。
```

.. 列::

````
```
$ curl http://localhost:8000/__health__
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

## 設定

| キー                                   | タイプ    | デフォルト           | 説明                          |
| ------------------------------------ | ------ | --------------- | --------------------------- |
| 健康                                   | `bool` | `False`         | この拡張機能を有効にするかどうか。           |
| HEALTH_ENDPOINT | `bool` | `False`         | 診断のエンドポイントを有効にするかどうか。       |
| 最大値が足りません                            | `int`  | `3`             | ワーカープロセスが再起動される前に連続したミスの数。  |
| 健康状態がありません。                          | `int`  | `10`            | モニターがワーカープロセスの健全性をチェックする秒数。 |
| ヘルスモニター                              | `bool` | `True`          | かどうかのヘルスモニターを有効にします。        |
| 内部レポート                               | `int`  | `5`             | 活気のあるそれぞれの確認を報告するまでの秒数。     |
| CHALLENGE_LABEL | `str`  | `""`            | 診断エンドポイントの URI パス。          |
| PREFIX                               | `str`  | `"/__health__"` | 診断のブループリントの URI プレフィックス。    |
