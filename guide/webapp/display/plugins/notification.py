from mistune.directives import Admonition

from html5tagger import HTML, E


class Notification(Admonition):
    SUPPORTED_NAMES = {
        "success",
        "info",
        "warning",
        "danger",
        "tip",
        "new",
        "note",
    }

    def __call__(self, directive, md):
        for name in self.SUPPORTED_NAMES:
            directive.register(name, self.parse)

        if md.renderer.NAME == "html":
            md.renderer.register("admonition", self._render_admonition)
            md.renderer.register(
                "admonition_title", self._render_admonition_title
            )
            md.renderer.register(
                "admonition_content", self._render_admonition_content
            )

    def _render_admonition(self, _, text, name, **attrs) -> str:
        return str(
            E.div(
                HTML(text),
                class_=f"notification is-{name}",
            )
        )

    def _render_admonition_title(self, _, text) -> str:
        return str(
            E.p(
                text,
                class_="notification-title",
            )
        )

    def _render_admonition_content(self, _, text) -> str:
        return text
