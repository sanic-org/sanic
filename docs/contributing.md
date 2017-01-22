# Contributing

Thank you for your interest! Sanic is always looking for contributors. If you
don't feel comfortable contributing code, adding docstrings to the source files
is very appreciated.

## Running tests

* `python -m pip install pytest`
* `python -m pytest tests`

## Documentation

Sanic's documentation is built
using [sphinx](http://www.sphinx-doc.org/en/1.5.1/). Guides are written in
Markdown and can be found in the `docs` folder, while the module reference is
automatically generated using `sphinx-apidoc`.

To generate the documentation from scratch:

```bash
sphinx-apidoc -fo docs/_api/ sanic
sphinx-build -b html docs docs/_build
```

The HTML documentation will be created in the `docs/_build` folder.

## Warning

One of the main goals of Sanic is speed. Code that lowers the performance of
Sanic without significant gains in usability, security, or features may not be
merged. Please don't let this intimidate you! If you have any concerns about an
idea, open an issue for discussion and help.

**Previous:** [Sanic extensions](extensions.md)
