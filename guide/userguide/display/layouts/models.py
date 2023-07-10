from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MenuItem:
    label: str
    path: str | None = None
    href: str | None = None
    items: list[MenuItem] = field(default_factory=list)
