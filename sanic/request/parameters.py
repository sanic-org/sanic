from __future__ import annotations

from typing import Any, Optional


class RequestParameters(dict):
    """Hosts a dict with lists as values where get returns the first value of the list and getlist returns the whole shebang"""  # noqa: E501

    def get(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        """Return the first value, either the default or actual

        Args:
            name (str): The name of the parameter
            default (Optional[Any], optional): The default value. Defaults to None.

        Returns:
            Optional[Any]: The first value of the list
        """  # noqa: E501
        return super().get(name, [default])[0]

    def getlist(
        self, name: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """Return the entire list

        Args:
            name (str): The name of the parameter
            default (Optional[Any], optional): The default value. Defaults to None.

        Returns:
            Optional[Any]: The entire list
        """  # noqa: E501
        return super().get(name, default)
