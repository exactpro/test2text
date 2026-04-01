from __future__ import annotations

from decimal import Decimal
from typing import Optional, List, Dict, Any, Set, TYPE_CHECKING

from .model_base import ModelNode, ModelState, ModelCollection

from .market_data import Level2MarketData, PriceLevel
from .enums import Side, OrdType

if TYPE_CHECKING:  # pragma: no cover
    from .orders import ChildOrder


class OrderBookPriorityComparisonResultEntry:
    """
    Result of comparing the priority of two orders.

    Attributes:
        has_higher_priority: True if the first order has higher priority than the second
        reason: String explaining the priority determination
    """

    def __init__(self, has_higher_priority: bool, reason: str):
        self.has_higher_priority = has_higher_priority
        self.reason = reason
        self.key1 = None
        self.key2 = None

    def __repr__(self):
        return f"OrderBookPriorityComparisonResultEntry(has_higher_priority={self.has_higher_priority}, reason='{self.reason}')"


class InstrumentStatus(ModelState):
    """
    Represents the status of an instrument, including National Best Bid and Offer (NBBO).

    Properties:
        nbb: National Best Bid - the highest bid price across all venues
        nbo: National Best Offer - the lowest ask/offer price across all venues
        default_book_best_bid: Best bid price from the default order book (read-only)
        default_book_best_ask: Best ask price from the default order book (read-only)
        instrument: The instrument this status belongs to

    Methods:
        refresh_status(): Recalculates default_book_best_bid and default_book_best_ask from the default order book
    """

    def __init__(self, key: str, instrument: "Instrument") -> None:
        super().__init__(key)
        self._extenral_nbb: Optional[Decimal] = None
        self._external_nbo: Optional[Decimal] = None
        self._default_book_best_bid: Optional[Decimal] = None
        self._default_book_best_ask: Optional[Decimal] = None
        self._session: Optional[str] = None

        # Link to the instrument (owner)
        self.link_to("instrument", instrument)

    @property
    def external_nbb(self) -> Optional[Decimal]:
        """Get the National Best Bid."""
        return self._extenral_nbb

    @external_nbb.setter
    def external_nbb(self, value: Optional[Decimal]) -> None:
        """Set the National Best Bid."""
        self._extenral_nbb = value
        self.mark_dirty()

    @property
    def external_nbo(self) -> Optional[Decimal]:
        """Get the National Best Offer."""
        return self._external_nbo

    @external_nbo.setter
    def external_nbo(self, value: Optional[Decimal]) -> None:
        """Set the National Best Offer."""
        self._external_nbo = value
        self.mark_dirty()

    @property
    def session(self) -> Optional[str]:
        """Get the trading session."""
        return self._session

    @session.setter
    def session(self, value: Optional[str]) -> None:
        """Set the trading session."""
        self._session = value
        self.mark_dirty()

    @property
    def default_book_best_bid(self) -> Optional[Decimal]:
        """Get the best bid from the default order book."""
        return self._default_book_best_bid

    @property
    def default_book_best_ask(self) -> Optional[Decimal]:
        """Get the best ask from the default order book."""
        return self._default_book_best_ask

    def refresh_status(self) -> None:
        """
        Refresh the status by recalculating default_book_best_bid and default_book_best_ask
        from the default order book's market data.

        This method:
        1. Gets the default order book from the instrument
        2. Converts it to market data (respecting visible_quantity by default)
        3. Updates default_book_best_bid and default_book_best_ask with the best prices
        """
        # Get the default order book
        default_book = self.instrument.get_default_order_book()

        if default_book is None:
            # No default book, set to None
            self._default_book_best_bid = None
            self._default_book_best_ask = None
            self.mark_dirty()
            return

        # Convert to market data (include_hidden=False by default)
        md = default_book.to_market_data(include_hidden=False)

        # Update the internal properties
        self._default_book_best_bid = md.best_bid()
        self._default_book_best_ask = md.best_ask()
        self.mark_dirty()


class InstrumentConfiguration:
    """
    Configuration settings for an Instrument.

    Attributes:
        enable_priority_checks: Whether to enable priority checking for this instrument (default: True)
        enable_limit_price_check: Whether to enable limit price checking for this instrument (default: True)
    """

    def __init__(self, enable_priority_checks: bool = True, enable_limit_price_check: bool = True, autofill_enabled: str = None, autofill_broker: str = None) -> None:
        self.enable_priority_checks = enable_priority_checks
        self.enable_limit_price_check = enable_limit_price_check
        self.autofill_enabled = autofill_enabled
        self.autofill_broker = autofill_broker


