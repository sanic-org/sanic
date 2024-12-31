import shutil

from argparse import ArgumentParser
from asyncio import run
from inspect import signature
from typing import Callable

from sanic import Sanic
from sanic.application.logo import get_logo
from sanic.cli.base import (
    SanicArgumentParser,
    SanicHelpFormatter,
)


def make_executor_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "command",
        help="Command to execute",
    )


class ExecutorSubParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.description:
            self.description = ""
        self.description = get_logo(True) + self.description


class Executor:
    def __init__(self, app: Sanic, kwargs: dict) -> None:
        self.app = app
        self.kwargs = kwargs
        self.commands = self._make_commands()
        self.parser = self._make_parser()

    def run(self, command: str, args: list[str]) -> None:
        if command == "exec":
            args = ["--help"]
        parsed_args = self.parser.parse_args(args)
        if command not in self.commands:
            raise ValueError(f"Unknown command: {command}")
        parsed_kwargs = vars(parsed_args)
        parsed_kwargs.pop("command")
        run(self.commands[command](**parsed_kwargs))

    def _make_commands(self) -> dict[str, Callable]:
        commands = {c.name: c.func for c in self.app._future_commands}
        return commands

    def _make_parser(self) -> SanicArgumentParser:
        width = shutil.get_terminal_size().columns
        parser = SanicArgumentParser(
            prog="sanic",
            description=get_logo(True),
            formatter_class=lambda prog: SanicHelpFormatter(
                prog,
                max_help_position=36 if width > 96 else 24,
                indent_increment=4,
                width=None,
            ),
        )

        subparsers = parser.add_subparsers(
            dest="command",
            title="  Commands",
            parser_class=ExecutorSubParser,
        )
        for command in self.app._future_commands:
            sub = subparsers.add_parser(
                command.name,
                help=command.func.__doc__ or f"Execute {command.name}",
                formatter_class=SanicHelpFormatter,
            )
            self._add_arguments(sub, command.func)

        return parser

    def _add_arguments(self, parser: ArgumentParser, func: Callable) -> None:
        sig = signature(func)
        for param in sig.parameters.values():
            kwargs = {}
            if param.default is not param.empty:
                kwargs["default"] = param.default
            parser.add_argument(
                f"--{param.name}",
                help=param.annotation,
                **kwargs,
            )
