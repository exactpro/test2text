from .model_base import ModelNode, ModelCollection


class InstrumentGroup(ModelNode):
    """
    A logical group / basket / sector / watchlist of instruments.

    Owns:
        instruments -> Instrument
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)

        self.instruments = ModelCollection(name="instruments", owner=self)


class UserGroup(ModelNode):
    """
    A logical group of users (e.g. desk, desk group, client group).

    Owns:
        users -> User
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)

        self.users = ModelCollection(name="users", owner=self)
