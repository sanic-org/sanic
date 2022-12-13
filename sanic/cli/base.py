from argparse import (
    Action,
    ArgumentParser,
    RawTextHelpFormatter,
    _SubParsersAction,
)
from typing import Any


class SanicArgumentParser(ArgumentParser):
    def _check_value(self, action: Action, value: Any) -> None:
        if isinstance(action, SanicSubParsersAction):
            return
        super()._check_value(action, value)


class SanicHelpFormatter(RawTextHelpFormatter):
    ...


class SanicSubParsersAction(_SubParsersAction):
    def __call__(self, parser, namespace, values, option_string=None):
        self._name_parser_map
        parser_name = values[0]
        if parser_name not in self._name_parser_map:
            self._name_parser_map[parser_name] = parser
            values = ["<custom>", *values]

        super().__call__(parser, namespace, values, option_string)
