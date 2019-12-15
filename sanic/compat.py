from multidict import CIMultiDict  # type: ignore


class Header(CIMultiDict):
    def get_all(self, key):
        return self.getall(key, default=[])