class Instrument(ModelNode):
    """
    Represents a tradeable instrument (symbol, listing, etc.).

    Owns:
        order_books -> OrderBook
        instrument_child_orders -> ChildOrder (aggregated from all order books)

    Optional:
        book_names: List of book names to automatically create OrderBook instances
                   If None or empty, creates a default book named "0"
        configuration: InstrumentConfiguration object with settings for this instrument
    """

    def __init__(self, key: str, book_names: Optional[List[str]] = None,
        configuration: Optional[InstrumentConfiguration] = None,
        underlying: Optional[str] = None
    ) -> None:
        super().__init__(key)

        self.configuration = configuration if configuration is not None else InstrumentConfiguration()
        self.underlying = underlying
        if self.underlying is None:
            self.underlying = key

        self.order_books = ModelCollection(name="order_books", owner=self)
        self.instrument_child_orders = ModelCollection(name="instrument_child_orders", owner=self)

        # Dictionary to store aliases: {symbology: symbol}
        self._aliases: Dict[str, str] = {}

        # Instrument status tracking NBBO
        self.status = InstrumentStatus(key=f"{key}_status", instrument=self)

        # Create OrderBook instances for each book name if provided
        # If no book names provided (None or empty list), create default book "0"
        # Note: OrderBook constructor automatically adds itself to instrument.order_books
        if book_names:
            for book_name in book_names:
                # OrderBook will automatically add itself to self.order_books
                OrderBook(book_name, instrument=self)
        else:
            # Create default book "0"
            # OrderBook will automatically add itself to self.order_books
            OrderBook("0", instrument=self)

    def on_order_book_added(self, order_book: "OrderBook") -> None:
        """Called when an OrderBook is added to this Instrument."""
        order_book.link_to("instrument", self)

    def get_default_order_book(self) -> Optional["OrderBook"]:
        """
        Get the default order book for this instrument.

        Returns the order book with key "0", which is the default order book
        created for every instrument.

        Returns:
            The default OrderBook if it exists, None otherwise
        """
        return self.order_books.get_default_node()

    def add_alias(self, symbology: str, symbol: str) -> None:
        """
        Add an alias for this instrument under a specific symbology.

        Args:
            symbology: The symbology type (e.g., "RIC", "ISIN", "NasdaqSymbol")
            symbol: The symbol value for this symbology
        """
        # Check if we're replacing an existing alias for this symbology
        old_symbol = self._aliases.get(symbology)

        # Store the alias
        self._aliases[symbology] = symbol

        # Register with the exchange if this instrument is linked to one
        if hasattr(self, '_links') and 'exchange' in self._links:
            exchange = self._links['exchange']
            # If replacing, unregister the old symbol first
            if old_symbol is not None and old_symbol != symbol:
                exchange._unregister_alias(symbology, old_symbol)
            # Register the new symbol
            exchange._register_alias(symbology, symbol, self)

    def get_alias(self, symbology: str) -> Optional[str]:
        """
        Get the alias (symbol) for this instrument under a specific symbology.

        Args:
            symbology: The symbology type (e.g., "RIC", "ISIN", "NasdaqSymbol")

        Returns:
            The symbol value for this symbology, or None if not found
        """
        return self._aliases.get(symbology)

    def remove_alias(self, symbology: str) -> None:
        """
        Remove an alias for this instrument under a specific symbology.

        Args:
            symbology: The symbology type to remove
        """
        # Get the symbol before removing (needed for exchange cleanup)
        symbol = self._aliases.pop(symbology, None)

        # Unregister from the exchange if this instrument is linked to one
        if symbol is not None:
            if hasattr(self, '_links') and 'exchange' in self._links:
                exchange = self._links['exchange']
                exchange._unregister_alias(symbology, symbol)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "key": self.key,
            "order_books": [ob.to_dict() for ob in self.order_books.values()],
        }
        if self._aliases:
            result["aliases"] = self._aliases.copy()
        if self.underlying is not None:
            result["underlying"] = self.underlying
        return result


