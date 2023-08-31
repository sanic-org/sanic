from __future__ import annotations

from msgspec import Struct, field


class MenuItem(Struct, kw_only=False, omit_defaults=True):
    label: str
    path: str | None = None
    href: str | None = None
    items: list[MenuItem] = field(default_factory=list)


class GeneralConfig(Struct, kw_only=False):
    current_version: str
