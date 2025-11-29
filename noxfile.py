"""Nox sessions for testing and development tasks.

This replaces tox.ini with a modern Python-based task runner that uses uv.
Run with: uv run nox [session]
"""

import nox


# Use uv for all sessions
nox.options.default_venv_backend = "uv"

# Stop on first failure when running multiple sessions
nox.options.stop_on_first_error = True

# Default sessions to run (in order) when no session is specified
# Format first for convenience (incl. lint), other checks, then tests, finally docs
nox.options.sessions = ["format", "type_checking", "security", "tests", "docs"]

# Python versions to test against
PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]
PYPY_VERSIONS = ["pypy3.10"]

# Tools run only on the latest Python version
TOOLS_PYTHON = PYTHON_VERSIONS[-1]

# Directories to format/lint
RUFF_TARGETS = ["."]


@nox.session(python=PYTHON_VERSIONS + PYPY_VERSIONS)
def tests(session):
    """Run tests with coverage for each Python version."""
    # If no args provided, default to "tests" directory
    test_args = session.posargs if session.posargs else ["tests"]

    # Run tests with coverage - this will fail if tests fail
    # Skip benchmark tests by default (run them separately with the benchmark session)
    session.run(
        "coverage",
        "run",
        "--source",
        "./sanic",
        "-m",
        "pytest",
        "-m",
        "not benchmark",
        *test_args,
    )
    # Only combine coverage if tests passed
    session.run("coverage", "combine", "--append", success_codes=[0, 1])


@nox.session(python=TOOLS_PYTHON)
def lint(session):
    """Run linting checks with ruff."""
    session.install("--group", "dev")
    session.run("ruff", "check", *RUFF_TARGETS)
    session.run("ruff", "format", "--check", *RUFF_TARGETS)
    session.run("slotscheck", "--verbose", "-m", "sanic")


@nox.session(python=TOOLS_PYTHON)
def format(session):
    """Format code with ruff."""
    session.install("--group", "dev")
    session.run("ruff", "check", "--fix-only", "--unsafe-fixes", *RUFF_TARGETS)
    session.run("ruff", "format", *RUFF_TARGETS)


@nox.session(python=TOOLS_PYTHON)
def type_checking(session):
    """Run type checking with mypy."""
    session.install("--group", "dev")
    session.run("mypy", "sanic")


@nox.session(python=TOOLS_PYTHON)
def security(session):
    """Run security checks with bandit."""
    session.install("--group", "dev")
    session.run("bandit", "--recursive", "sanic", "--skip", "B404,B101")


@nox.session(python=TOOLS_PYTHON)
def docs(session):
    """Build HTML documentation."""
    session.install("--group", "docs")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build/html")
    session.log("Documentation built in docs/_build/html/")


@nox.session(python=TOOLS_PYTHON)
def docs_lint(session):
    """Check documentation for syntax errors (dry run without output)."""
    session.install("--group", "docs")
    session.run("sphinx-build", "-b", "dummy", "docs", "docs/_build/dummy")
    session.log("Documentation syntax check passed")


@nox.session(python=TOOLS_PYTHON)
def docs_clean(session):
    """Clean documentation build artifacts."""
    import shutil

    from pathlib import Path

    build_dir = Path("docs/_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
        session.log("Cleaned docs/_build/")
    else:
        session.log("docs/_build/ does not exist, nothing to clean")


@nox.session(python=TOOLS_PYTHON)
def docs_serve(session):
    """Serve documentation with live reload."""
    session.install(".")
    session.install("--group", "docs")
    session.run(
        "sphinx-autobuild",
        "docs",
        "docs/_build/html",
        "--port",
        "9999",
        "--watch",
        "./",
    )


@nox.session(python=TOOLS_PYTHON)
def docs_linkcheck(session):
    """Check external links in documentation."""
    session.install(".")
    session.install("--group", "docs")
    session.run(
        "sphinx-build", "-b", "linkcheck", "docs", "docs/_build/linkcheck"
    )
    session.log(
        "Link check complete; check docs/_build/linkcheck/output.txt for results"
    )


@nox.session(python=TOOLS_PYTHON)
def docs_doctest(session):
    """Run doctests in documentation."""
    session.install(".")
    session.install("--group", "docs")
    session.run("sphinx-build", "-b", "doctest", "docs", "docs/_build/doctest")
    session.log(
        "Doctest complete; check docs/_build/doctest/output.txt for results"
    )


@nox.session(python=TOOLS_PYTHON)
def coverage_report(session):
    """Generate coverage reports from previously collected data."""
    # Generate reports from combined coverage data
    session.run("coverage", "report", "-m", "-i")
    session.run("coverage", "html", "-i")
    session.log("Coverage report generated in htmlcov/")


@nox.session(python=TOOLS_PYTHON)
def coverage_xml(session):
    """Generate coverage XML report for CI from previously collected data."""
    # Generate XML report from combined coverage data
    session.run("coverage", "xml", "-i")
    session.log("Coverage XML report generated: coverage.xml")


@nox.session(python=TOOLS_PYTHON)
def build(session):
    """Build distribution packages."""
    session.run("python", "-m", "build")


@nox.session(python=TOOLS_PYTHON)
def clean(session):
    """Clean build artifacts and caches."""
    import shutil

    from pathlib import Path

    patterns = [
        "**/*.pyc",
        "**/*.pyo",
        "**/__pycache__",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".nox",
    ]

    for pattern in patterns:
        if pattern.startswith("**"):
            for path in Path(".").glob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
        else:
            for path in Path(".").glob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)

    session.log("Cleaned build artifacts and caches")


@nox.session(python=TOOLS_PYTHON, name="test-quick")
def test_quick(session):
    """Run tests quickly on the latest Python version only (for rapid development)."""
    # If no args provided, default to "tests" directory
    test_args = session.posargs if session.posargs else ["tests"]

    session.run("pytest", "-m", "not benchmark", *test_args)


@nox.session(python=TOOLS_PYTHON)
def benchmark(session):
    """Run benchmark tests using standalone script."""
    session.run("python", "scripts/benchmark.py")
    session.log("Benchmark tests completed successfully")


@nox.session(python=TOOLS_PYTHON)
def changelog(session):
    """Generate changelog for Sanic to prepare for new release."""
    session.run("python", "scripts/changelog.py")


@nox.session(python=TOOLS_PYTHON)
def release(session):
    """Prepare Sanic for a new release by version bump and changelog."""
    # Check if version argument is provided via posargs
    if session.posargs and len(session.posargs) > 0:
        session.run(
            "python",
            "scripts/release.py",
            "--release-version",
            session.posargs[0],
            "--generate-changelog",
        )
    else:
        session.run("python", "scripts/release.py", "--generate-changelog")


@nox.session(python=TOOLS_PYTHON)
def guide_serve(session):
    """Serve the user guide with live reload."""
    session.run(
        "sanic",
        "server:app",
        "-r",
        "-R",
        "./guide/content",
        "-R",
        "./guide/style",
        external=True,
        env={"SANIC_WORKING_DIR": "guide"},
    )


@nox.session(python=False)
def docker_test(session):
    """Run Sanic unit tests using Docker."""
    session.run(
        "docker",
        "build",
        "-t",
        "sanic/test-image",
        "-f",
        "docker/Dockerfile",
        ".",
        external=True,
    )
    session.run(
        "docker",
        "run",
        "-t",
        "sanic/test-image",
        "uv",
        "run",
        "nox",
        external=True,
    )


@nox.session(python=TOOLS_PYTHON)
def view_coverage(session):
    """View coverage report using sanic."""
    session.run("sanic", "./coverage", "--simple", external=True)
