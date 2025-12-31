from __future__ import annotations

from typing import Any


class RequestParameters(dict):
    """Hosts a dict with lists as values where get returns the first value of the list and getlist returns the whole shebang"""  # noqa: E501

    def get(self, name: str, default: Any | None = None) -> Any | None:
        """Return the first value, either the default or actual

        Args:
            name (str): The name of the parameter
            default (Any | None, optional): The default value. Defaults to None.

        Returns:
            Any | None: The first value of the list
        """  # noqa: E501
        return super().get(name, [default])[0]

    def getlist(
        self, name: str, default: list[Any] | None = None
    ) -> list[Any]:
        """Return the entire list

        Args:
            name (str): The name of the parameter
            default (list[Any] | None, optional): The default value. Defaults to None.

        Returns:
            list[Any]: The entire list of values or [] if not found
        """  # noqa: E501
        return super().get(name, default) or []
