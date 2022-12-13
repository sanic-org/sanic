from argparse import ArgumentParser

from sanic.cli.base import SanicHelpFormatter, SanicSubParsersAction


def make_inspector_parser(parser: ArgumentParser) -> None:
    parser.add_argument("--host", "-H", default="localhost")
    parser.add_argument("--port", "-p", default=6457, type=int)
    parser.add_argument("--secure", "-s", action="store_true")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Whether to output the raw response information",
    )

    subparsers = parser.add_subparsers(
        action=SanicSubParsersAction,
        dest="action",
        description=(
            "Run one of the below subcommands. If you have created a custom "
            "Inspector instance, then you can run custom commands.\nSee ___ "
            "for more details."
        ),
        title="Subcommands",
    )
    subparsers.add_parser(
        "reload", help="Trigger a reload of the server workers"
    )
    subparsers.add_parser(
        "shutdown", help="Shutdown the application and all processes"
    )
    scale = subparsers.add_parser("scale", help="Scale the number of workers")
    scale.add_argument("replicas", type=int)

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
        "positional", nargs="*", help="Add one or more non-keyword args"
    )
