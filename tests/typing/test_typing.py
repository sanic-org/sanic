# flake8: noqa: E501

import subprocess
import sys

from pathlib import Path
from typing import List, Tuple

import pytest


CURRENT_DIR = Path(__file__).parent


def run_check(path_location: str) -> str:
    """Use mypy to check the given path location and return the output."""

    mypy_path = "mypy"
    path = CURRENT_DIR / path_location
    command = [mypy_path, path.resolve().as_posix()]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    output = process.stdout + process.stderr
    return output


@pytest.mark.parametrize(
    "path_location,expected",
    (
        (
            "app_default.py",
            [
                (
                    "sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]",
                    5,
                )
            ],
        ),
        (
            "app_custom_config.py",
            [
                (
                    "sanic.app.Sanic[app_custom_config.CustomConfig, types.SimpleNamespace]",
                    10,
                )
            ],
        ),
        (
            "app_custom_ctx.py",
            [("sanic.app.Sanic[sanic.config.Config, app_custom_ctx.Foo]", 9)],
        ),
        (
            "app_fully_custom.py",
            [
                (
                    "sanic.app.Sanic[app_fully_custom.CustomConfig, app_fully_custom.Foo]",
                    14,
                )
            ],
        ),
        (
            "request_custom_sanic.py",
            [
                ("types.SimpleNamespace", 18),
                (
                    "sanic.app.Sanic[request_custom_sanic.CustomConfig, types.SimpleNamespace]",
                    19,
                ),
            ],
        ),
        (
            "request_custom_ctx.py",
            [
                ("request_custom_ctx.Foo", 16),
                (
                    "sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]",
                    17,
                ),
            ],
        ),
        (
            "request_fully_custom.py",
            [
                ("request_fully_custom.CustomRequest", 32),
                ("request_fully_custom.RequestContext", 33),
                (
                    "sanic.app.Sanic[request_fully_custom.CustomConfig, request_fully_custom.Foo]",
                    34,
                ),
            ],
        ),
    ),
)
def test_check_app_default(
    path_location: str, expected: List[Tuple[str, int]]
) -> None:
    output = run_check(f"samples/{path_location}")

    for text, number in expected:
        current = CURRENT_DIR / f"samples/{path_location}"
        path = current.relative_to(CURRENT_DIR.parent)

        target = Path.cwd()
        while True:
            note = _text_from_path(current, path, target, number, text)
            try:
                assert note in output, output
            except AssertionError:
                target = target.parent
                if not target.exists():
                    raise
            else:
                break


def _text_from_path(
    base: Path, path: Path, target: Path, number: int, text: str
) -> str:
    relative_to_cwd = base.relative_to(target)
    prefix = ".".join(relative_to_cwd.parts[:-1])
    text = text.replace(path.stem, f"{prefix}.{path.stem}")
    return f'{path}:{number}: note: Revealed type is "{text}"'
