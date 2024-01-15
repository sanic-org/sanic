from abc import ABC, abstractmethod
from shutil import get_terminal_size
from textwrap import indent, wrap
from typing import Dict, Optional

from sanic import __version__
from sanic.helpers import is_atty
from sanic.log import logger


class MOTD(ABC):
    """Base class for the Message of the Day (MOTD) display."""

    def __init__(
        self,
        logo: Optional[str],
        serve_location: str,
        data: Dict[str, str],
        extra: Dict[str, str],
    ) -> None:
        self.logo = logo
        self.serve_location = serve_location
        self.data = data
        self.extra = extra
        self.key_width = 0
        self.value_width = 0

    @abstractmethod
    def display(self):
        """Display the MOTD."""

    @classmethod
    def output(
        cls,
        logo: Optional[str],
        serve_location: str,
        data: Dict[str, str],
        extra: Dict[str, str],
    ) -> None:
        """Output the MOTD.

        Args:
            logo (Optional[str]): Logo to display.
            serve_location (str): Location to serve.
            data (Dict[str, str]): Data to display.
            extra (Dict[str, str]): Extra data to display.
        """
        motd_class = MOTDTTY if is_atty() else MOTDBasic
        motd_class(logo, serve_location, data, extra).display()


class MOTDBasic(MOTD):
    """A basic MOTD display.

    This is used when the terminal does not support ANSI escape codes.
    """

    def display(self):
        if self.logo:
            logger.debug(self.logo)
        lines = [f"Sanic v{__version__}"]
        if self.serve_location:
            lines.append(f"Goin' Fast @ {self.serve_location}")
        lines += [
            *(f"{key}: {value}" for key, value in self.data.items()),
            *(f"{key}: {value}" for key, value in self.extra.items()),
        ]
        for line in lines:
            logger.info(line)


class MOTDTTY(MOTD):
    """A MOTD display for terminals that support ANSI escape codes."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_variables()

    def set_variables(self):  # no  cov
        """Set the variables used for display."""
        fallback = (108, 24)
        terminal_width = max(
            get_terminal_size(fallback=fallback).columns, fallback[0]
        )
        self.max_value_width = terminal_width - fallback[0] + 36

        self.key_width = 4
        self.value_width = self.max_value_width
        if self.data:
            self.key_width = max(map(len, self.data.keys()))
            self.value_width = min(
                max(map(len, self.data.values())), self.max_value_width
            )
        if self.extra:
            self.key_width = max(
                self.key_width, max(map(len, self.extra.keys()))
            )
            self.value_width = min(
                max((*map(len, self.extra.values()), self.value_width)),
                self.max_value_width,
            )
        self.logo_lines = self.logo.split("\n") if self.logo else []
        self.logo_line_length = 24
        self.centering_length = (
            self.key_width + self.value_width + 2 + self.logo_line_length
        )
        self.display_length = self.key_width + self.value_width + 2

    def display(self, version=True, action="Goin' Fast", out=None):
        """Display the MOTD.

        Args:
            version (bool, optional): Display the version. Defaults to `True`.
            action (str, optional): Action to display. Defaults to
                `"Goin' Fast"`.
            out (Optional[Callable], optional): Output function. Defaults to
                `None`.
        """
        if not out:
            out = logger.info
        header = "Sanic"
        if version:
            header += f" v{__version__}"
        header = header.center(self.centering_length)
        running = (
            f"{action} @ {self.serve_location}" if self.serve_location else ""
        ).center(self.centering_length)
        length = len(header) + 2 - self.logo_line_length
        first_filler = "─" * (self.logo_line_length - 1)
        second_filler = "─" * length
        display_filler = "─" * (self.display_length + 2)
        lines = [
            f"\n┌{first_filler}─{second_filler}┐",
            f"│ {header} │",
            f"│ {running} │",
            f"├{first_filler}┬{second_filler}┤",
        ]

        self._render_data(lines, self.data, 0)
        if self.extra:
            logo_part = self._get_logo_part(len(lines) - 4)
            lines.append(f"│ {logo_part} ├{display_filler}┤")
            self._render_data(lines, self.extra, len(lines) - 4)

        self._render_fill(lines)

        lines.append(f"└{first_filler}┴{second_filler}┘\n")
        out(indent("\n".join(lines), "  "))

    def _render_data(self, lines, data, start):
        offset = 0
        for idx, (key, value) in enumerate(data.items(), start=start):
            key = key.rjust(self.key_width)

            wrapped = wrap(value, self.max_value_width, break_on_hyphens=False)
            for wrap_index, part in enumerate(wrapped):
                part = part.ljust(self.value_width)
                logo_part = self._get_logo_part(idx + offset + wrap_index)
                display = (
                    f"{key}: {part}"
                    if wrap_index == 0
                    else (" " * len(key) + f"  {part}")
                )
                lines.append(f"│ {logo_part} │ {display} │")
                if wrap_index:
                    offset += 1

    def _render_fill(self, lines):
        filler = " " * self.display_length
        idx = len(lines) - 5
        for i in range(1, len(self.logo_lines) - idx):
            logo_part = self.logo_lines[idx + i]
            lines.append(f"│ {logo_part} │ {filler} │")

    def _get_logo_part(self, idx):
        try:
            logo_part = self.logo_lines[idx]
        except IndexError:
            logo_part = " " * (self.logo_line_length - 3)
        return logo_part
