import logging


class VerbosityFilter(logging.Filter):
    verbosity: int = 0

    def filter(self, record: logging.LogRecord) -> bool:
        verbosity = getattr(record, "verbosity", 0)
        return verbosity <= self.verbosity
