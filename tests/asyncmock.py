"""
For 3.7 compat

"""


from unittest.mock import Mock


class AsyncMock(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.await_count = 0

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        parent = super(AsyncMock, self)

        async def dummy():
            self.await_count += 1
            return parent.__call__(*args, **kwargs)

        return dummy()

    def __await__(self):
        return self().__await__()

    def assert_awaited_once(self):
        if not self.await_count == 1:
            msg = (
                f"Expected to have been awaited once."
                f" Awaited {self.await_count} times."
            )
            raise AssertionError(msg)
