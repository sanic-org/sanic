from __future__ import annotations

from typing import Any, Optional


class RequestParameters(dict):
    """
    Hosts a dict with lists as values where get returns the first
    value of the list and getlist returns the whole shebang
    """

    def get(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        """Return the first value, either the default or actual"""
        return super().get(name, [default])[0]

    def getlist(
        self, name: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Return the entire list
        """
        return super().get(name, default)
