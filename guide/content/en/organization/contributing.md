# Contributing

Thank you for your interest! Sanic is always looking for contributors. If you don't feel comfortable contributing code, adding docstrings to the source files, or helping with the [Sanic User Guide](https://github.com/sanic-org/sanic-guide) by providing documentation or implementation examples would be appreciated!

We are committed to providing a friendly, safe and welcoming environment for all, regardless of gender, sexual orientation, disability, ethnicity, religion, or similar personal characteristic. Our [code of conduct](https://github.com/sanic-org/sanic/blob/master/CONDUCT.md) sets the standards for behavior.

## Installation

To develop on Sanic (and mainly to just run the tests) it is highly recommend to install from sources.

So assume you have already cloned the repo and are in the working directory with a virtual environment already set up, then run:

```sh
pip install -e ".[dev]"
```

## Dependency Changes

`Sanic` doesn't use `requirements*.txt` files to manage any kind of dependencies related to it in order to simplify the effort required in managing the dependencies. Please make sure you have read and understood the following section of the document that explains the way `sanic` manages dependencies inside the `setup.py` file.

| Dependency Type                 | Usage                                             | Installation                 |
| ------------------------------- | ------------------------------------------------- | ---------------------------- |
| requirements                    | Bare minimum dependencies required for sanic to function | `pip3 install -e .`         |
| tests_require / extras_require['test'] | Dependencies required to run the Unit Tests for `sanic` | `pip3 install -e '.[test]'` |
| extras_require['dev']           | Additional Development requirements to add contributing | `pip3 install -e '.[dev]'`  |
| extras_require['docs']          | Dependencies required to enable building and enhancing sanic documentation | `pip3 install -e '.[docs]'` |

## Running all tests

To run the tests for Sanic it is recommended to use tox like so:

```sh
tox
```

See it's that simple!

`tox.ini` contains different environments. Running `tox` without any arguments will
run all unittests, perform lint and other checks.

## Run unittests

`tox` environment -> `[testenv]`

To execute only unittests, run `tox` with environment like so:

```sh

tox -e py37 -v -- tests/test_config.py
# or
tox -e py310 -v -- tests/test_config.py
```

## Run lint checks

`tox` environment -> `[testenv:lint]`

Permform `flake8`\ , `black` and `isort` checks.


```sh
tox -e lint
```

## Run type annotation checks

`tox` environment -> `[testenv:type-checking]`

Permform `mypy` checks.

```sh
tox -e type-checking
```

## Run other checks

`tox` environment -> `[testenv:check]`

Perform other checks.

```sh
tox -e check
```

## Run Static Analysis

`tox` environment -> `[testenv:security]`

Perform static analysis security scan

```sh
tox -e security
```

## Run Documentation sanity check

`tox` environment -> `[testenv:docs]`

Perform sanity check on documentation

```sh
tox -e docs
```
## Code Style

To maintain the code consistency, Sanic uses the following tools:

1. [isort](https://github.com/timothycrosley/isort)
2. [black](https://github.com/python/black)
3. [flake8](https://github.com/PyCQA/flake8)
4. [slotscheck](https://github.com/ariebovenberg/slotscheck)

### isort

`isort` sorts Python imports. It divides imports into three categories sorted each in alphabetical order:

1. built-in
2. third-party
3. project-specific

### black

`black` is a Python code formatter.

### flake8

`flake8` is a Python style guide that wraps the following tools into one:

1. PyFlakes
2. pycodestyle
3. Ned Batchelder's McCabe script

### slotscheck

`slotscheck` ensures that there are no problems with `__slots__` (e.g., overlaps, or missing slots in base classes).

`isort`, `black`, `flake8`, and `slotscheck` checks are performed during `tox` lint checks.

The **easiest** way to make your code conform is to run the following before committing:

```bash
make pretty
```

Refer to [tox documentation](https://tox.readthedocs.io/en/latest/index.html) for more details.

## Pull requests

So the pull request approval rules are pretty simple:

1. All pull requests must pass unit tests.
2. All pull requests must be reviewed and approved by at least one current member of the Core Developer team.
3. All pull requests must pass flake8 checks.
4. All pull requests must match `isort` and `black` requirements.
5. All pull requests must be **PROPERLY** type annotated, unless exemption is given.
6. All pull requests must be consistent with the existing code.
7. If you decide to remove/change anything from any common interface a deprecation message should accompany it in accordance with our [deprecation policy](https://sanicframework.org/en/guide/project/policies.html#deprecation).
8. If you implement a new feature you should have at least one unit test to accompany it.
9. An example must be one of the following:
    * Example of how to use Sanic
    * Example of how to use Sanic extensions
    * Example of how to use Sanic and asynchronous library

## Documentation

_Check back. We are reworking our documentation so this will change._
