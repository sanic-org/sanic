---
title: 神经扩展-健康监测
---

# 健康监测

健康监视器需要`sanic>=22.9`和`sanic-ext>=22.9`。

您可以设置 Sanic 扩展来监测您的工作流程的健康状况。 This requires that you not be in [single process mode](../../guide/running/manager.md#single-process-mode).

## 设置

.. 列:

```
离开框，健康监视器被禁用。如果您想要使用它，您需要选择进入并启用端点。
```

.. 列:

````
```python
app.config.HEALTH = True
app.config.HEALTH_ENDPOINT = True
```
````

## 如何工作

监测员建立了一个新的背景程序，将定期从每个工人过程中收到直观的确认书。 如果某个工人进程错过多次报告，则监视器会重新启动该工人。

## 诊断终点

.. 列:

```
The health monitor will also enable a diagnostics endpoint that outputs the [worker state](../../guide/running/manager.md#worker-state). By default is id disabled.

.. danger:: 

    The diagnostics endpoint is not secured. If you are deploying it in a production environment, you should take steps to protect it with a proxy server if you are using one. If not, you may want to consider disabling this feature in production since it will leak details about your server state.
```

.. 列:

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

## 配置

| 关键字                                                                               | 类型     | 默认设置            | 描述               |
| --------------------------------------------------------------------------------- | ------ | --------------- | ---------------- |
| 生命值                                                                               | `bool` | `False`         | 是否启用此扩展。         |
| HEALTH_ENDPOINT                                              | `bool` | `False`         | 是否启用诊断端点。        |
| HEALTH_MEX_MISSES                       | `int`  | `3`             | 工作流程重新启动前连续缺失次数。 |
| HEALTH_MISSED_TITLE                     | `int`  | `10`            | 检查工人流程健康的秒数。     |
| HEALTH_MONITOR                                               | `bool` | `True`          | 是否启用健康监视器。       |
| HEALTH_REPORT_INTERVAL                  | `int`  | `5`             | 每次确认活动之间的秒数。     |
| HEALTH_URI_TO_INFO | `str`  | `""`            | 诊断端点的 URI 路径。    |
| HEALTH_URL_PREFIX                       | `str`  | `"/__health__"` | 诊断蓝图的 URI 前缀。    |
