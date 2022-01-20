from enum import Enum, IntEnum


class Stage(Enum):
    """
    Enum for representing the stage of the request/response cycle

    | ``IDLE``  Waiting for request
    | ``REQUEST``  Request headers being received
    | ``HANDLER``  Headers done, handler running
    | ``RESPONSE``  Response headers sent, body in progress
    | ``FAILED``  Unrecoverable state (error while sending response)
    |
    """

    IDLE = 0  # Waiting for request
    REQUEST = 1  # Request headers being received
    HANDLER = 3  # Headers done, handler running
    RESPONSE = 4  # Response headers sent, body in progress
    FAILED = 100  # Unrecoverable state (error while sending response)


class HTTP(IntEnum):
    VERSION_1 = 1
    VERSION_3 = 3

    def display(self) -> str:
        value = str(self.value)
        if value == 1:
            value = "1.1"
        return f"HTTP/{value}"
