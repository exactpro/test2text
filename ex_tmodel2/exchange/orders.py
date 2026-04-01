"""
Order classes - ParentOrder and ChildOrder
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, Dict, Any, TYPE_CHECKING

from .model_base import ModelNode, ModelState, ModelCollection

if TYPE_CHECKING: # pragma: no cover
    from .enums import Side, OrdType, TimeInForce, PegPriceType, DisplayMethod, OrdStatus

class ParentOrder(ModelNode):
    """
    Represents a parent order (top-level instruction).

    Owns:
        child_orders -> ChildOrder
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)

        self.parent_child_orders = ModelCollection(name="parent_child_orders", owner=self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "key": self.key,
        }


class ChildOrder(ModelState):
    """
    A ChildOrder cannot exist without a ParentOrder.
    On creation:
      - it links itself to its parent via .parent_order
      - it is automatically added to parent.child_orders

    For orders requiring many optional parameters, create with ready=False,
    use setter methods, then call mark_ready().
    """

    def __init__(
        self,
        key: str,
        parent: ParentOrder,
        price: Optional[Decimal] = None,
        quantity: Optional[Decimal] = None,
        side: Optional["Side"] = None,
        timestamp: Optional[str] = None,
        ordtype: Optional["OrdType"] = None,
        visible_quantity: Optional[Decimal] = None,
        tif: Optional["TimeInForce"] = None,
        memo: Optional[str] = None,
        testcase: Optional[str] = None,
        order_status: Optional["OrdStatus"] = None,
        iceberg_strategy_root_child_order: Optional[ChildOrder] = None,
        ready: bool = True,
    ) -> None:
        super().__init__(key)

        # Validate parent type
        if not isinstance(parent, ParentOrder):
            raise TypeError(
                f"ChildOrder(parent=...) must be a ParentOrder, got {type(parent).__name__}"
            )

        # Core fields from constructor
        self._price = price
        self._quantity = quantity
        self._side = side

        # Optional fields from constructor (for backward compatibility)
        self._visible_quantity = visible_quantity
        self._timestamp = timestamp
        self._ordtype = ordtype
        self._tif = tif
        self._memo = memo
        self._testcase = testcase
        self._order_status = order_status
        self._peg_offset_value = None
        self._peg_price_type = None
        self._min_quantity = None

        # Initialize new optional fields with None
        self._display_price = None
        self._rank_price = None
        self._display_method = None
        self._display_quantity = None

        # Sync display_quantity and visible_quantity:
        # If one is set and the other is not, copy the value
        if self._visible_quantity is not None and self._display_quantity is None:
            self._display_quantity = self._visible_quantity
        elif self._display_quantity is not None and self._visible_quantity is None:
            self._visible_quantity = self._display_quantity

        # Calculated fields
        self._cumulative_quantity = Decimal(0)
        self._leaves_quantity = quantity
        if self._leaves_quantity is not None:
            self._leaves_quantity -= self._cumulative_quantity

        self.iceberg_strategy_root_child_order = iceberg_strategy_root_child_order

        # Building state
        self._ready = ready

        # Counters counter
        self._amend_counter = 0
        self._replenishment_counter = 0
        self._execution_counter = 0

        # Link this child to its parent so child_order.parent_order works
        self.link_to("parent_order", parent)

        # Insert this child into the parent's child_orders collection
        parent.parent_child_orders[self.key] = self
        # Note: this also updates self._member_of["child_orders"] internally

    def mark_dirty(self) -> None:
        """
        Mark this child order as dirty and propagate to all related order books.

        This method marks the child order itself as dirty in the registry,
        then walks through all order books that contain this child order
        and marks them as dirty as well.
        """
        super().mark_dirty()

        # Walk through all collections this child order belongs to
        for collection_name, collection_list in self._member_of.items():
            # If it's a child_orders collection, mark the owner (OrderBook) as dirty
            if collection_name == "child_orders":
                for collection in collection_list:
                    if collection.owner is not None:
                        # The owner of a child_orders collection is typically an OrderBook
                        if hasattr(collection.owner, 'mark_dirty'):
                            collection.owner.mark_dirty()

    @property
    def ready(self) -> bool:
        """Check if the order is ready for processing."""
        return self._ready

    def mark_ready(self) -> "ChildOrder":
        """Mark the order as ready for processing."""
        self._ready = True
        self.mark_dirty()
        return self

    # Setter methods for optional parameters (return self for chaining)

    def set_price(self, price: Decimal) -> "ChildOrder":
        """Set the order price."""
        self._price = price
        self.mark_dirty()
        return self

    def set_quantity(self, quantity: Decimal) -> "ChildOrder":
        """Set the order quantity."""
        self._quantity = quantity
        self._leaves_quantity = quantity - self._cumulative_quantity
        if self._leaves_quantity < 0:
            self._leaves_quantity = Decimal(0)
        self.mark_dirty()
        return self

    def set_side(self, side: "Side") -> "ChildOrder":
        """Set the order side."""
        self._side = side
        self.mark_dirty()
        return self

    def set_visible_quantity(self, visible_quantity: Decimal, increment_replenishment_counter: bool=False) -> "ChildOrder":
        """Set the visible quantity.

        If display_quantity is None, also sets display_quantity to the same value.
        """
        self._visible_quantity = visible_quantity
        # Sync: if display_quantity is not set, set it to visible_quantity
        if self._display_quantity is None:
            self._display_quantity = visible_quantity
        if increment_replenishment_counter:
            self._replenishment_counter += 1
        self.mark_dirty()
        return self

    def set_timestamp(self, timestamp: str) -> "ChildOrder":
        """Set the order timestamp."""
        self._timestamp = timestamp
        self.mark_dirty()
        return self

    def set_ordtype(self, ordtype: "OrdType") -> "ChildOrder":
        """Set the order type."""
        self._ordtype = ordtype
        self.mark_dirty()
        return self

    def set_tif(self, tif: "TimeInForce") -> "ChildOrder":
        """Set the time in force."""
        self._tif = tif
        self.mark_dirty()
        return self

    def set_memo(self, memo: str) -> "ChildOrder":
        """Set the memo field."""
        self._memo = memo
        self.mark_dirty()
        return self

    def set_testcase(self, testcase: str) -> "ChildOrder":
        """Set the testcase field."""
        self._testcase = testcase
        self.mark_dirty()
        return self

    def set_order_status(self, order_status: "OrdStatus") -> "ChildOrder":
        """Set the order status."""
        self._order_status = order_status
        self.mark_dirty()
        return self

    def set_cumulative_quantity(self, cumulative_quantity: Decimal) -> "ChildOrder":
        """Set the cumulative executed quantity."""
        self._cumulative_quantity = cumulative_quantity
        self._leaves_quantity = self._quantity - cumulative_quantity if self._quantity else None
        if self._leaves_quantity is not None and self._leaves_quantity < 0:
            self._leaves_quantity = Decimal(0)
        self.mark_dirty()
        return self

    def set_peg_offset_value(self, peg_offset_value: Decimal) -> "ChildOrder":
        """Set the peg offset value."""
        self._peg_offset_value = peg_offset_value
        self.mark_dirty()
        return self

    def set_peg_price_type(self, peg_price_type: "PegPriceType") -> "ChildOrder":
        """Set the peg price type."""
        self._peg_price_type = peg_price_type
        self.mark_dirty()
        return self

    def set_min_quantity(self, min_quantity: Decimal) -> "ChildOrder":
        """Set the minimum quantity."""
        self._min_quantity = min_quantity
        self.mark_dirty()
        return self

    def set_display_price(self, display_price: Decimal) -> "ChildOrder":
        """Set the display price for display-only purposes."""
        self._display_price = display_price
        self.mark_dirty()
        return self

    def set_rank_price(self, rank_price: Decimal) -> "ChildOrder":
        """Set the rank price for priority calculations."""
        self._rank_price = rank_price
        self.mark_dirty()
        return self

    def set_display_method(self, display_method: "DisplayMethod") -> "ChildOrder":
        """Set the display method for iceberg/reserve orders."""
        self._display_method = display_method
        self.mark_dirty()
        return self

    def set_display_quantity(self, display_quantity: Decimal) -> "ChildOrder":
        """Set the display quantity for iceberg/reserve orders.

        If visible_quantity is None, also sets visible_quantity to the same value.
        """
        self._display_quantity = display_quantity
        # Sync: if visible_quantity is not set, set it to display_quantity
        if self._visible_quantity is None:
            self._visible_quantity = display_quantity
        self.mark_dirty()
        return self

    def set_visibility_parameters(
        self,
        ready: bool = True,
        peg_offset_value: Optional[Decimal] = None,
        rank_price: Optional[Decimal] = None,
        display_price: Optional[Decimal] = None,
        visibility_quantity: Optional[Decimal] = None,
    ) -> "ChildOrder":
        """
        Set multiple visibility-related parameters at once.

        Args:
            ready: Mark the order as ready for processing (optional)
            peg_offset_value: Peg offset value for pegged orders (optional)
            rank_price: Rank price for priority calculations (optional)
            display_price: Display price for display-only purposes (optional)
            visibility_quantity: Visible quantity (optional)

        Returns:
            Self for method chaining
        """
        if peg_offset_value is not None:
            self.set_peg_offset_value(peg_offset_value)

        if rank_price is not None:
            self.set_rank_price(rank_price)

        if display_price is not None:
            self.set_display_price(display_price)

        if visibility_quantity is not None:
            self.set_visible_quantity(visibility_quantity)

        if ready is not None:
            if ready:
                self.mark_ready()
            else:
                self._ready = False
                self.mark_dirty()

        return self

    # Read-only properties
    @property
    def price(self) -> Optional[Decimal]:
        """Get the order price."""
        return self._price

    @property
    def quantity(self) -> Optional[Decimal]:
        """Get the order quantity."""
        return self._quantity

    @property
    def side(self) -> Optional["Side"]:
        """Get the order side."""
        return self._side

    @property
    def ordtype(self) -> Optional["OrdType"]:
        """Get the order type."""
        return self._ordtype

    @property
    def tif(self) -> Optional["TimeInForce"]:
        """Get the time in force."""
        return self._tif

    @property
    def visible_quantity(self) -> Optional[Decimal]:
        """Get the visible quantity."""
        return self._visible_quantity

    @property
    def timestamp(self) -> Optional[str]:
        """Get the order timestamp."""
        return self._timestamp

    @property
    def memo(self) -> Optional[str]:
        """Get the memo field."""
        return self._memo

    @property
    def testcase(self) -> Optional[str]:
        """Get the testcase field."""
        return self._testcase

    @property
    def order_status(self) -> Optional["OrdStatus"]:
        """Get the order status."""
        return self._order_status

    @property
    def leaves_quantity(self) -> Optional[Decimal]:
        """Get the remaining quantity to be executed."""
        return self._leaves_quantity

    @property
    def cumulative_quantity(self) -> Decimal:
        """Get the cumulative executed quantity."""
        return self._cumulative_quantity

    @property
    def peg_offset_value(self) -> Optional[Decimal]:
        """Get the peg offset value for pegged orders."""
        return self._peg_offset_value

    @property
    def peg_price_type(self) -> Optional["PegPriceType"]:
        """Get the peg price type."""
        return self._peg_price_type

    @property
    def min_quantity(self) -> Optional[Decimal]:
        """Get the minimum quantity."""
        return self._min_quantity

    @property
    def display_price(self) -> Optional[Decimal]:
        """Get the display price."""
        return self._display_price

    @property
    def rank_price(self) -> Optional[Decimal]:
        """Get the rank price."""
        return self._rank_price

    @property
    def display_method(self) -> Optional["DisplayMethod"]:
        """Get the display method for iceberg/reserve orders."""
        return self._display_method

    @property
    def display_quantity(self) -> Optional[Decimal]:
        """Get the display quantity for iceberg/reserve orders."""
        return self._display_quantity

    @property
    def amend_counter(self) -> int:
        """Get the number of times this order has been amended."""
        return self._amend_counter

    @property
    def replenishment_counter(self) -> int:
        """Get the number of times this order has been replenished."""
        return self._replenishment_counter

    @property
    def execution_counter(self) -> int:
        """Get the number of times this order has been replenished."""
        return self._execution_counter

    def execute(self, price: Decimal, quantity: Decimal) -> None:
        """
        Execute the order.

        Args:
            price: Execution price
            quantity: Execution quantity
        """
        self._cumulative_quantity += quantity
        self._leaves_quantity -= quantity
        self._execution_counter += 1
        self.mark_dirty()

    def make_visible(self) -> None:
        """
        Make the order visible by setting visible_quantity to None
        """
        self._visible_quantity = None
        self.mark_dirty()


    def amend(
        self,
        ready: bool = True,
        price: Optional[Decimal] = None,
        quantity: Optional[Decimal] = None,
        side: Optional[Side] = None,
        ordtype: Optional[OrdType] = None,
        visible_quantity: Optional[Decimal] = None,
        timestamp: Optional[str] = None,
        timestamp_override: Optional[str] = None,
        peg_offset_value: Optional[Decimal] = None,
        peg_price_type: Optional[PegPriceType] = None,
        min_quantity: Optional[Decimal] = None,
        display_price: Optional[Decimal] = None,
        rank_price: Optional[Decimal] = None,
        tif: Optional[TimeInForce] = None,
    ) -> "ChildOrder":
        """
        Amend the order.

        Args:
            price: New price (optional)
            quantity: New quantity (optional)
            side: New side (optional)
            ordtype: New ordtype (optional)
            visible_quantity: New visible quantity (optional)
            timestamp: New timestamp (optional)
            timestamp_override: Will be applied regardless of priority loss (optional)
            cumulative_quantity: New cumulative quantity (optional)
            peg_offset_value: New peg offset value (optional)
            peg_price_type: New peg price type (optional)
            min_quantity: New minimum quantity (optional)
            display_price: New display price (optional)
            rank_price: New rank price (optional)
            ready: Set ready state (optional)

        Returns:
            Self for method chaining
        """
        self._amend_counter += 1

        # Track if timestamp should be updated due to price/quantity changes
        should_update_timestamp = False

        if price is not None and price != self._price:
            self.set_price(price)
            should_update_timestamp = True

        if quantity is not None and quantity != self._quantity:
            old_quantity = self._quantity
            self.set_quantity(quantity)
            # Update timestamp if quantity increased
            if old_quantity is not None and quantity > old_quantity:
                should_update_timestamp = True

        if side is not None and side != self._side:
            self.set_side(side)

        if ordtype is not None and ordtype != self._ordtype:
            self.set_ordtype(ordtype)

        if tif is not None and tif != self._tif:
            self.set_tif(tif)

        if visible_quantity is not None and visible_quantity != self._visible_quantity:
            self.set_visible_quantity(visible_quantity)

        if peg_offset_value is not None and peg_offset_value != self._peg_offset_value:
            self.set_peg_offset_value(peg_offset_value)

        if peg_price_type is not None and peg_price_type != self._peg_price_type:
            self.set_peg_price_type(peg_price_type)

        if min_quantity is not None and min_quantity != self._min_quantity:
            self.set_min_quantity(min_quantity)

        if display_price is not None and display_price != self._display_price:
            self.set_display_price(display_price)

        if rank_price is not None and rank_price != self._rank_price:
            self.set_rank_price(rank_price)

        # Handle timestamp updates
        if timestamp_override is not None and timestamp_override != self._timestamp:
            self.set_timestamp(timestamp_override)
        elif should_update_timestamp and timestamp is not None:
            self.set_timestamp(timestamp)

        # Handle ready state
        if ready is not None and ready != self._ready:
            self._ready = ready
            self.mark_dirty()

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "key": self.key,
            "parent_order_key": self.parent_order.key,
        }
        if self._price is not None:
            result["price"] = str(self._price)
        if self._quantity is not None:
            result["quantity"] = str(self._quantity)
        if self._side is not None:
            result["side"] = self._side.value
        if self._timestamp is not None:
            result["timestamp"] = self._timestamp
        if self._ordtype is not None:
            result["ordtype"] = self._ordtype.value
        if self._visible_quantity is not None:
            result["visible_quantity"] = str(self._visible_quantity)
        if self._tif is not None:
            result["tif"] = self._tif.value
        if self._memo is not None:
            result["memo"] = self._memo
        if self._testcase is not None:
            result["testcase"] = self._testcase
        if self._order_status is not None:
            result["order_status"] = self._order_status.value
        if self._peg_offset_value is not None:
            result["peg_offset_value"] = str(self._peg_offset_value)
        if self._peg_price_type is not None:
            result["peg_price_type"] = self._peg_price_type.value
        if self._min_quantity is not None:
            result["min_quantity"] = str(self._min_quantity)
        if self._display_price is not None:
            result["display_price"] = str(self._display_price)
        if self._rank_price is not None:
            result["rank_price"] = str(self._rank_price)
        if self._display_method is not None:
            result["display_method"] = self._display_method.value
        if self._display_quantity is not None:
            result["display_quantity"] = str(self._display_quantity)
        if self._cumulative_quantity != Decimal(0):
            result["cumulative_quantity"] = str(self._cumulative_quantity)
        if self._leaves_quantity is not None and self._leaves_quantity != self._quantity:
            result["leaves_quantity"] = str(self._leaves_quantity)
        return result
