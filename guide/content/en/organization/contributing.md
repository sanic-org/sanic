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
# Install all development dependencies
uv sync --dev

# Or install development and documentation dependencies
uv sync --group dev --group docs
```

Activate the virtual environment (`.venv/bin/activate`) to run commands directly without `uv run`.

## Dependency Management

Dependencies are managed in `pyproject.toml`:

- **`[project.dependencies]`** - Core runtime dependencies required by Sanic
- **`[project.optional-dependencies]`** - Installable extras `sanic[ext]` and `sanic[http3]`
- **`[dependency-groups]`** - Development-only dependencies (testing, linting, docs)
  - `dev` - All testing and development tools
  - `docs` - Documentation building tools

When using `uv run` or nox sessions, dependencies are automatically installed as needed.

## Running all checks

To run development actions for Sanic, use nox:

```sh
uv run nox
```

By default, this runs the complete CI pipeline:
1. **Format** - Auto-format code with `ruff`
2. **Lint** - Check code style and quality
3. **Type checking** - Run `mypy` type checks
4. **Security** - Run `bandit` security checks
5. **Tests** - Run the full test suite across all supported Python versions
6. **Docs** - Build documentation

This takes a long time to complete. Use `nox -l` to see all available sessions that can be used individually with `nox -s <name>`, including ones not included in the default pipeline.

## Quick development testing

A `test-quick` session is available to only run tests with the most recent Python version, rather than all of them like `test`. Both options can pass additional options to pytest, e.g. to run just a single test module:

```sh
uv run nox -s test-quick -- tests/test_app.py
```

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
