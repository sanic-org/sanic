import re

from typing import Any, Dict, List, Optional

from sanic.cookies.response import Cookie
from sanic.log import deprecation
from sanic.request.parameters import RequestParameters


COOKIE_NAME_RESERVED_CHARS = re.compile(
    '[\x00-\x1F\x7F-\xFF()<>@,;:\\\\"/[\\]?={} \x09]'
)
OCTAL_PATTERN = re.compile(r"\\[0-3][0-7][0-7]")
QUOTE_PATTERN = re.compile(r"[\\].")


def _unquote(str):  # no cov
    if str is None or len(str) < 2:
        return str
    if str[0] != '"' or str[-1] != '"':
        return str

    str = str[1:-1]

    i = 0
    n = len(str)
    res = []
    while 0 <= i < n:
        o_match = OCTAL_PATTERN.search(str, i)
        q_match = QUOTE_PATTERN.search(str, i)
        if not o_match and not q_match:
            res.append(str[i:])
            break
        # else:
        j = k = -1
        if o_match:
            j = o_match.start(0)
        if q_match:
            k = q_match.start(0)
        if q_match and (not o_match or k < j):
            res.append(str[i:k])
            res.append(str[k + 1])
            i = k + 2
        else:
            res.append(str[i:j])
            res.append(chr(int(str[j + 1 : j + 4], 8)))  # noqa: E203
            i = j + 4
    return "".join(res)


def parse_cookie(raw: str):
    cookies: Dict[str, List] = {}

    for token in raw.split(";"):
        name, __, value = token.partition("=")
        name = name.strip()
        value = value.strip()

        if not name:
            continue

        if COOKIE_NAME_RESERVED_CHARS.search(name):  # no cov
            continue

        if len(value) > 2 and value[0] == '"' and value[-1] == '"':  # no cov
            value = _unquote(value)

        if name in cookies:
            cookies[name].append(value)
        else:
            cookies[name] = [value]

    return cookies


class CookieRequestParameters(RequestParameters):
    def __getitem__(self, key: str) -> Optional[str]:
        deprecation(
            f"You are accessing cookie key '{key}', which is currently in "
            "compat mode returning a single cookie value. Starting in v24.3 "
            "accessing a cookie value like this will return a list of values. "
            "To avoid this behavior and continue accessing a single value, "
            f"please upgrade from request.cookies['{key}'] to "
            f"request.cookies.get('{key}'). See more details: "
            "https://sanic.dev/en/guide/release-notes/v23.3.html#request-cookies",  # noqa
            24.3,
        )
        try:
            value = self._get_prefixed_cookie(key)
        except KeyError:
            value = super().__getitem__(key)
        return value[0]

    def __getattr__(self, key: str) -> str:
        if key.startswith("_"):
            return self.__getattribute__(key)
        key = key.rstrip("_").replace("_", "-")
        return str(self.get(key, ""))

    def get(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        try:
            return self._get_prefixed_cookie(name)[0]
        except KeyError:
            return super().get(name, default)

    def getlist(
        self, name: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        try:
            return self._get_prefixed_cookie(name)
        except KeyError:
            return super().getlist(name, default)

    def _get_prefixed_cookie(self, name: str) -> Any:
        getitem = super().__getitem__
        try:
            return getitem(f"{Cookie.HOST_PREFIX}{name}")
        except KeyError:
            return getitem(f"{Cookie.SECURE_PREFIX}{name}")
