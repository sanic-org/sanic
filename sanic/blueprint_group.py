from collections.abc import MutableSequence


class BlueprintGroup(MutableSequence):
    """
    This class provides a mechanism to implement a Blueprint Group
    using the `Blueprint.group` method. To avoid having to re-write
    some of the existing implementation, this class provides a custom
    iterator implementation that will let you use the object of this
    class as a list/tuple inside the existing implementation.
    """

    __slots__ = ("_blueprints", "_url_prefix")

    def __init__(self, url_prefix=None):
        """
        Create a new Blueprint Group

        :param url_prefix: URL: to be prefixed before all the Blueprint Prefix
        """
        self._blueprints = []
        self._url_prefix = url_prefix

    @property
    def url_prefix(self):
        """
        Retrieve the URL prefix being used for the Current Blueprint Group
        :return: string with url prefix
        """
        return self._url_prefix

    @property
    def blueprints(self):
        """
        Retrieve a list of all the available blueprints under this group.
        :return: List of Blueprint instance
        """
        return self._blueprints

    def __iter__(self):
        """Tun the class Blueprint Group into an Iterable item"""
        return iter(self._blueprints)

    def __getitem__(self, item):
        """
        This method returns a blueprint inside the group specified by
        an index value. This will enable indexing, splice and slicing
        of the blueprint group like we can do with regular list/tuple.

        This method is provided to ensure backward compatibility with
        any of the pre-existing usage that might break.

        :param item: Index of the Blueprint item in the group
        :return: Blueprint object
        """
        return self._blueprints[item]

    def __setitem__(self, index: int, item: object) -> None:
        """
        Abstract method implemented to turn the `BlueprintGroup` class
        into a list like object to support all the existing behavior.

        This method is used to perform the list's indexed setter operation.

        :param index: Index to use for inserting a new Blueprint item
        :param item: New `Blueprint` object.
        :return: None
        """
        self._blueprints[index] = item

    def __delitem__(self, index: int) -> None:
        """
        Abstract method implemented to turn the `BlueprintGroup` class
        into a list like object to support all the existing behavior.

        This method is used to delete an item from the list of blueprint
        groups like it can be done on a regular list with index.

        :param index: Index to use for removing a new Blueprint item
        :return: None
        """
        del self._blueprints[index]

    def __len__(self) -> int:
        """
        Get the Length of the blueprint group object.
        :return: Length of Blueprint group object
        """
        return len(self._blueprints)

    def insert(self, index: int, item: object) -> None:
        """
        The Abstract class `MutableSequence` leverages this insert method to
        perform the `BlueprintGroup.append` operation.

        :param index: Index to use for removing a new Blueprint item
        :param item: New `Blueprint` object.
        :return: None
        """
        self._blueprints.insert(index, item)

    def middleware(self, *args, **kwargs):
        """
        A decorator that can be used to implement a Middleware plugin to
        all of the Blueprints that belongs to this specific Blueprint Group.

        In case of nested Blueprint Groups, the same middleware is applied
        across each of the Blueprints recursively.

        :param args: Optional positional Parameters to be use middleware
        :param kwargs: Optional Keyword arg to use with Middleware
        :return: Partial function to apply the middleware
        """
        kwargs["bp_group"] = True

        def register_middleware_for_blueprints(fn):
            for blueprint in self.blueprints:
                blueprint.middleware(fn, *args, **kwargs)

        return register_middleware_for_blueprints
