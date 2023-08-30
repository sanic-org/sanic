from __future__ import annotations

# from dataclasses import dataclass, field
from msgspec import Struct, field


# @dataclass
class MenuItem(Struct, kw_only=False, omit_defaults=True):
    label: str
    path: str | None = None
    href: str | None = None
    items: list[MenuItem] = field(default_factory=list)
