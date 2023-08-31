import re

from mistune.markdown import Markdown


def parse_inline_span(inline, m: re.Match, state):
    state.append_token(
        {
            "type": "span",
            "attrs": {"classes": m.group("classes")},
            "raw": m.group("content"),
        }
    )
    return m.end()


SPAN_PATTERN = r"{span:(?:(?P<classes>[^\:]+?):)?(?P<content>.*?)}"


def span(md: Markdown) -> None:
    md.inline.register(
        "span",
        SPAN_PATTERN,
        parse_inline_span,
        before="link",
    )
