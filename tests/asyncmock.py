"""for 3.7 compat"""


class AsyncMock:
    """A mock that acts like an async def function."""

    def __init__(self, return_value=None, return_values=None):
        if return_values is not None:
            self._return_value = return_values
            self._index = 0
        else:
            self._return_value = return_value
            self._index = None
        self._call_count = 0
        self._call_args = None
        self._call_kwargs = None

    @property
    def call_args(self):
        return self._call_args

    @property
    def call_kwargs(self):
        return self._call_kwargs

    @property
    def called(self):
        return self._call_count > 0

    @property
    def call_count(self):
        return self._call_count

    async def __call__(self, *args, **kwargs):
        self._call_args = args
        self._call_kwargs = kwargs
        self._call_count += 1
        if self._index is not None:
            return_index = self._index
            self._index += 1
            return self._return_value[return_index]
        else:
            return self._return_value
