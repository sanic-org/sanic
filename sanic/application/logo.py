import re
import sys

from os import environ

from sanic.compat import is_atty


BASE_LOGO = """

                 Sanic
         Build Fast. Run Fast.

"""
COFFEE_LOGO = """\033[48;2;255;13;104m                     \033[0m
\033[38;2;255;255;255;48;2;255;13;104m     ▄████████▄      \033[0m
\033[38;2;255;255;255;48;2;255;13;104m    ██       ██▀▀▄   \033[0m
\033[38;2;255;255;255;48;2;255;13;104m    ███████████  █   \033[0m
\033[38;2;255;255;255;48;2;255;13;104m    ███████████▄▄▀   \033[0m
\033[38;2;255;255;255;48;2;255;13;104m     ▀███████▀       \033[0m
\033[48;2;255;13;104m                     \033[0m
Dark roast. No sugar."""

COLOR_LOGO = """\033[48;2;255;13;104m                     \033[0m
\033[38;2;255;255;255;48;2;255;13;104m    ▄███ █████ ██    \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ██                \033[0m
\033[38;2;255;255;255;48;2;255;13;104m    ▀███████ ███▄    \033[0m
\033[38;2;255;255;255;48;2;255;13;104m                ██   \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ████ ████████▀    \033[0m
\033[48;2;255;13;104m                     \033[0m
Build Fast. Run Fast."""

FULL_COLOR_LOGO = """

\033[38;2;255;13;104m  ▄███ █████ ██ \033[0m     ▄█▄      ██       █   █   ▄██████████
\033[38;2;255;13;104m ██             \033[0m    █   █     █ ██     █   █  ██
\033[38;2;255;13;104m  ▀███████ ███▄ \033[0m   ▀     █    █   ██   ▄   █  ██
\033[38;2;255;13;104m              ██\033[0m  █████████   █     ██ █   █  ▄▄
\033[38;2;255;13;104m ████ ████████▀ \033[0m █         █  █       ██   █   ▀██ ███████

"""  # noqa

ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def get_logo(full=False, coffee=False):
    logo = (
        (FULL_COLOR_LOGO if full else (COFFEE_LOGO if coffee else COLOR_LOGO))
        if is_atty()
        else BASE_LOGO
    )

    if (
        sys.platform == "darwin"
        and environ.get("TERM_PROGRAM") == "Apple_Terminal"
    ):
        logo = ansi_pattern.sub("", logo)

    return logo