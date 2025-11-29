# Contributing

Thank you for your interest! Sanic is always looking for contributors. If you don't feel comfortable contributing code, adding docstrings to the source files, or helping with the [Sanic User Guide](https://github.com/sanic-org/sanic-guide) by providing documentation or implementation examples would be appreciated!

We are committed to providing a friendly, safe and welcoming environment for all, regardless of gender, sexual orientation, disability, ethnicity, religion, or similar personal characteristic. Our [code of conduct](https://github.com/sanic-org/sanic/blob/master/CONDUCT.md) sets the standards for behavior.

## Installation

To develop on Sanic, it is highly recommended to use `uv` which automatically manages virtual environments and dependencies.

After cloning the repo, you don't need a separate install step! Simply use `uv run` to execute commands:

```sh
# Run tests - uv will automatically set up the environment
uv run nox -s test-quick

# Run any script with dependencies automatically installed
uv run pytest tests/test_app.py

# Run sanic itself
uv run sanic path.to.app:app
```

If you prefer to work in an activated virtual environment, you can sync all dependencies:

```sh
uv sync
```

Activate the virtual environment (`.venv/bin/activate`) to run commands directly without `uv run`.

## Dependency Management

All extra dependencies are managed in `pyproject.toml`. When using `uv`, the dev dependencies are automatically installed as needed—you don't need to manually manage them.

## Running all tests

To run the tests for Sanic it is recommended to use nox like so:

```sh
uv run nox
```

This will run all the checks, including the test suite with each supported Python version in separate venvs. It takes a few minutes to complete.

`noxfile.py` contains different sessions. Running `nox` without any arguments will
run all test sessions across all supported Python versions.

## Run unittests

To execute only unittests for a specific Python version, run `nox` with a session like so:

```sh
uv run nox -s tests-3.13
# or for a specific test file
uv run nox -s tests-3.13 -- tests/test_config.py
```

To run tests across all Python versions:

```sh
uv run nox -s tests
```

## Run lint checks

Perform `ruff` checks (linting, formatting, and import sorting) and `slotscheck`.

```sh
uv run nox -s lint
```

## Run type annotation checks

Perform `mypy` checks.

```sh
uv run nox -s type_checking
```

## Format code

Automatically format code with `ruff`.

```sh
uv run nox -s format
```

## Run Static Analysis

Perform static analysis security scan with `bandit`.

```sh
uv run nox -s security
```

## Run Documentation sanity check

Perform sanity check on documentation.

```sh
uv run nox -s docs
```
## Code Style

To maintain the code consistency, Sanic uses the following tools:

1. [ruff](https://github.com/astral-sh/ruff) - for linting, formatting, and import sorting
2. [slotscheck](https://github.com/ariebovenberg/slotscheck) - for `__slots__` validation

### ruff

`ruff` is an extremely fast Python linter and formatter that replaces multiple tools:

- **Linting**: Replaces flake8, pylint, and related plugins
- **Formatting**: Replaces black
- **Import sorting**: Replaces isort

`ruff` provides a unified toolchain for code quality and consistency.

### slotscheck

`slotscheck` ensures that there are no problems with `__slots__` (e.g., overlaps, or missing slots in base classes).

All code style checks are performed during `nox` lint sessions.

The **easiest** way to make your code conform is to run the following before committing:

```bash
uv run nox -s format
```

Refer to [nox documentation](https://nox.thea.codes/) for more details.

## Pull requests

So the pull request approval rules are pretty simple:

1. All pull requests must pass unit tests.
2. All pull requests must be reviewed and approved by at least one current member of the Core Developer team.
3. All pull requests must pass `ruff` checks (linting, formatting, and import sorting).
4. All pull requests must be **PROPERLY** type annotated, unless exemption is given.
5. All pull requests must be consistent with the existing code.
6. If you decide to remove/change anything from any common interface a deprecation message should accompany it in accordance with our [deprecation policy](https://sanicframework.org/en/guide/project/policies.html#deprecation).
7. If you implement a new feature you should have at least one unit test to accompany it.
8. An example must be one of the following:
    * Example of how to use Sanic
    * Example of how to use Sanic extensions
    * Example of how to use Sanic and asynchronous library

## Documentation

_Check back. We are reworking our documentation so this will change._
