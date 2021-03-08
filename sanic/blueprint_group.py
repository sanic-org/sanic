from collections.abc import MutableSequence
from typing import List, Optional, Union

import sanic


class BlueprintGroup(MutableSequence):
    """
    This class provides a mechanism to implement a Blueprint Group
    using the :meth:`~sanic.blueprints.Blueprint.group` method in
    :class:`~sanic.blueprints.Blueprint`. To avoid having to re-write
    some of the existing implementation, this class provides a custom
    iterator implementation that will let you use the object of this
    class as a list/tuple inside the existing implementation.

    .. code-block:: python

        bp1 = Blueprint('bp1', url_prefix='/bp1')
        bp2 = Blueprint('bp2', url_prefix='/bp2')

        bp3 = Blueprint('bp3', url_prefix='/bp4')
        bp3 = Blueprint('bp3', url_prefix='/bp4')

        bpg = BlueprintGroup(bp3, bp4, url_prefix="/api", version="v1")

        @bp1.middleware('request')
        async def bp1_only_middleware(request):
            print('applied on Blueprint : bp1 Only')

        @bp1.route('/')
        async def bp1_route(request):
            return text('bp1')

        @bp2.route('/<param>')
        async def bp2_route(request, param):
            return text(param)

        @bp3.route('/')
        async def bp1_route(request):
            return text('bp1')

        @bp4.route('/<param>')
        async def bp2_route(request, param):
            return text(param)

        group = Blueprint.group(bp1, bp2)

        @group.middleware('request')
        async def group_middleware(request):
            print('common middleware applied for both bp1 and bp2')

        # Register Blueprint group under the app
        app.blueprint(group)
        app.blueprint(bpg)
    """

    __slots__ = ("_blueprints", "_url_prefix", "_version", "_strict_slashes")

    def __init__(self, url_prefix=None, version=None, strict_slashes=None):
        """
        Create a new Blueprint Group

        :param url_prefix: URL: to be prefixed before all the Blueprint Prefix
        :param version: API Version for the blueprint group. This will be
            inherited by each of the Blueprint
        :param strict_slashes: URL Strict slash behavior indicator
        """
        self._blueprints = []
        self._url_prefix = url_prefix
        self._version = version
        self._strict_slashes = strict_slashes

    @property
    def url_prefix(self) -> str:
        """
        Retrieve the URL prefix being used for the Current Blueprint Group

        :return: string with url prefix
        """
        return self._url_prefix

    @property
    def blueprints(self) -> List["sanic.Blueprint"]:
        """
        Retrieve a list of all the available blueprints under this group.

        :return: List of Blueprint instance
        """
        return self._blueprints

    @property
    def version(self) -> Optional[Union[str, int, float]]:
        """
        API Version for the Blueprint Group. This will be applied only in case
        if the Blueprint doesn't already have a version specified

        :return: Version information
        """
        return self._version

    @property
    def strict_slashes(self) -> Optional[bool]:
        """
        URL Slash termination behavior configuration

        :return: bool
        """
        return self._strict_slashes

    def __iter__(self):
        """
        Tun the class Blueprint Group into an Iterable item
        """
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

    def __setitem__(self, index, item) -> None:
        """
        Abstract method implemented to turn the `BlueprintGroup` class
        into a list like object to support all the existing behavior.

        This method is used to perform the list's indexed setter operation.

        :param index: Index to use for inserting a new Blueprint item
        :param item: New `Blueprint` object.
        :return: None
        """
        self._blueprints[index] = item

    def __delitem__(self, index) -> None:
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

    def _sanitize_blueprint(self, bp: "sanic.Blueprint") -> "sanic.Blueprint":
        """
        Sanitize the Blueprint Entity to override the Version and strict slash
        behaviors as required.

        :param bp: Sanic Blueprint entity Object
        :return: Modified Blueprint
        """
        if self._url_prefix:
            merged_prefix = "/".join(
                u.strip("/") for u in [self._url_prefix, bp.url_prefix or ""]
            ).rstrip("/")
            bp.url_prefix = f"/{merged_prefix}"
        for _attr in ["version", "strict_slashes"]:
            if getattr(bp, _attr) is None:
                setattr(bp, _attr, getattr(self, _attr))
        return bp

    def append(self, value: "sanic.Blueprint") -> None:
        """
        The Abstract class `MutableSequence` leverages this append method to
        perform the `BlueprintGroup.append` operation.
        :param value: New `Blueprint` object.
        :return: None
        """
        self._blueprints.append(self._sanitize_blueprint(bp=value))

    def insert(self, index: int, item: "sanic.Blueprint") -> None:
        """
        The Abstract class `MutableSequence` leverages this insert method to
        perform the `BlueprintGroup.append` operation.

        :param index: Index to use for removing a new Blueprint item
        :param item: New `Blueprint` object.
        :return: None
        """
        self._blueprints.insert(index, self._sanitize_blueprint(item))

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

        if args and callable(args[0]):
            fn = args[0]
            args = list(args)[1:]
            return register_middleware_for_blueprints(fn)
        return register_middleware_for_blueprints
