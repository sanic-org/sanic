from multidict import CIMultiDict


class Header(CIMultiDict):
    def get_all(self, key):
        return self.getall(key, default=[])
