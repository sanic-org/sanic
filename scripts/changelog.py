#!/usr/bin/env python

from os import path
import sys

if __name__ == "__main__":
    try:
        import towncrier
        import click
    except ImportError:
        print(
            "Please make sure you have a installed towncrier and click before using this tool"
        )
        sys.exit(1)

    @click.command()
    @click.option(
        "--draft",
        "draft",
        default=False,
        flag_value=True,
        help="Render the news fragments, don't write to files, "
        "don't check versions.",
    )
    @click.option(
        "--dir", "directory", default=path.dirname(path.abspath(__file__))
    )
    @click.option("--name", "project_name", default=None)
    @click.option(
        "--version",
        "project_version",
        default=None,
        help="Render the news fragments using given version.",
    )
    @click.option("--date", "project_date", default=None)
    @click.option(
        "--yes",
        "answer_yes",
        default=False,
        flag_value=True,
        help="Do not ask for confirmation to remove news fragments.",
    )
    def _main(
        draft,
        directory,
        project_name,
        project_version,
        project_date,
        answer_yes,
    ):
        return towncrier.__main(
            draft,
            directory,
            project_name,
            project_version,
            project_date,
            answer_yes,
        )

    _main()
