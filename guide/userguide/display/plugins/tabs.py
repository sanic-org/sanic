from re import Match
from textwrap import dedent
from typing import Any

from mistune import HTMLRenderer
from mistune.block_parser import BlockParser
from mistune.core import BlockState
from mistune.directives import DirectivePlugin, RSTDirective
from mistune.markdown import Markdown


class Tabs(DirectivePlugin):
    def parse(
        self, block: BlockParser, m: Match, state: BlockState
    ) -> dict[str, Any]:
        info = m.groupdict()

        new_state = block.state_cls()
        new_state.process(dedent(info["text"]))
        block.parse(new_state)

        return {
            "type": "tab",
            "text": info["text"],
            "children": new_state.tokens,
            "attrs": {
                "title": info["title"],
            },
        }

    def __call__(  # type: ignore
        self,
        directive: RSTDirective,
        md: Markdown,
    ) -> None:
        directive.register("tab", self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("tab", self._render_tab)

    def _render_tab(self, renderer: HTMLRenderer, text: str, **attrs):
        start = '<div class="tabs mt-6"><ul>\n' if attrs.get("first") else ""
        end = (
            '</ul></div><div class="tab-display"></div>\n'
            if attrs.get("last")
            else ""
        )
        content = f'<div class="tab-content">{text}</div>\n'
        tab = f'<li><a>{attrs["title"]}</a>{content}</li>\n'
        return start + tab + end
