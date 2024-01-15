from html import unescape
from re import Match
from textwrap import dedent
from typing import Any

from html5tagger import HTML, E
from mistune import HTMLRenderer
from mistune.block_parser import BlockParser
from mistune.core import BlockState
from mistune.directives import DirectivePlugin, RSTDirective
from mistune.markdown import Markdown


class Mermaid(DirectivePlugin):
    def parse(
        self, block: BlockParser, m: Match, state: BlockState
    ) -> dict[str, Any]:
        info = m.groupdict()

        new_state = block.state_cls()
        new_state.process(dedent(info["text"]))
        block.parse(new_state)

        text = HTML(info["text"].strip())

        return {
            "type": "mermaid",
            "text": text,
            "children": [{"type": "text", "text": text}],
            "attrs": {},
        }

    def __call__(self, directive: RSTDirective, md: Markdown) -> None:  # type: ignore
        directive.register("mermaid", self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("mermaid", self._render_mermaid)

    def _render_mermaid(self, renderer: HTMLRenderer, text: str, **attrs):
        return str(E.div(class_="mermaid")(HTML(unescape(text))))