class OrderBook(ModelState):
    """
    Represents an order book for a particular instrument / venue / side.

    An OrderBook cannot exist without an Instrument.
    On creation:
      - it links itself to its instrument via .instrument
      - it is automatically added to instrument.order_books

    Owns:
        child_orders -> ChildOrder

    Note:
    - ModelExchange does not expose an 'order_books' collection at the top level,
      but each Instrument can have its own order_books collection containing
      OrderBook nodes, and each OrderBook can then maintain its own child_orders.
    """

    def __init__(self, key: str, instrument: Instrument) -> None:
        super().__init__(key)

        # Validate instrument type
        if not isinstance(instrument, Instrument):
            raise TypeError(
                f"OrderBook(instrument=...) must be an Instrument, got {type(instrument).__name__}"
            )

        self.child_orders = ModelCollection(name="child_orders", owner=self)

        # Link this order book to its instrument
        self.link_to("instrument", instrument)

        # Insert this order book into the instrument's order_books collection
        instrument.order_books[self.key] = self
        # Note: this also updates self._member_of["order_books"] internally

        # Real-time market data tracking
        self._market_data_tracking_enabled = False
        self._tracked_market_data = None

    def get_full_key(self) -> str:
        """
        Return the full key combining instrument key and order book key.

        Returns:
            String in format "instrument_key|order_book_key"
        """
        return f"{self.instrument.key}|{self.key}"

    @staticmethod
    def normalize_side(side: Side) -> Side:
        """
        Normalize a Side enum value to either BUY or SELL.

        Args:
            side: The Side enum value to normalize

        Returns:
            Side.BUY for BUY-related sides (BUY, BUY_MINUS)
            Side.SELL for SELL-related sides (SELL, SELL_PLUS, SELL_SHORT, SELL_SHORT_EXEMPT)

        Raises:
            ValueError: If the side cannot be normalized to BUY or SELL

        Note:
            Subclasses can override this method to support different side normalization rules.
        """
        if side in (Side.BUY, Side.BUY_MINUS):
            return Side.BUY
        elif side in (Side.SELL, Side.SELL_PLUS, Side.SELL_SHORT, Side.SELL_SHORT_EXEMPT):
            return Side.SELL
        elif side in (Side.CROSS, Side.CROSS_SHORT):
            return Side.CROSS
        else:
            raise ValueError(f"Cannot normalize side: {side}")

    def to_market_data(self, include_hidden: bool = False, exclude_pegged: bool = False) -> Level2MarketData:
        """
        Generate a Level2MarketData object from the current order book state.

        Args:
            include_hidden: If False (default), respects visible_quantity:
                           - Orders with visible_quantity=0 are excluded
                           - Orders with visible_quantity>0 contribute only visible_quantity
                           - Orders with visible_quantity=None contribute full quantity
                           If True, all orders contribute their full quantity regardless of visible_quantity
            exclude_pegged: If True ignore PEGGED

        Returns:
            Level2MarketData object representing the current order book

        Note:
            - Orders without price, quantity, or side are ignored
            - BUY/BUY_MINUS orders create bid quantities
            - SELL/SELL_PLUS/SELL_SHORT/SELL_SHORT_EXEMPT orders create ask quantities
            - Quantities are aggregated at each price level
            - Sides that cannot be normalized are skipped
        """
        md = Level2MarketData()

        # Dictionary to aggregate quantities and order counts by price
        # price -> {'bid': Decimal, 'ask': Decimal, 'bid_numorders': int, 'ask_numorders': int}
        aggregated = {}

        for child_order in self.child_orders.values():
            # Skip orders without required fields
            if child_order.price is None or child_order.quantity is None or child_order.side is None:
                continue

            if exclude_pegged and child_order.ordtype == OrdType.PEGGED:
                continue

            # Normalize the side to BUY or SELL
            try:
                normalized_side = self.normalize_side(child_order.side)
            except ValueError:
                # Skip sides that cannot be normalized
                continue

            # Determine the quantity to contribute based on include_hidden and visible_quantity
            if include_hidden:
                # Include all orders with their full quantity
                qty_to_add = child_order.leaves_quantity
            else:
                # Respect visible_quantity
                if child_order.visible_quantity is not None:
                    # If visible_quantity is 0, skip this order
                    if child_order.visible_quantity == 0:
                        continue
                    # Use visible_quantity if it's set and non-zero
                    qty_to_add = min(child_order.visible_quantity, child_order.leaves_quantity)
                else:
                    # visible_quantity is None, use full quantity
                    qty_to_add = child_order.leaves_quantity

            display_price = child_order.display_price if child_order.display_price is not None else child_order.price

            # Initialize price level if not exists
            if display_price not in aggregated:
                aggregated[display_price] = {
                    'bid': Decimal("0"),
                    'ask': Decimal("0"),
                    'bid_numorders': 0,
                    'ask_numorders': 0
                }

            # Add to appropriate side
            if normalized_side == Side.BUY:
                aggregated[display_price]['bid'] += qty_to_add
                aggregated[display_price]['bid_numorders'] += 1
            else:  # normalized_side == Side.SELL:
                aggregated[display_price]['ask'] += qty_to_add
                aggregated[display_price]['ask_numorders'] += 1

        # Convert aggregated data to PriceLevels and add to market data
        for price, qtys in aggregated.items():
            bid_qty = qtys['bid'] if qtys['bid'] > 0 else None
            ask_qty = qtys['ask'] if qtys['ask'] > 0 else None
            bid_numorders = qtys['bid_numorders'] if qtys['bid_numorders'] > 0 else None
            ask_numorders = qtys['ask_numorders'] if qtys['ask_numorders'] > 0 else None

            level = PriceLevel(
                price=price,
                bid_qty=bid_qty,
                ask_qty=ask_qty,
                bid_numorders=bid_numorders,
                ask_numorders=ask_numorders
            )
            md.add_level(level)

        return md

    def enable_market_data_tracking(self) -> None:
        """Enable real-time market data tracking."""
        self._market_data_tracking_enabled = True
        self._tracked_market_data = Level2MarketData()

    def disable_market_data_tracking(self) -> None:
        """Disable real-time market data tracking and clear tracked data."""
        self._market_data_tracking_enabled = False
        self._tracked_market_data = None

    def is_market_data_tracking_enabled(self) -> bool:
        """Check if market data tracking is enabled."""
        return self._market_data_tracking_enabled

    def get_tracked_market_data(self) -> Optional[Level2MarketData]:
        """
        Get the tracked market data.

        Returns:
            Level2MarketData if tracking is enabled, None otherwise
        """
        return self._tracked_market_data

    def _update_tracked_market_data_add(self, child_order: "ChildOrder") -> None:
        """Update tracked market data when an order is added."""
        if not self._market_data_tracking_enabled or self._tracked_market_data is None:
            return

        # Skip orders without required fields
        if child_order.price is None or child_order.quantity is None or child_order.side is None:
            return

        # Normalize the side
        try:
            normalized_side = self.normalize_side(child_order.side)
        except ValueError:
            return

        # Get or create the level
        level = self._tracked_market_data.get_level(child_order.price)
        if level is None:
            level = PriceLevel(price=child_order.price, bid_qty=None, ask_qty=None)

        # Update the appropriate side
        if normalized_side == Side.BUY:
            current_bid = level.bid_qty if level.bid_qty is not None else Decimal("0")
            level.bid_qty = current_bid + child_order.quantity
        else:  # normalized_side == Side.SELL:
            current_ask = level.ask_qty if level.ask_qty is not None else Decimal("0")
            level.ask_qty = current_ask + child_order.quantity

        self._tracked_market_data.add_level(level)

    def _update_tracked_market_data_delete(self, child_order: "ChildOrder") -> None:
        """Update tracked market data when an order is deleted."""
        if not self._market_data_tracking_enabled or self._tracked_market_data is None:
            return

        # Skip orders without required fields
        if child_order.price is None or child_order.quantity is None or child_order.side is None:
            return

        # Normalize the side
        try:
            normalized_side = self.normalize_side(child_order.side)
        except ValueError:
            return

        # Get the level
        level = self._tracked_market_data.get_level(child_order.price)
        if level is None:
            return

        # Update the appropriate side
        if normalized_side == Side.BUY:
            current_bid = level.bid_qty if level.bid_qty is not None else Decimal("0")
            new_bid = current_bid - child_order.quantity
            level.bid_qty = new_bid if new_bid > 0 else None
        else: # normalized_side == Side.SELL:
            current_ask = level.ask_qty if level.ask_qty is not None else Decimal("0")
            new_ask = current_ask - child_order.quantity
            level.ask_qty = new_ask if new_ask > 0 else None

        self._tracked_market_data.add_level(level)

    def on_child_order_added(self, child_order: "ChildOrder") -> None:
        """Called when a ChildOrder is added to this OrderBook."""
        child_order.link_to("order_book", self)
        child_order.link_to("instrument", self.instrument)
        self._update_tracked_market_data_add(child_order)
        self.mark_dirty()

        # Add to instrument's aggregated child_orders if not already present
        if child_order.key not in self.instrument.instrument_child_orders:
            self.instrument.instrument_child_orders[child_order.key] = child_order

        # Add to exchange's aggregated child_orders if instrument is linked to an exchange
        for instruments_collection in self.instrument._member_of.get("instruments", []):
            exchange = instruments_collection.owner
            if exchange is not None and hasattr(exchange, "exchange_child_orders"):
                if child_order.key not in exchange.exchange_child_orders:
                    exchange.exchange_child_orders[child_order.key] = child_order

    def on_child_order_deleted(self, child_order: "ChildOrder") -> None:
        """Called when a ChildOrder is deleted from this OrderBook."""
        self._update_tracked_market_data_delete(child_order)
        self.mark_dirty()

        # Only remove from instrument's aggregated collection if order is not in any other order book
        # The callback is called AFTER removal from this collection, so if _member_of["child_orders"]
        # is empty or doesn't exist, the order is not in any other order book's child_orders
        child_orders_memberships = child_order._member_of.get("child_orders", [])
        if not child_orders_memberships:
            # Order is not in any order book's child_orders, remove from instrument
            if child_order.key in self.instrument.instrument_child_orders:
                del self.instrument.instrument_child_orders[child_order.key]

            # Also remove from exchange's aggregated child_orders if instrument is linked to an exchange
            for instruments_collection in self.instrument._member_of.get("instruments", []):
                exchange = instruments_collection.owner
                if exchange is not None and hasattr(exchange, "exchange_child_orders"):
                    if child_order.key in exchange.exchange_child_orders:
                        del exchange.exchange_child_orders[child_order.key]

    def on_child_order_replaced(self, old_child_order: "ChildOrder", new_child_order: "ChildOrder") -> None:
        """Called when a ChildOrder is replaced (same key) in this OrderBook."""
        new_child_order.link_to("order_book", self)
        self.mark_dirty()

    def signature(self, structure_only: bool = False) -> str:
        """
        Return a string signature representing the current order book state.

        If market data tracking is enabled, uses the tracked market data.
        Otherwise, converts the current order book to market data and gets the signature.

        Args:
            structure_only: If False (default), format includes prices and quantities.
                           If True, format shows only structure using numorders.

        Returns:
            String signature of the order book's market data state
        """
        if self._market_data_tracking_enabled and self._tracked_market_data is not None:
            # Use tracked market data
            return self._tracked_market_data.signature(structure_only=structure_only)
        else:
            # Convert order book to market data and get signature
            md = self.to_market_data(include_hidden=True)
            return md.signature(structure_only=structure_only)

    def print_contents(self) -> str:
        """
        Print the contents of the order book in a human-readable format.

        Returns:
            String representation of all child orders in the order book
        """
        lines = []
        lines.append(f"OrderBook: {self.instrument.key}{'[' + self.key + ']' if self.key != '' else ''} - {len(self.child_orders)} orders")

        level2_str = f"Level2: {self.signature()} session={self.instrument.status.session}"
        if self.instrument.status.external_nbb:
            level2_str += f" nbb={self.instrument.status.external_nbb}"
        if self.instrument.status.external_nbo:
            level2_str += f" nbo={self.instrument.status.external_nbo}"
        lines.append(level2_str)

        for order_key, order in self.child_orders.items():
            order_str = (f" {order_key} memo={order.memo} side={order.side.name if order.side else None}"
                f" price={order.price} quantity={order.quantity}")
            if order.ordtype:
                order_str += f" type={order.ordtype.name}"
            if order.tif:
                order_str += f" tif={order.tif.name}"
            if order.visible_quantity is not None:
                order_str += f" visQty={order.visible_quantity}"
            if order.leaves_quantity != order.quantity:
                order_str += f" leavesQty={order.leaves_quantity}"
            if order.cumulative_quantity != 0:
                order_str += f" cumQty={order.cumulative_quantity}"
            if order.rank_price and order.rank_price != order.price:
                order_str += f" rprice={order.rank_price}"
            if order.display_price and order.display_price != order.price:
                order_str += f" dprice={order.display_price}"
            if order.peg_offset_value:
                order_str += f" peg_offset_value={order.peg_offset_value}"
            if order.min_quantity:
                order_str += f" min_qty={order.min_quantity}"
            if order.timestamp:
                order_str += f" ts={order.timestamp}"

            lines.append(order_str)
        return "\n".join(lines)

    def check_orders_priority(
        self,
        keys: Set[str],
        comparison_func = None,
        excluded_other_keys: Dict[str, str] = None,
        subset_of_other_keys: Set[str] = None
    ) -> List[OrderBookPriorityComparisonResultEntry]:
        """
        Check the priority order of child orders specified by their keys.

        Compares each order in the keys list against all other orders on the same normalized
        side (buy against buy, sell against sell).

        Args:
            keys: List of child order keys to check in sequence
            comparison_func: Optional comparison function that takes two ChildOrder objects
                           and returns OrderBookPriorityComparisonResultEntry. If None, uses
                           is_first_order_has_higher_priority_default.
            excluded_other_keys: Optional dictionary mapping resting order keys to exclusion reasons.
                         If a resting order's key is in this dict and comparison_func returns
                         False, the result is overridden to True with the specified reason.
            subset_of_other_keys: Optional set of order keys to limit comparison to.
                         If specified, only other orders whose keys are in this set will be
                         used for comparison.

        Returns:
            List of OrderBookPriorityComparisonResultEntry objects, where each entry contains:
            - has_higher_priority: True if first order has higher priority, False otherwise
            - reason: String explaining the priority determination
            Empty list if keys is empty.

        Raises:
            KeyError: If any key is not found in child_orders
        """
        if comparison_func is None:
            comparison_func = is_first_order_has_higher_priority_default

        if excluded_other_keys is None:
            excluded_other_keys = {}

        # Empty keys list returns empty results
        if not keys:
            return []

        # Get all orders in keys and verify they exist
        key_orders = []
        for key in keys:
            key_orders.append(self.child_orders[key])

        # Compare each key order with all other orders on the same normalized side
        results = []
        keys_set = set(keys)

        for key_order in key_orders:
            # Skip orders without side
            if key_order.side is None:
                continue

            # Get normalized side for this order
            try:
                key_normalized_side = OrderBook.normalize_side(key_order.side)
            except ValueError:
                # Skip orders with sides that cannot be normalized
                continue

            # Find all other orders (not in keys) with the same normalized side
            for other_key, other_order in self.child_orders.items():
                # Skip orders that are in the keys list
                if other_key in keys_set:
                    continue

                # Skip orders not in subset_of_other_keys if specified
                if subset_of_other_keys is not None and other_key not in subset_of_other_keys:
                    continue

                # Skip orders without side
                if other_order.side is None:
                    continue

                # Check if normalized side matches
                try:
                    other_normalized_side = OrderBook.normalize_side(other_order.side)
                except ValueError:
                    # Skip orders with sides that cannot be normalized
                    continue

                # Compare if they have the same normalized side
                if key_normalized_side == other_normalized_side:
                    result = comparison_func(key_order, other_order)
                    result.key1 = key_order.key
                    result.key2 = other_key

                    # Check if resting order is excluded and comparison failed
                    if not result.has_higher_priority and other_key in excluded_other_keys:
                        result.has_higher_priority = True
                        result.reason += " " + excluded_other_keys[other_key]

                    results.append(result)

        return results


    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "key": self.key,
            "instrument_key": self.instrument.key,
            "child_orders": [order.to_dict() for order in self.child_orders.values()],
        }


