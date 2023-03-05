from __future__ import annotations

import re
import string
import sys
from datetime import datetime
from typing import Dict, Optional, Union

if sys.version_info < (3, 8):  # no cov
    SameSite = str
else:  # no cov
    from typing import Literal

    SameSite = Union[
        Literal["Strict"],
        Literal["Lax"],
        Literal["None"],
        Literal["strict"],
        Literal["lax"],
        Literal["none"],
    ]

DEFAULT_MAX_AGE = 0
SAMESITE_VALUES = ("strict", "lax", "none")

# ------------------------------------------------------------ #
#  SimpleCookie
# ------------------------------------------------------------ #

# Straight up copied this section of dark magic from SimpleCookie

_LegalChars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~:"
_UnescapedChars = _LegalChars + " ()/<=>?@[]{}"

_Translator = {
    n: "\\%03o" % n for n in set(range(256)) - set(map(ord, _UnescapedChars))
}
_Translator.update({ord('"'): '\\"', ord("\\"): "\\\\"})


def _quote(str):
    r"""Quote a string for use in a cookie header.
    If the string does not need to be double-quoted, then just return the
    string.  Otherwise, surround the string in doublequotes and quote
    (with a \) special characters.
    """
    if str is None or _is_legal_key(str):
        return str
    else:
        return '"' + str.translate(_Translator) + '"'


_is_legal_key = re.compile("[%s]+" % re.escape(_LegalChars)).fullmatch

# ------------------------------------------------------------ #
#  Custom SimpleCookie
# ------------------------------------------------------------ #


class CookieJar(dict):
    """
    CookieJar dynamically writes headers as cookies are added and removed
    It gets around the limitation of one header per name by using the
    MultiHeader class to provide a unique key that encodes to Set-Cookie.
    """

    def __init__(self, headers):
        super().__init__()
        self.headers: Dict[str, str] = headers
        self.cookie_headers: Dict[str, str] = {}
        self.header_key: str = "Set-Cookie"

    def __setitem__(self, key, value):
        # If this cookie doesn't exist, add it to the header keys
        if not self.cookie_headers.get(key):
            cookie = Cookie(key, value)
            cookie["path"] = "/"
            self.cookie_headers[key] = self.header_key
            self.headers.add(self.header_key, cookie)
            return super().__setitem__(key, cookie)
        else:
            self[key].value = value

    def __delitem__(self, key):
        if key not in self.cookie_headers:
            self[key] = ""
            self[key]["max-age"] = 0
        else:
            cookie_header = self.cookie_headers[key]
            # remove it from header
            cookies = self.headers.popall(cookie_header)
            for cookie in cookies:
                if cookie.key != key:
                    self.headers.add(cookie_header, cookie)
            del self.cookie_headers[key]
            del self[key]
            return super().__delitem__(key)

    def add(
        self,
        key: str,
        value: str,
        *,
        path: Optional[str] = None,
        expires: Optional[datetime] = None,
        comment: Optional[str] = None,
        domain: Optional[str] = None,
        max_age: Optional[int] = None,
        secure: Optional[bool] = None,
        httponly: Optional[bool] = None,
        samesite: Optional[SameSite] = None,
    ) -> Cookie:
        """
        Add a cookie to the response

        :param key: Key of the cookie
        :type key: str
        :param value: Value of the cookie
        :type value: str
        :param path: Path of the cookie, defaults to None
        :type path: Optional[str], optional
        :param expires: When the cookie expires; if set to None browsers
            should set it as a session cookie, defaults to None
        :type expires: Optional[datetime], optional
        :param comment: A cookie comment, defaults to None
        :type comment: Optional[str], optional
        :param domain: Domain of the cookie, defaults to None
        :type domain: Optional[str], optional
        :param max_age: Max age of the cookie in seconds; if set to 0 a
            browser should delete it, defaults to None
        :type max_age: Optional[int], optional
        :param secure: Whether to set it as a secure cookie, defaults to None
        :type secure: Optional[bool], optional
        :param httponly: Whether to set it as HTTP only, defaults to None
        :type httponly: Optional[bool], optional
        :param samesite: How to set the samesite property, should be
            strict, lax or none, defaults to None
        :type samesite: Optional[SameSite], optional
        :return: The instance of the created cookie
        :rtype: Cookie
        """
        self[key] = value
        cookie = self[key]
        if path is not None:
            cookie["path"] = path
        if expires is not None:
            cookie["expires"] = expires
        if comment is not None:
            cookie["comment"] = comment
        if domain is not None:
            cookie["domain"] = domain
        if max_age is not None:
            cookie["max-age"] = max_age
        if secure is not None:
            cookie["secure"] = secure
        if httponly is not None:
            cookie["httponly"] = httponly
        if samesite is not None:
            cookie["samesite"] = samesite
        return cookie

    def delete(self, key: str) -> None:
        """
        Delete a cookie from the response

        This will effectively set it as Max-Age: 0, which a browser should
        interpret it to mean: "delete the cookie".

        Since it is a browser/client implementation, your results may vary
        depending upon which client is being used.

        :param key: The key to be deleted
        :type key: str
        """
        del self[key]


