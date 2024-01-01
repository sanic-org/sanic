---
title: 自动发现
---

# 自动发现蓝图、中程和侦听器

> 我如何自动发现我正在使用的组件来构建我的应用程序？

某人在构建应用程序时面临的第一个问题是_如何_构建项目。 Sanic大量使用装饰器注册路由处理器、中间人和听众。 在创建蓝图后，它们需要安装到应用程序上。

可能的解决方案是一个 **每件事** 导入并应用到 Sanic 实例的单一文件。 另一个正在环绕着Sanic实例作为一个全球变量。 这两种解决办法都有其缺点。

另一种办法是自动发现。 您将您的应用程序指向模块 (已导入，或字符串)，并让它连接一切。

## `server.py`

```python
from sanic import Sanic
from sanic.response import empty

import blueprints
from utility import autodiscover

app = Sanic("auto", register=True)
autodiscover(
    app,
    blueprints,
    "parent.child",
    "listeners.something",
    recursive=True,
)

app.route("/")(lambda _: empty())
```

```bash
[2021-03-02 21:37:02 +0200] [880451] [INFO] Goin' Fast @ http://127.0.0.1:9999
[2021-03-02 21:37:02 +0200] [880451] [DEBUG] something
[2021-03-02 21:37:02 +0200] [880451] [DEBUG] something @ nested
[2021-03-02 21:37:02 +0200] [880451] [DEBUG] something @ level1
[2021-03-02 21:37:02 +0200] [880451] [DEBUG] something @ level3
[2021-03-02 21:37:02 +0200] [880451] [DEBUG] something inside __init__.py
[2021-03-02 21:37:02 +0200] [880451] [INFO] Starting worker [880451]
```

## `utility.py`

```python

from glob import glob
from importlib import import_module, util
from inspect import getmembers
from pathlib import Path
from types import ModuleType
from typing import Union

from sanic.blueprints import Blueprint

def autodiscover(
    app, *module_names: Union[str, ModuleType], recursive: bool = False
):
    mod = app.__module__
    blueprints = set()
    _imported = set()

    def _find_bps(module):
        nonlocal blueprints

        for _, member in getmembers(module):
            if isinstance(member, Blueprint):
                blueprints.add(member)

    for module in module_names:
        if isinstance(module, str):
            module = import_module(module, mod)
            _imported.add(module.__file__)
        _find_bps(module)

        if recursive:
            base = Path(module.__file__).parent
            for path in glob(f"{base}/**/*.py", recursive=True):
                if path not in _imported:
                    name = "module"
                    if "__init__" in path:
                        *_, name, __ = path.split("/")
                    spec = util.spec_from_file_location(name, path)
                    specmod = util.module_from_spec(spec)
                    _imported.add(path)
                    spec.loader.exec_module(specmod)
                    _find_bps(specmod)

    for bp in blueprints:
        app.blueprint(bp)
```

## `蓝图/level1.py`

```python
from sanic import Blueprint
from sanic.log import logger

level1 = Blueprint("level1")

@level1.after_server_start
def print_something(app, loop):
    logger.debug("something @ level1")
```

## “蓝图1e/2/level3.py”

```python
from sanic import Blueprint
from sanic.log import logger

level3 = Blueprint("level3")

@level3.after_server_start
def print_something(app, loop):
    logger.debug("something @ level3")
```

## `监听器/something.py`

```python
from sanic import Sanic
from sanic.log import logger

app = Sanic.get_app("auto")

@app.after_server_start
def print_something(app, loop):
    logger.debug("something")
```

## `parent/child/__init__.py`

```python
from sanic import Blueprint
from sanic.log import logger

bp = Blueprint("__init__")

@bp.after_server_start
def print_something(app, loop):
    logger.debug("something inside __init__.py")
```

## `parent/child/nested.py`

```python
从sanic.log 导入蓝图
从sanic.log 导入记录器

嵌套= Blueprint("嵌套")

@nested.after _server_start
def print_something(app, loop):
    logger.debug("some @ 嵌套")
```

***

```text
here is the dir tree
generate with 'find . -type d -name "__pycache__" -exec rm -rf {} +; tree'

. # run 'sanic sever -d' here
├── blueprints
│   ├── __init__.py # you need add this file, just empty
│   ├── level1.py
│   └── one
│       └── two
│           └── level3.py
├── listeners
│   └── something.py
├── parent
│   └── child
│       ├── __init__.py
│       └── nested.py
├── server.py
└── utility.py
```

```sh
源 ./.venv/bin/激活 # 激活安装在
sanic sever -d # 中的 python venv 在包含服务器的目录中运行它。
```

```text
you will see "something ***" like this:

[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something inside __init__.py
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ level3
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ level1
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ nested
```