def is_first_order_has_higher_priority_error(_order1: ChildOrder, _order2: ChildOrder) -> OrderBookPriorityComparisonResultEntry:
    return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Error")

def _calculate_rank_price(order: ChildOrder) -> tuple[Optional[Decimal], str]:
    """
    Calculate the rank price for an order.

    For PEGGED orders: uses midpoint of NBBO (if both bid and ask are not None and market is well-formed)
    For all other order types: uses order price

    Args:
        order: The ChildOrder to calculate rank price for

    Returns:
        tuple[Optional[Decimal], str]: (rank_price, reason)
        - rank_price: The calculated rank price, or None if it cannot be calculated
        - reason: A string explaining how the rank price was calculated
    """
    # For PEGGED orders, try to calculate midpoint from NBBO
    if order.ordtype == OrdType.PEGGED:
        # Try to get instrument and NBBO
        if hasattr(order, 'instrument') and order.instrument is not None:
            instrument = order.instrument
            if hasattr(instrument, 'status') and instrument.status is not None:
                nbb = instrument.status.external_nbb
                nbo = instrument.status.external_nbo

                # Check if market is well-formed (both not None and nbb <= nbo)
                if nbb is not None and nbo is not None and nbb <= nbo:
                    # Calculate midpoint
                    midpoint = (nbb + nbo) / Decimal("2")
                    return (midpoint, f"PEGGED order: NBBO midpoint ({nbb} + {nbo}) / 2 = {midpoint}")

        # If we can't get NBBO midpoint for PEGGED order, fall back to order price
        return (order.price, f"PEGGED order: fallback to order price {order.price} (NBBO unavailable)")


    if order.rank_price is not None:
        # For all other order types, use order price
        ordtype_name = order.ordtype.name if order.ordtype else "None"
        return (order.rank_price, f"{ordtype_name} order: using order price {order.rank_price}")

    # For all other order types, use order price
    ordtype_name = order.ordtype.name if order.ordtype else "None"
    return (order.price, f"{ordtype_name} order: using order price {order.price}")

