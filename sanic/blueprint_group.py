class BlueprintGroup:
    """
    This class provides a mechanism to implement a Blueprint Group
    using the `Blueprint.group` method. To avoid having to re-write
    some of the existing implementation, this class provides a custom
    iterator implementation that will let you use the object of this
    class as a list/tuple inside the existing implementation.
    """

    def __init__(self, url_prefix=None):
        """
        Create a new Blueprint Group

        :param url_prefix: URL: to be prefixed before all the Blueprint Prefix
        """
        self._blueprints = []
        self._iter_position = 0
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

    @blueprints.setter
    def blueprints(self, blueprint):
        """
        Add a new Blueprint to the Group under consideration.
        :param blueprint: Instance of Blueprint
        :return: None
        """
        self._blueprints.append(blueprint)

    def __iter__(self):
        """Tun the class Blueprint Group into an Iterable item"""
        return iter(self._blueprints)

    def __next__(self):
        """
        A Custom method to iterate over the Blueprint Objects in the
        group under consideration
        """
        if not len(self._blueprints) or self._iter_position >= len(
            self._blueprints
        ):
            raise StopIteration
        else:
            self._iter_position += 1
            return self._blueprints[self._iter_position - 1]

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

        def register_middleware_for_blueprints(fn):
            for blueprint in self.blueprints:
                blueprint.middleware(fn, *args, **kwargs)

        return register_middleware_for_blueprints
