from re import Match
from textwrap import dedent
from typing import Any

from mistune.block_parser import BlockParser
from mistune.core import BlockState
from mistune.directives import DirectivePlugin

from html5tagger import HTML, E


class Attributes(DirectivePlugin):
    def __call__(self, directive, md):
        directive.register("attrs", self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("attrs", self._render)

    def parse(
        self, block: BlockParser, m: Match, state: BlockState
    ) -> dict[str, Any]:
        info = m.groupdict()
        options = dict(self.parse_options(m))
        new_state = block.state_cls()
        new_state.process(dedent(info["text"]))
        block.parse(new_state)
        options.setdefault("class_", "additional-attributes")
        classes = options.pop("class", "")
        if classes:
            options["class_"] += f" {classes}"

        return {
            "type": "attrs",
            "text": info["text"],
            "children": new_state.tokens,
            "attrs": options,
        }

    def _render(self, _, text: str, **attrs) -> str:
        return str(E.div(HTML(text), **attrs))
