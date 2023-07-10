from mistune import HTMLRenderer, create_markdown, escape
from mistune.directives import RSTDirective, TableOfContents
from mistune.util import safe_entity
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name

from html5tagger import HTML, E

from .code_style import SanicCodeStyle
from .plugins.attrs import Attributes
from .plugins.columns import Column
from .plugins.notification import Notification
from .text import slugify


class DocsRenderer(HTMLRenderer):
    def block_code(self, code: str, info: str | None = None):
        if info:
            lexer = get_lexer_by_name(info, stripall=False)
            formatter = html.HtmlFormatter(
                style=SanicCodeStyle,
                wrapcode=True,
                cssclass=f"highlight language-{info}",
            )
            pre = HTML(highlight(code, lexer, formatter))
        else:
            pre = E.pre(E.code(escape(code)))
        return str(pre)

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
        url = self.safe_url(url).removesuffix(".md")
        if not url.endswith("/"):
            url += ".html"

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

    def list(self, text: str, ordered: bool, **attrs) -> str:
        tag = "ol" if ordered else "ul"
        attrs["class"] = tag
        return self._make_tag(tag, attrs, text)

    def list_item(self, text: str, **attrs) -> str:
        attrs["class"] = "li"
        return self._make_tag("li", attrs, text)

    def table(self, text: str, **attrs) -> str:
        attrs["class"] = "table"
        return self._make_tag("table", attrs, text)

    def _make_tag(
        self, tag: str, attributes: dict[str, str], text: str | None = None
    ) -> str:
        attrs = " ".join(
            f'{key}="{value}"' for key, value in attributes.items()
        )
        if text is None:
            return f"<{tag} {attrs} />"
        return f"<{tag} {attrs}>{text}</{tag}>"


render_markdown = create_markdown(
    renderer=DocsRenderer(),
    plugins=[
        RSTDirective(
            [
                Attributes(),
                Notification(),
                TableOfContents(),
                Column(),
            ]
        ),
        "abbr",
        "def_list",
        "footnotes",
        "mark",
        "table",
    ],
)
