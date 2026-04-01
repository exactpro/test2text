""" 
Base classes for the digital twin toolkit
"""

from __future__ import annotations
from typing import Iterable

from .exchange import ModelExchange
from .orders import ParentOrder, ChildOrder
from .instruments import Instrument, OrderBook
from .users import User

def _iter_all_order_books(exchange: ModelExchange) -> Iterable[OrderBook]:
    """
    Walk the exchange hierarchy and yield every OrderBook instance.
    Logic:
      exchange.instruments -> Instrument nodes
      each instrument.order_books -> OrderBook nodes
    """
    for instr in exchange.instruments.values():
        # instr is an Instrument
        for ob in instr.order_books.values():
            yield ob


def delete_child_order(exchange: ModelExchange, child: ChildOrder) -> None:
    """
    Remove a ChildOrder from the model.

    Steps:
    1. Remove from exchange.child_orders
    2. Remove from parent.child_orders (if the child has a parent)
    3. Remove from every OrderBook.child_orders

    This function can be used to delete individual child orders,
    even if they are not associated with any parent order.

    Assumptions:
    - ChildOrder.__init__(key, parent) may have:
         * linked child.parent_order -> parent
         * inserted child into parent.child_orders
    - exchange.child_orders, instrument.order_books, order_book.child_orders
      all follow the current model.
    """
    child_key = child.key

    # 1. Remove from global child_orders view
    if child_key in exchange.exchange_child_orders:
        del exchange.exchange_child_orders[child_key]

    # 2. Remove from the parent's child_orders (if it has a parent)
    if hasattr(child, 'parent_order') and child.parent_order is not None:
        if child_key in child.parent_order.parent_child_orders:
            del child.parent_order.parent_child_orders[child_key]

    # 3. Remove from every order book's view
    for ob in _iter_all_order_books(exchange):
        if child_key in ob.child_orders:
            del ob.child_orders[child_key]

    # After this function runs, the child order should not be reachable
    # from exchange.child_orders, parent.child_orders (if applicable),
    # or any ob.child_orders


def delete_parent_order(exchange: ModelExchange, parent: ParentOrder) -> None:
    """
    Remove a ParentOrder from the model, along with *all* of its ChildOrder nodes.

    Steps:
    1. Collect all child orders from parent.child_orders.
    2. For each child order: delete using delete_child_order()
    3. Remove the parent order itself:
        - from exchange.parent_orders
        - from every User.parent_orders

    Assumptions:
    - ChildOrder.__init__(key, parent) already:
         * linked child.parent_order -> parent
         * inserted child into parent.child_orders
    - exchange.child_orders, exchange.parent_orders, user.parent_orders,
      instrument.order_books, order_book.child_orders all follow the current model.
    """

    # --- Step 1: collect all child order keys for this parent
    # We snapshot keys() because we will mutate collections while deleting.

    child_keys = list(parent.parent_child_orders.keys())

    # --- Step 2: remove each child order using delete_child_order
    for child_key in child_keys:
        child_node = parent.parent_child_orders[child_key]
        # We assume child_node is a ChildOrder
        delete_child_order(exchange, child_node)

    # --- Step 3: remove the parent order itself everywhere it appears

    parent_key = parent.key

    # 3a. Remove from exchange.parent_orders
    if parent_key in exchange.parent_orders:
        del exchange.parent_orders[parent_key]

    # 3b. Remove from any user's parent_orders
    for user in exchange.users.values():
        # user is expected to be a User node
        if parent_key in user.parent_orders:
            del user.parent_orders[parent_key]

    # Note:
    # We don't explicitly "delete" the objects from memory.
    # After this method runs, there should be no remaining references to
    # the parent or its child orders via any collection on the exchange,
    # order books, or users. Python GC can reclaim them if you drop any
    # local vars referring to them.