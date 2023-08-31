from __future__ import annotations

import email.utils
import unicodedata

from typing import NamedTuple
from urllib.parse import unquote

from sanic.headers import parse_content_header
from sanic.log import logger

from .parameters import RequestParameters


class File(NamedTuple):
    """Model for defining a file.

    It is a `namedtuple`, therefore you can iterate over the object, or
    access the parameters by name.

    Args:
        type (str, optional): The mimetype, defaults to "text/plain".
        body (bytes): Bytes of the file.
        name (str): The filename.
    """

    type: str
    body: bytes
    name: str


def parse_multipart_form(body, boundary):
    """Parse a request body and returns fields and files

    Args:
        body (bytes): Bytes request body.
        boundary (bytes): Bytes multipart boundary.

    Returns:
        Tuple[RequestParameters, RequestParameters]: A tuple containing fields and files as `RequestParameters`.
    """  # noqa: E501
    files = {}
    fields = {}

    form_parts = body.split(boundary)
    for form_part in form_parts[1:-1]:
        file_name = None
        content_type = "text/plain"
        content_charset = "utf-8"
        field_name = None
        line_index = 2
        line_end_index = 0
        while not line_end_index == -1:
            line_end_index = form_part.find(b"\r\n", line_index)
            form_line = form_part[line_index:line_end_index].decode("utf-8")
            line_index = line_end_index + 2

            if not form_line:
                break

            colon_index = form_line.index(":")
            idx = colon_index + 2
            form_header_field = form_line[0:colon_index].lower()
            form_header_value, form_parameters = parse_content_header(
                form_line[idx:]
            )

            if form_header_field == "content-disposition":
                field_name = form_parameters.get("name")
                file_name = form_parameters.get("filename")

                # non-ASCII filenames in RFC2231, "filename*" format
                if file_name is None and form_parameters.get("filename*"):
                    encoding, _, value = email.utils.decode_rfc2231(
                        form_parameters["filename*"]
                    )
                    file_name = unquote(value, encoding=encoding)

                # Normalize to NFC (Apple MacOS/iOS send NFD)
                # Notes:
                # - No effect for Windows, Linux or Android clients which
                #   already send NFC
                # - Python open() is tricky (creates files in NFC no matter
                #   which form you use)
                if file_name is not None:
                    file_name = unicodedata.normalize("NFC", file_name)

            elif form_header_field == "content-type":
                content_type = form_header_value
                content_charset = form_parameters.get("charset", "utf-8")

        if field_name:
            post_data = form_part[line_index:-4]
            if file_name is None:
                value = post_data.decode(content_charset)
                if field_name in fields:
                    fields[field_name].append(value)
                else:
                    fields[field_name] = [value]
            else:
                form_file = File(
                    type=content_type, name=file_name, body=post_data
                )
                if field_name in files:
                    files[field_name].append(form_file)
                else:
                    files[field_name] = [form_file]
        else:
            logger.debug(
                "Form-data field does not have a 'name' parameter "
                "in the Content-Disposition header"
            )

    return RequestParameters(fields), RequestParameters(files)
