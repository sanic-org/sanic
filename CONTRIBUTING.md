# Contributing

Thank you for your interest! Sanic is always looking for contributors. If you
don't feel comfortable contributing code, adding docstrings to the source files
is very appreciated.

We are committed to providing a friendly, safe and welcoming environment for all,
regardless of gender, sexual orientation, disability, ethnicity, religion,
or similar personal characteristic.
Our [code of conduct](./CONDUCT.md) sets the standards for behavior.

## Installation

To develop on sanic (and mainly to just run the tests) it is highly recommend to
install from sources.

So assume you have already cloned the repo and are in the working directory with
a virtual environment already set up, then run:

```bash
pip3 install -e . ".[dev]"
```

# Dependency Changes

`Sanic` doesn't use `requirements*.txt` files to manage any kind of dependencies related to it in order to simplify the
effort required in managing the dependencies. Please make sure you have read and understood the following section of
the document that explains the way `sanic` manages dependencies inside the `setup.py` file.

| Dependency Type                           | Usage                                                                      | Installation                 |
| ------------------------------------------| -------------------------------------------------------------------------- | ---------------------------  |
| requirements                              | Bare minimum dependencies required for sanic to function                   | pip3 install -e .            |
| tests_require / extras_require['test']    | Dependencies required to run the Unit Tests for `sanic`                    | pip3 install -e '.[test]'    |
| extras_require['dev']                     | Additional Development requirements to add contributing                    | pip3 install -e '.[dev]'     |
| extras_require['docs']                    | Dependencies required to enable building and enhancing sanic documentation | pip3 install -e '.[docs]'    |

## Running all tests 
To run the tests for Sanic it is recommended to use tox like so:

```bash
tox
```
See it's that simple!

`tox.ini` contains different environments. Running `tox` without any arguments will 
run all unittests, perform lint and other checks. 

## Run unittests : 
`tox` environment -> `[testenv]`

To execute only unittests, run `tox` with environment like so: 

```bash
tox -e py36 -v -- tests/test_config.py
# or 
tox -e py37 -v -- tests/test_config.py
```

## Run lint checks : 
`tox` environment -> `[testenv:lint]`

Permform `flake8`, `black` and `isort` checks.
```bash
tox -e lint
```

## Run other checks : 
`tox` environment -> `[testenv:check]`

Perform other checks.
```bash
tox -e check
```

# Code Style 
To maintain the code consistency, Sanic uses following tools. 

1. [isort](https://github.com/timothycrosley/isort)
2. [black](https://github.com/python/black)
2. [flake8](https://github.com/PyCQA/flake8)


## isort
`isort` sorts Python imports. It divides imports into three 
categories sorted each in alphabetical order. 
  1. built-in
  2. third-party
  3. project-specific

## black
`black` is a Python code formatter.

## flake8
`flake8` is a Python style guide that wraps following tools into one.
1. PyFlakes
2. pycodestyle
3. Ned Batchelder's McCabe script 

`isort`, `black` and `flake8` checks are performed during `tox` lint checks. 

Refer [tox](https://tox.readthedocs.io/en/latest/index.html) documentation for more details.

## Pull requests!

So the pull request approval rules are pretty simple:
1. All pull requests must pass unit tests.
2. All pull requests must be reviewed and approved by at least
  one current collaborator on the project.
3. All pull requests must pass flake8 checks.
4. All pull requests must be consistent with the existing code.
5. If you decide to remove/change anything from any common interface
  a deprecation message should accompany it.
6. If you implement a new feature you should have at least one unit
  test to accompany it.
7. An example must be one of the following:
  * Example of how to use Sanic
  * Example of how to use Sanic extensions
  * Example of how to use Sanic and asynchronous library

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
