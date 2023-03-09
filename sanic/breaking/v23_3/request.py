from ..v22_12.request import File
from ..v22_12.request import Request as LegacyRequest
from ..v22_12.request import RequestParameters, parse_multipart_form


class Request(LegacyRequest):
    @property
    def something_new(self):
        return 123
