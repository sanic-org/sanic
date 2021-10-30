import sys

from textwrap import indent
from typing import Dict

from sanic import __version__
from sanic.log import logger


class MOTD:
    def __init__(self, logo: str, data: Dict[str, str]) -> None:
        self.logo = logo
        self.data = data
        self.key_width = 0
        self.value_width = 0
        self.set_widths()

    def display(self):
        display = (
            self._display_tty if sys.stdout.isatty() else self._display_basic
        )
        display()

    def _display_basic(self):
        ...

    def _display_tty(self):
        logo_lines = self.logo.split("\n")
        logo_line_length = 24
        version = f"Sanic v{__version__}".center(
            self.key_width + self.value_width + 2 + logo_line_length
        )
        length = len(version) + 2 - logo_line_length
        first_filler = "─" * (logo_line_length - 1)
        second_filler = "─" * (length)
        lines = [
            f"\n┌{first_filler}─{second_filler}┐",
            f"│ {version} │",
            f"├{first_filler}┬{second_filler}┤",
        ]

        for idx, (key, value) in enumerate(self.data.items()):
            key = key.rjust(self.key_width)
            value = value.ljust(self.value_width)
            try:
                logo_part = logo_lines[idx]
            except IndexError:
                logo_part = "                     "
            lines.append(f"│ {logo_part} │ {key}: {value} │")

        lines.append(f"└{first_filler}┴{second_filler}┘\n")

        logger.info(indent("\n".join(lines), "  "))

    def set_widths(self):
        self.key_width = max(map(len, self.data.keys()))
        self.value_width = max(map(len, self.data.values()))
