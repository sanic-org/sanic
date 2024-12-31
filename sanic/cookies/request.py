import re

from typing import Any, Optional

from sanic.cookies.response import Cookie
from sanic.request.parameters import RequestParameters


COOKIE_NAME_RESERVED_CHARS = re.compile(
    '[\x00-\x1f\x7f-\xff()<>@,;:\\\\"/[\\]?={} \x09]'
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


def parse_cookie(raw: str) -> dict[str, list[str]]:
    """Parses a raw cookie string into a dictionary.

    The function takes a raw cookie string (usually from HTTP headers) and
    returns a dictionary where each key is a cookie name and the value is a
    list of values for that cookie. The function handles quoted values and
    skips invalid cookie names.

    Args:
        raw (str): The raw cookie string to be parsed.

    Returns:
        Dict[str, List[str]]: A dictionary containing the cookie names as keys
        and a list of values for each cookie.

    Example:
        ```python
        raw = 'name1=value1; name2="value2"; name3=value3'
        cookies = parse_cookie(raw)
        # cookies will be {'name1': ['value1'], 'name2': ['value2'], 'name3': ['value3']}
        ```
    """  # noqa: E501
    cookies: dict[str, list[str]] = {}

    for token in raw.split(";"):
        name, sep, value = token.partition("=")
        name = name.strip()
        value = value.strip()

        # Support cookies =value or plain value with no name
        # https://github.com/httpwg/http-extensions/issues/159
        if not sep:
            if not name:
                # Empty value like ;; or a cookie header with no value
                continue
            name, value = "", name

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
    """A container for accessing single and multiple cookie values.

    Because the HTTP standard allows for multiple cookies with the same name,
    a standard dictionary cannot be used to access cookie values. This class
    provides a way to access cookie values in a way that is similar to a
    dictionary, but also allows for accessing multiple values for a single
    cookie name when necessary.

    Args:
        cookies (Dict[str, List[str]]): A dictionary containing the cookie
            names as keys and a list of values for each cookie.

    Example:
        ```python
        raw = 'name1=value1; name2="value2"; name3=value3'
        cookies = parse_cookie(raw)
        # cookies will be {'name1': ['value1'], 'name2': ['value2'], 'name3': ['value3']}

        request_cookies = CookieRequestParameters(cookies)
        request_cookies['name1']  # 'value1'
        request_cookies.get('name1')  # 'value1'
        request_cookies.getlist('name1')  # ['value1']
        ```
    """  # noqa: E501

    def __getitem__(self, key: str) -> Optional[str]:
        try:
            value = self._get_prefixed_cookie(key)
        except KeyError:
            value = super().__getitem__(key)
        return value

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
        self, name: str, default: Optional[list[Any]] = None
    ) -> list[Any]:
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