def is_first_order_has_higher_priority_default(order1: ChildOrder, order2: ChildOrder) -> OrderBookPriorityComparisonResultEntry:
    """
    Determine if order1 has higher priority than order2.

    Priority rules (in order):
    1. Market orders (no rank_price) have priority over limit orders (with rank_price)
    2. Buy orders: Higher rank_price has priority
    3. Sell orders: Lower rank_price has priority
    4. Orders with visible_quantity that is non-zero or None have priority over orders with visible_quantity=0
    5. If rank_prices are equal: Earlier timestamp has priority
    6. If timestamps are equal: Lexicographically smaller key has priority

    Note on rank_price:
    - For PEGGED orders: rank_price is the midpoint of NBBO (if market is well-formed)
    - For all other order types: rank_price is the order price

    Args:
        order1: First ChildOrder to compare
        order2: Second ChildOrder to compare

    Returns:
        OrderBookPriorityComparisonResultEntry with has_higher_priority and reason

    Raises:
        ValueError: If sides are different or not specified, or cannot be normalized
    """

    # Check if side is None
    if order1.side is None or order2.side is None: # pragma: no cover - blocked upstream
        raise ValueError("Orders must have side specified to compare priority")

    # Normalize the sides
    normalized_side1 = OrderBook.normalize_side(order1.side)
    normalized_side2 = OrderBook.normalize_side(order2.side)

    # Check if normalized sides are different
    if normalized_side1 != normalized_side2: # pragma: no cover - blocked upstream
        raise ValueError(f"Orders have different normalized sides: {normalized_side1.name} vs {normalized_side2.name}")

    # Calculate rank prices for both orders
    rank_price1, rank_price1_reason = _calculate_rank_price(order1)
    rank_price2, rank_price2_reason = _calculate_rank_price(order2)

    # Check market vs limit order priority (absent rank_price = market order has higher priority)
    order1_is_market = rank_price1 is None
    order2_is_market = rank_price2 is None

    if order1_is_market and not order2_is_market:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Market")
    elif not order1_is_market and order2_is_market:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=False, reason="Market")

    # Check price priority based on normalized side (only if both have rank prices)
    if rank_price1 is not None and rank_price2 is not None:
        if normalized_side1 == Side.BUY:
            if rank_price1 > rank_price2:
                return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Price")
            elif rank_price1 < rank_price2:
                return OrderBookPriorityComparisonResultEntry(has_higher_priority=False, reason="Price")
        else: #  normalized_side1 == Side.SELL
            if rank_price1 < rank_price2:
                return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Price")
            elif rank_price1 > rank_price2:
                return OrderBookPriorityComparisonResultEntry(has_higher_priority=False, reason="Price")

    # Check visibility priority (visible_quantity=0 has lower priority)
    order1_visible = order1.visible_quantity is None or order1.visible_quantity != 0
    order2_visible = order2.visible_quantity is None or order2.visible_quantity != 0

    if order1_visible and not order2_visible:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Visibility")
    elif not order1_visible and order2_visible:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=False, reason="Visibility")

    # Prices are equal or missing, check timestamp
    if order1.timestamp is None or order2.timestamp is None:
        raise ValueError("Orders must have timestamp specified to compare priority")

    if order1.timestamp < order2.timestamp:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="Time")
    elif order1.timestamp > order2.timestamp:
        return OrderBookPriorityComparisonResultEntry(has_higher_priority=False, reason="Time")

    return OrderBookPriorityComparisonResultEntry(has_higher_priority=True, reason="None")