class Cookie(dict):
    """A stripped down version of Morsel from SimpleCookie #gottagofast"""

    _keys = {
        "expires": "expires",
        "path": "Path",
        "comment": "Comment",
        "domain": "Domain",
        "max-age": "Max-Age",
        "secure": "Secure",
        "httponly": "HttpOnly",
        "version": "Version",
        "samesite": "SameSite",
    }
    _flags = {"secure", "httponly"}

    def __init__(self, key, value):
        if key in self._keys:
            raise KeyError("Cookie name is a reserved word")
        if not _is_legal_key(key):
            raise KeyError("Cookie key contains illegal characters")
        self.key = key
        self.value = value
        super().__init__()

    def __setitem__(self, key, value):
        if key not in self._keys:
            raise KeyError("Unknown cookie property")
        if value is not False:
            if key.lower() == "max-age" and not str(value).isdigit():
                raise ValueError("Cookie max-age must be an integer")
            elif key.lower() == "expires" and not isinstance(value, datetime):
                raise TypeError("Cookie 'expires' property must be a datetime")
            elif key.lower() == "samesite":
                if value.lower() not in SAMESITE_VALUES:
                    raise TypeError(
                        "Cookie 'samesite' property must "
                        f"be one of: {','.join(SAMESITE_VALUES)}"
                    )
                value = value.title()
            return super().__setitem__(key, value)

    def encode(self, encoding):
        """
        Encode the cookie content in a specific type of encoding instructed
        by the developer. Leverages the :func:`str.encode` method provided
        by python.

        This method can be used to encode and embed ``utf-8`` content into
        the cookies.

        :param encoding: Encoding to be used with the cookie
        :return: Cookie encoded in a codec of choosing.
        :except: UnicodeEncodeError
        """
        return str(self).encode(encoding)

    def __str__(self):
        """Format as a Set-Cookie header value."""
        output = ["%s=%s" % (self.key, _quote(self.value))]
        for key, value in self.items():
            if key == "max-age":
                try:
                    output.append("%s=%d" % (self._keys[key], value))
                except TypeError:
                    output.append("%s=%s" % (self._keys[key], value))
            elif key == "expires":
                output.append(
                    "%s=%s"
                    % (self._keys[key], value.strftime("%a, %d-%b-%Y %T GMT"))
                )
            elif key in self._flags and self[key]:
                output.append(self._keys[key])
            else:
                output.append("%s=%s" % (self._keys[key], value))

        return "; ".join(output)

    @property
    def path(self) -> Optional[str]:
        return self.get("path")

    @path.setter
    def path(self, value: str) -> None:
        self["path"] = value

    @path.deleter
    def path(self) -> None:
        del self["path"]

    @property
    def expires(self) -> Optional[datetime]:
        return self.get("expires")

    @expires.setter
    def expires(self, value: datetime) -> None:
        self["expires"] = value

    @expires.deleter
    def expires(self) -> None:
        del self["expires"]

    @property
    def comment(self) -> Optional[str]:
        return self.get("comment")

    @comment.setter
    def comment(self, value: str) -> None:
        self["comment"] = value

    @comment.deleter
    def comment(self) -> None:
        del self["comment"]

    @property
    def domain(self) -> Optional[str]:
        return self.get("domain")

    @domain.setter
    def domain(self, value: str) -> None:
        self["domain"] = value

    @domain.deleter
    def domain(self) -> None:
        del self["domain"]

    @property
    def max_age(self) -> Optional[int]:
        return self.get("max-age")

    @max_age.setter
    def max_age(self, value: int) -> None:
        self["max-age"] = value

    @max_age.deleter
    def max_age(self) -> None:
        del self["max-age"]

    @property
    def secure(self) -> Optional[bool]:
        return self.get("secure")

    @secure.setter
    def secure(self, value: bool) -> None:
        self["secure"] = value

    @secure.deleter
    def secure(self) -> None:
        del self["secure"]

    @property
    def httponly(self) -> Optional[bool]:
        return self.get("httponly")

    @httponly.setter
    def httponly(self, value: bool) -> None:
        self["httponly"] = value

    @httponly.deleter
    def httponly(self) -> None:
        del self["httponly"]

    @property
    def samesite(self) -> Optional[SameSite]:
        return self.get("samesite")

    @samesite.setter
    def samesite(self, value: SameSite) -> None:
        self["samesite"] = value

    @samesite.deleter
    def samesite(self) -> None:
        del self["samesite"]
