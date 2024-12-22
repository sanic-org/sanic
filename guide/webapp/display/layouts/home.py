from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from html5tagger import Builder, E

from sanic import Request
from webapp.display.layouts.elements.footer import do_footer

from .base import BaseLayout


class HomeLayout(BaseLayout):
    @contextmanager
    def layout(
        self, request: Request, full: bool = True
    ) -> Generator[None, None, None]:
        self._sponsors()
        self._hero(request.ctx.language)
        with self.builder.div(class_="home container"):
            yield
        self._footer(request)

    def _hero(self, language: str) -> None:
        with self.builder.section(class_="hero is-large has-text-centered"):
            self.builder.div(
                E.h1(E.span("Sanic"), class_="title"),
                E.h2(class_="subtitle")("Build fast. Run fast."),
                E.h3(class_="tagline")("Accelerate your web app development"),
                self._do_buttons(language),
                class_="hero-body",
            )

    def _do_buttons(self, language: str) -> Builder:
        builder = E.div(class_="buttons is-centered")
        with builder:
            builder.a(
                "Get Started",
                class_="button is-primary",
                href=f"/{language}/guide/getting-started.html",
            )
            builder.a(
                "Help",
                class_="button is-outlined",
                href=f"/{language}/help.html",
            )
            builder.a(
                "GitHub",
                class_="button is-outlined",
                href="https://github.com/sanic-org/sanic",
                target="_blank",
            )
        return builder

    def _sponsors(self) -> None:
        with self.builder.section(class_="sponsors"):
            self.builder(
                "Secure, auto-document, and monetize "
                "your Sanic API with Zuplo",
                E.a(
                    "Start free",
                    href="https://zuplo.com",
                    target="_blank",
                    class_="button is-primary is-small",
                ),
            )

    def _footer(self, request: Request) -> None:
        do_footer(
            self.builder,
            request,
            extra_classes="mb-0 mt-6",
            with_pagination=False,
        )
