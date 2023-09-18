import re

from mistune.markdown import Markdown

DIRECTIVE_PATTERN = r":(?:class|func|meth|attr|exc|mod|data|const|obj|keyword|option|cmdoption|envvar):`(?P<ref>sanic\.[^`]+)`"  # noqa: E501

def _parse_inline_directive(inline, m: re.Match, state):
    state.append_token(
        {
            "type": "inline_directive",
            "attrs": {},
            "raw": m.group("ref"),
        }
    )
    return m.end()

def inline_directive(md: Markdown):
    md.inline.register("inline_directive", DIRECTIVE_PATTERN, _parse_inline_directive, before="escape",)
