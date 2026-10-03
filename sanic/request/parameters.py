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

    def __getattr__(self, name: str) -> str:
        """Return the first value as ``str``, or ``""`` when missing.

        Mirrors the convenience attribute access already available on
        ``request.cookies`` and ``request.headers``. Trailing underscores
        are stripped so Python keywords (``class_``, ``from_``) can be
        used as attribute names. Underscores inside the name are kept
        as-is because form and query-string keys are typically written in
        ``snake_case``; use ``get``/``__getitem__`` for keys that contain
        characters not valid in a Python identifier.

        File uploads live on ``request.files``, which is a dedicated
        :class:`~sanic.request.form.FileRequestParameters` subclass whose
        own ``__getattr__`` returns the uploaded :class:`File` (or
        ``None`` when missing). This base implementation only ever
        returns ``str`` so form and query-string callers never
        accidentally receive a file object.

        Args:
            name (str): The attribute name to look up as a parameter.

        Returns:
            str: The first value coerced to ``str``, or ``""`` when the
            parameter is not present.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        return str(self.get(name.rstrip("_"), ""))
