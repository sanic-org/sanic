---
title: Sanic 扩展-背景记录器
---

# 背景记录器

背景记录器需要 `sanic>=22.9` 和 `sanic-ext>=22.9`。

您可以设置 Sanic 扩展来从后台进程中记录您所有的消息。 这要求您不要处于[单一进程模式](../../guide/deplement/manager.md#单一进程模式)。

日志记录有时可能是一个昂贵的操作。 通过将所有登录推出到后台流程，您可以获得一些性能效益。

## 设置

.. 列:

```
在方框之外，后台记录器已禁用。如果您想要使用它，您将需要选入它。
```

.. 列:

````
```python
app.config.LOGING = True
```
````

## 如何工作

启用时，扩展将创建 `multoprocessing.Queue` 。 它将移除[默认 Sanic loggers](../../guide/best practices/logging.md) 上的所有处理程序，并将其替换为 [`QueueHandler`](https://docs.python.org/3/library/logging.handlers.html#queuehandler)。 当消息被记录时，它将被处理器推送到队列。 并通过后台进程读取原有的日志处理程序。 这意味着您仍然可以将日志配置为正常，它应该“只能工作”。

## 配置

| 关键字                                                                                  | 类型     | 默认设置    | 描述             |
| ------------------------------------------------------------------------------------ | ------ | ------- | -------------- |
| 正在登录                                                                                 | `bool` | `False` | 是否启用此扩展。       |
| LOGING_QUEUE_MAX_SIZE | `int`  | `4096`  | 拒绝消息之前队列的最大尺寸。 |