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

    def __call__(self, directive: RSTDirective, md: Markdown) -> None:
        directive.register("column", self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("column", self._render_column)
            md.before_render_hooks.append(self._hook)

    def _hook(self, md: Markdown, state: BlockState) -> None:
        prev = None
        for idx, token in enumerate(state.tokens):
            if token["type"] == "column":
                maybe_next = (
                    state.tokens[idx + 1]
                    if idx + 1 < len(state.tokens)
                    else None
                )
                token.setdefault("attrs", {})
                if prev and prev["type"] != "column":
                    token["attrs"]["first"] = True
                if maybe_next and maybe_next["type"] != "column":
                    token["attrs"]["last"] = True

            prev = token

    def _render_column(self, renderer: HTMLRenderer, text: str, **attrs):
        start = '<div class="columns mt-3">\n' if attrs.get("first") else ""
        end = "</div>\n" if attrs.get("last") else ""
        col = f'<div class="column">{text}</div>\n'
        return start + (col) + end
