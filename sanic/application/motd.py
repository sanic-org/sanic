from abc import ABC, abstractmethod
from textwrap import indent
from typing import Dict

from sanic import __version__
from sanic.log import logger


class MOTD(ABC):
    def __init__(
        self,
        logo: str,
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
        ...


class MOTDBasic(MOTD):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def display(self):
        lines = [
            f"Sanic v{__version__}",
            f"Goin' Fast @ {self.serve_location}",
            *(f"{key}: {value}" for key, value in self.data.items()),
            *(f"{key}: {value}" for key, value in self.extra.items()),
        ]
        for line in lines:
            logger.debug(line)


class MOTDTTY(MOTD):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_variables()

    def set_variables(self):
        self.key_width = max(map(len, self.data.keys()))
        self.value_width = max(map(len, self.data.values()))
        self.logo_lines = self.logo.split("\n")
        self.logo_line_length = 24
        self.centering_length = (
            self.key_width + self.value_width + 2 + self.logo_line_length
        )
        self.display_length = self.key_width + self.value_width + 2

    def display(self):
        version = f"Sanic v{__version__}".center(self.centering_length)
        running = f"Goin' Fast @ {self.serve_location}".center(
            self.centering_length
        )
        length = len(version) + 2 - self.logo_line_length
        first_filler = "─" * (self.logo_line_length - 1)
        second_filler = "─" * length
        display_filler = "─" * (self.display_length + 2)
        lines = [
            f"\n┌{first_filler}─{second_filler}┐",
            f"│ {version} │",
            f"│ {running} │",
            f"├{first_filler}┬{second_filler}┤",
        ]

        self._render_data(lines, self.data, 0)
        if self.extra:
            logo_part = self._get_logo_part(len(lines) - 4)
            lines.append(f"| {logo_part} ├{display_filler}┤")
            self._render_data(lines, self.extra, len(lines) - 4)

        self._render_fill(lines)

        lines.append(f"└{first_filler}┴{second_filler}┘\n")
        logger.info(indent("\n".join(lines), "  "))

    def _render_data(self, lines, data, start):
        for idx, (key, value) in enumerate(data.items(), start=start):
            key = key.rjust(self.key_width)
            value = value.ljust(self.value_width)
            logo_part = self._get_logo_part(idx)
            lines.append(f"│ {logo_part} │ {key}: {value} │")

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
