from typing import Protocol, Union


class TransportProtocol(Protocol):
    def get_protocol(self):
        ...

    def get_extra_info(self, info: str) -> Union[str, bool, None]:
        ...
