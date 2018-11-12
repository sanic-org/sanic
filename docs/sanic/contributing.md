# Contributing

Thank you for your interest! Sanic is always looking for contributors. If you
don't feel comfortable contributing code, adding docstrings to the source files
is very appreciated.

## Installation

To develop on sanic (and mainly to just run the tests) it is highly recommend to
install from sources.

So assume you have already cloned the repo and are in the working directory with
a virtual environment already set up, then run:

```bash
python setup.py develop && pip install -r requirements-dev.txt
```

## Running tests

To run the tests for sanic it is recommended to use tox like so:

```bash
tox
```

See it's that simple!

## Pull requests!

So the pull request approval rules are pretty simple:
* All pull requests must pass unit tests
* All pull requests must be reviewed and approved by at least
one current collaborator on the project
* All pull requests must pass flake8 checks
* If you decide to remove/change anything from any common interface
a deprecation message should accompany it.
* If you implement a new feature you should have at least one unit
test to accompany it.

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
