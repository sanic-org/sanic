from pygments.style import Style
from pygments.token import (  # Error,; Generic,; Number,; Operator,
    Comment,
    Keyword,
    Name,
    String,
    Token,
)


class SanicCodeStyle(Style):
    styles = {
        Token: "#777",
        Comment: "italic #a2a2a2",
        Keyword: "#ff0d68",
        Name: "#333",
        Name.Class: "bold #37ae6f",
        Name.Function: "#0092FF",
        String: "bg:#eee #833FE3",
    }
