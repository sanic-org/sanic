from re import Match
from textwrap import dedent
from typing import Any

from mistune import HTMLRenderer
from mistune.block_parser import BlockParser
from mistune.core import BlockState
from mistune.directives import DirectivePlugin, RSTDirective
from mistune.markdown import Markdown


class Column(DirectivePlugin):
    def parse(
        self, block: BlockParser, m: Match, state: BlockState
    ) -> dict[str, Any]:
        info = m.groupdict()

        new_state = block.state_cls()
        new_state.process(dedent(info["text"]))
        block.parse(new_state)

        return {
            "type": "column",
            "text": info["text"],
            "children": new_state.tokens,
            "attrs": {},
        }

    def __call__(  # type: ignore
        self, directive: RSTDirective, md: Markdown
    ) -> None:
        directive.register("column", self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("column", self._render_column)

    def _render_column(self, renderer: HTMLRenderer, text: str, **attrs):
        start = (
            '<div class="columns mt-3 is-multiline">\n'
            if attrs.get("first")
            else ""
        )
        end = "</div>\n" if attrs.get("last") else ""
        col = f'<div class="column is-half">{text}</div>\n'
        return start + (col) + end
