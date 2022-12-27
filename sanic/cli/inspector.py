from argparse import ArgumentParser

from sanic.application.logo import get_logo
from sanic.cli.base import SanicHelpFormatter, SanicSubParsersAction


def _add_shared(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        "-H",
        default="localhost",
        help="Inspector host address [default 127.0.0.1]",
    )
    parser.add_argument(
        "--port",
        "-p",
        default=6457,
        type=int,
        help="Inspector port [default 6457]",
    )
    parser.add_argument(
        "--secure",
        "-s",
        action="store_true",
        help="Whether to access the Inspector via TLS encryption",
    )
    parser.add_argument("--api-key", "-k", help="Inspector authentication key")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Whether to output the raw response information",
    )


class InspectorSubParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_shared(self)
        if not self.description:
            self.description = ""
        self.description = get_logo(True) + self.description


def make_inspector_parser(parser: ArgumentParser) -> None:
    _add_shared(parser)
    subparsers = parser.add_subparsers(
        action=SanicSubParsersAction,
        dest="action",
        description=(
            "Run one or none of the below subcommands. Using inspect without "
            "a subcommand will fetch general information about the state "
            "of the application instance.\n\n"
            "Or, you can optionally follow inspect with a subcommand. "
            "If you have created a custom "
            "Inspector instance, then you can run custom commands. See "
            "https://sanic.dev/en/guide/deployment/inspector.html "
            "for more details."
        ),
        title="  Subcommands",
        parser_class=InspectorSubParser,
    )
    reloader = subparsers.add_parser(
        "reload",
        help="Trigger a reload of the server workers",
        formatter_class=SanicHelpFormatter,
    )
    reloader.add_argument(
        "--zero-downtime",
        action="store_true",
        help=(
            "Whether to wait for the new process to be online before "
            "terminating the old"
        ),
    )
    subparsers.add_parser(
        "shutdown",
        help="Shutdown the application and all processes",
        formatter_class=SanicHelpFormatter,
    )
    scale = subparsers.add_parser(
        "scale",
        help="Scale the number of workers",
        formatter_class=SanicHelpFormatter,
    )
    scale.add_argument(
        "replicas",
        type=int,
        help="Number of workers requested",
    )

    custom = subparsers.add_parser(
        "<custom>",
        help="Run a custom command",
        description=(
            "keyword arguments:\n  When running a custom command, you can "
            "add keyword arguments by appending them to your command\n\n"
            "\tsanic inspect foo --one=1 --two=2"
        ),
        formatter_class=SanicHelpFormatter,
    )
    custom.add_argument(
        "positional",
        nargs="*",
        help="Add one or more non-keyword args to your custom command",
    )
