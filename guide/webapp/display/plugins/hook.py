from mistune.core import BlockState
from mistune.directives import DirectivePlugin, RSTDirective
from mistune.markdown import Markdown


class Hook(DirectivePlugin):
    def __call__(  # type: ignore
        self, directive: RSTDirective, md: Markdown
    ) -> None:
        if md.renderer.NAME == "html":
            md.before_render_hooks.append(self._hook)

    def _hook(self, md: Markdown, state: BlockState) -> None:
        prev = None
        for idx, token in enumerate(state.tokens):
            for type_ in ("column", "tab"):
                if token["type"] == type_:
                    maybe_next = (
                        state.tokens[idx + 1]
                        if idx + 1 < len(state.tokens)
                        else None
                    )
                    token.setdefault("attrs", {})
                    if prev and prev["type"] != type_:
                        token["attrs"]["first"] = True
                    if (
                        maybe_next and maybe_next["type"] != type_
                    ) or not maybe_next:
                        token["attrs"]["last"] = True

            prev = token
