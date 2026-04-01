"""
User class
"""

from .model_base import ModelNode, ModelCollection


class User(ModelNode):
    """
    Represents a user / client / trader / desk identity in the model.

    Owns:
        parent_orders -> ParentOrder
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)

        self.parent_orders = ModelCollection(name="parent_orders", owner=self)
