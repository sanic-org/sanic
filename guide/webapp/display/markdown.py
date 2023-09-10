import re
from textwrap import dedent

from mistune import HTMLRenderer, create_markdown, escape
from mistune.directives import RSTDirective, TableOfContents
from mistune.util import safe_entity
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name

from html5tagger import HTML, Builder, E  # type: ignore

from .code_style import SanicCodeStyle
from .plugins.attrs import Attributes
from .plugins.columns import Column
from .plugins.hook import Hook
from .plugins.mermaid import Mermaid
from .plugins.notification import Notification
from .plugins.span import span
from .plugins.inline_directive import inline_directive
from .plugins.tabs import Tabs
from .text import slugify


class DocsRenderer(HTMLRenderer):
    def block_code(self, code: str, info: str | None = None):
        builder = Builder("Block")
        with builder.div(class_="code-block"):
            if info:
                lexer = get_lexer_by_name(info, stripall=False)
                formatter = html.HtmlFormatter(
                    style=SanicCodeStyle,
                    wrapcode=True,
                    cssclass=f"highlight language-{info}",
                )
                builder(HTML(highlight(code, lexer, formatter)))
                with builder.div(
                    class_="code-block__copy",
                    onclick="copyCode(this)",
                ):
                    builder.div(
                        class_="code-block__rectangle code-block__filled"
                    ).div(class_="code-block__rectangle code-block__outlined")
            else:
                builder.pre(E.code(escape(code)))
        return str(builder)

    def heading(self, text: str, level: int, **attrs) -> str:
        ident = slugify(text)
        if level > 1:
            text += self._make_tag(
                "a", {"href": f"#{ident}", "class": "anchor"}, "#"
            )
        return self._make_tag(
            f"h{level}", {"id": ident, "class": f"is-size-{level}"}, text
        )

    def link(self, text: str, url: str, title: str | None = None) -> str:
        url = self.safe_url(url).replace(".md", ".html")
        url, anchor = url.split("#", 1) if "#" in url else (url, None)
        if not url.endswith("/") and not url.endswith(".html"):
            url += ".html"
        if anchor:
            url += f"#{anchor}"
        attributes: dict[str, str] = {"href": url}
        if title:
            attributes["title"] = safe_entity(title)
        if url.startswith("http"):
            attributes["target"] = "_blank"
            attributes["rel"] = "nofollow noreferrer"
        else:
            attributes["hx-get"] = url
            attributes["hx-target"] = "#content"
            attributes["hx-swap"] = "innerHTML"
            attributes["hx-push-url"] = "true"
        return self._make_tag("a", attributes, text)

    def span(self, text, classes, **attrs) -> str:
        if classes:
            attrs["class"] = classes
        return self._make_tag("span", attrs, text)

    def list(self, text: str, ordered: bool, **attrs) -> str:
        tag = "ol" if ordered else "ul"
        attrs["class"] = tag
        return self._make_tag(tag, attrs, text)

    def list_item(self, text: str, **attrs) -> str:
        attrs["class"] = "li"
        return self._make_tag("li", attrs, text)

    def table(self, text: str, **attrs) -> str:
        attrs["class"] = "table is-fullwidth is-bordered"
        return self._make_tag("table", attrs, text)

    def inline_directive(self, text: str, **attrs) -> str:
        num_dots = text.count(".")
        display = self.codespan(text)

        if num_dots <= 1:
            return display

        module, *_ = text.rsplit(".", num_dots - 1)
        href = f"/api/{module}.html"
        return self._make_tag(
            "a",
            {"href": href, "class": "inline-directive"},
            display,
        )
            

    def _make_tag(
        self, tag: str, attributes: dict[str, str], text: str | None = None
    ) -> str:
        attrs = " ".join(
            f'{key}="{value}"' for key, value in attributes.items()
        )
        if text is None:
            return f"<{tag} {attrs} />"
        return f"<{tag} {attrs}>{text}</{tag}>"


RST_CODE_BLOCK_PATTERN = re.compile(
    r"\.\.\scode-block::\s(\w+)\n\n((?:\n|(?:\s\s\s\s[^\n]*))+)"
)

_render_markdown = create_markdown(
    renderer=DocsRenderer(),
    plugins=[
        RSTDirective(
            [
                # Admonition(),
                Attributes(),
                Notification(),
                TableOfContents(),
                Column(),
                Mermaid(),
                Tabs(),
                Hook(),
            ]
        ),
        "abbr",
        "def_list",
        "footnotes",
        "mark",
        "table",
        span,
        inline_directive,
    ],
)


def render_markdown(text: str) -> str:
    def replacer(match):
        language = match.group(1)
        code_block = dedent(match.group(2)).strip()
        return f"```{language}\n{code_block}\n```\n\n"

    text = RST_CODE_BLOCK_PATTERN.sub(replacer, text)
    return _render_markdown(text)
