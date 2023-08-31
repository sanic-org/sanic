---
title: Autodiscovery
---

# Autodiscovery of Blueprints, Middleware, and Listeners

> How do I autodiscover the components I am using to build my application?

One of the first problems someone faces when building an application, is *how* to structure the project. Sanic makes heavy use of decorators to register route handlers, middleware, and listeners. And, after creating blueprints, they need to be mounted to the application.

A possible solution is a single file in which **everything** is imported and applied to the Sanic instance. Another is passing around the Sanic instance as a global variable. Both of these solutions have their drawbacks.

An alternative is autodiscovery. You point your application at modules (already imported, or strings), and let it wire everything up.

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

## `blueprints/level1.py`

```python
from sanic import Blueprint
from sanic.log import logger

level1 = Blueprint("level1")

@level1.after_server_start
def print_something(app, loop):
    logger.debug("something @ level1")
```

## `blueprints/one/two/level3.py`

```python
from sanic import Blueprint
from sanic.log import logger

level3 = Blueprint("level3")

@level3.after_server_start
def print_something(app, loop):
    logger.debug("something @ level3")
```

## `listeners/something.py`

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
from sanic import Blueprint
from sanic.log import logger

nested = Blueprint("nested")

@nested.after_server_start
def print_something(app, loop):
    logger.debug("something @ nested")
```

---

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
source ./.venv/bin/activate # activate the python venv which sanic is installed in
sanic sever -d # run this in the directory containing server.py
```

```text
you will see "something ***" like this:

[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something inside __init__.py
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ level3
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ level1
[2023-07-12 11:23:36 +0000] [113704] [DEBUG] something @ nested
```

