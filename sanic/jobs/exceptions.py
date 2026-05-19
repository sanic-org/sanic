class JobError(Exception):
    """Base exception for job engine errors."""

    __slots__ = ("message",)

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class JobSerializationError(JobError):
    """Raised when a job payload cannot be serialized."""

    __slots__ = ()


class JobDeserializationError(JobError):
    """Raised when a job payload cannot be deserialized."""

    __slots__ = ()


class JobTimeoutError(JobError):
    """Raised when a job exceeds its timeout."""

    __slots__ = ()


class JobPerformError(JobError):
    """Raised when perform() raises an unhandled exception."""

    __slots__ = ("original",)

    def __init__(
        self, message: str = "", original: BaseException | None = None
    ) -> None:
        self.original = original
        super().__init__(message)
