from __future__ import annotations
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Set, Iterable

from .model_base import ModelState, ModelCollection, ModelTransitionAudit, ModelCleanUpEffect
from .downstream_effects import (
    OrderAcceptedEffect,
    OrderCanceledEffect,
    OrderReplacedEffect,
    OrderExecutedEffect,
    TradeEffect,
    InstrumentStatusEffect,
    CreateInstrumentEffect,
    IcebergReplenishmentExtraChildOrder,
)
from .orders import ParentOrder, ChildOrder
from .instruments import OrderBook, Instrument, InstrumentConfiguration
from .enums import CancelReason, TimeInForce, OrdStatus, LastLiquidityInd, IcebergTradeMode
from .trades import Trade, TradeSide
from ..base.system_effects import TradingSessionEffect

if TYPE_CHECKING:  # pragma: no cover
    from .instruments import Instrument
    from .model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import (
    ReportedRuleData,
    report_rule_for_state_transition
)


class ExchangeConfiguration:
    """
    Configuration settings for a ModelExchange.

    Attributes:
        enable_consistency_check: Whether to enable consistency checking for this exchange (default: True)
        crash_on_exceptions: Whether to raise exceptions on book builder errors (default: True)
    """

    def __init__(
        self,
        enable_consistency_check: bool = True,
        crash_on_exceptions: bool = True,
    ) -> None:
        self.enable_consistency_check = enable_consistency_check
        self.crash_on_exceptions = crash_on_exceptions


class ExchangeTransitionAudit(ModelTransitionAudit):
    """
    Exchange-specific transition audit.

    Represents the result/audit of applying a state transition to a ModelExchange.
    Contains information about affected order books, order keys, and their states
    before and after the transition.

    Attributes:
        affected_child_order_keys: Set of order key affected by the transition
        resting_child_order_keys: Set of order keys that existed before the transition
        non_resting_child_order_keys: that will not stay in the order book after the transaction
        executed_child_order_keys: Set of order keys affected by OrderExecutedEffect
        executed_child_order_executed_quantity: Volumes executed during the transition
        canceled_by_stp_child_order_keys: Set of order keys canceled due to self-trade prevention
        new_child_order_keys: Set of new order keys (from AcceptedEffect or ReplacedEffect)
        trades: Dictionary of trades created during the transition, keyed by trade match ID
    """

    def __init__(self) -> None:
        super().__init__()
        # Order key -> Set of affected OrderBooks
        self.affected_child_order_keys: Set[str] = set()
        self.affected_order_books: Set[OrderBook] = set()
        self.affected_instruments: Set[Instrument] = set()

        # Keys that were already present in exchange_child_orders before the transition
        self.resting_child_order_keys: Set[str] = set()
        # Keys that will not stay in the order book after the transaction
        self.non_resting_child_order_keys: Set[str] = set()
        # Keys affected by OrderExecutedEffect
        self.executed_child_order_keys: Set[str] = set()
        self.executed_child_order_executed_quantity: Dict[str, Decimal] = {}
        # Keys canceled due to self-trade prevention
        self.canceled_by_stp_child_order_keys: Set[str] = set()
        # Keys that are new (from AcceptedEffect or new_key in ReplacedEffect)
        self.new_child_order_keys: Set[str] = set()
        # Trades created during the transition
        self.trades: Dict[str, Trade] = {}

        self.testcases: Set[str] = set()
        self.last_transition = ""
        self.affected_underlying: Set[Instrument] = set()

        self.transition_exceptions: List[ReportedRuleData] = []
        self.transition_observations: List[ReportedRuleData] = []

class ModelExchange(ModelState):
    """
    Top-level container for the digital twin of an exchange / venue / environment.

    According to the spec:
    - ModelExchange will contain all these collections except OrderBook.

    So we expose:
        instruments          -> Instrument
        parent_orders        -> ParentOrder
        child_orders         -> ChildOrder
        trades               -> Trade
        instrument_groups    -> InstrumentGroup
        users                -> User
        user_groups          -> UserGroup

    We intentionally DO NOT create an order_books collection here.
    """

    def __init__(
        self,
        key: str,
        crash_on_exceptions: bool = True,  # Deprecated: use configuration.crash_on_exceptions
        configuration: Optional[ExchangeConfiguration] = None,
    ) -> None:
        super().__init__(key)

        if configuration:
            self.configuration = configuration
        else:
            self.configuration = ExchangeConfiguration()
            # For backward compatibility, override configuration if crash_on_exceptions is explicitly passed
            self.configuration.crash_on_exceptions = crash_on_exceptions

        self.trading_session = ""

        self.instruments = ModelCollection(name="instruments", owner=self)
        self.parent_orders = ModelCollection(name="parent_orders", owner=self)

        self.exchange_child_orders = ModelCollection(name="exchange_child_orders", owner=self)
        self.trades = ModelCollection(name="trades", owner=self)
        self.instrument_groups = ModelCollection(name="instrument_groups", owner=self)
        self.users = ModelCollection(name="users", owner=self)
        self.user_groups = ModelCollection(name="user_groups", owner=self)

        # Alias registry: {symbology: {symbol: instrument}}
        # e.g., {"RIC": {"AAPL.O": <Instrument AAPL>}}
        self._alias_registry: dict[str, dict[str, "Instrument"]] = {}

    def on_instrument_added(self, instrument: "Instrument") -> None:
        """Called when an Instrument is added to this ModelExchange."""
        instrument.link_to("exchange", self)

        # Register any existing aliases the instrument already has
        for symbology, symbol in instrument._aliases.items():
            self._register_alias(symbology, symbol, instrument)

    def get_instrument_by_symbol(self, symbol: str, symbology: Optional[str] = None) -> Optional["Instrument"]:
        """
        Get an instrument by symbol and optional symbology.

        If symbology is None, searches in the default instruments collection using the symbol as the key.
        Otherwise, searches in the aliases dictionary for the given symbology.

        Args:
            symbol: The symbol to search for
            symbology: The symbology type (e.g., "RIC", "ISIN", "NasdaqSymbol").
                      If None, uses the default instruments collection.

        Returns:
            The Instrument if found, None otherwise
        """
        if symbology is None:
            # Use default instruments collection
            return self.instruments.get(symbol)
        else:
            # Look up in alias registry
            if symbology in self._alias_registry:
                return self._alias_registry[symbology].get(symbol)
            return None

    def _register_alias(self, symbology: str, symbol: str, instrument: "Instrument") -> None:
        """
        Internal method to register an alias in the exchange registry.

        Args:
            symbology: The symbology type
            symbol: The symbol value
            instrument: The instrument to associate with this alias
        """
        if symbology not in self._alias_registry:
            self._alias_registry[symbology] = {}
        self._alias_registry[symbology][symbol] = instrument

    def _unregister_alias(self, symbology: str, symbol: str) -> None:
        """
        Internal method to unregister an alias from the exchange registry.

        Args:
            symbology: The symbology type
            symbol: The symbol value to remove
        """
        if symbology in self._alias_registry:
            self._alias_registry[symbology].pop(symbol, None)

    def transition(self, state_transition: "ModelStateTransition") -> ExchangeTransitionAudit:
        """
        Apply a state transition to this exchange.

        This method processes the input signal contained in the ModelStateTransition
        and updates the exchange state accordingly. It handles downstream effects
        such as order acceptance, cancellation, replacement, and execution.

        The processing order is:
        1. Call _pre_* for all downstream effects (populates audit with affected order books)
        2. Call _apply_* for all downstream effects
        3. Call _post_* for all downstream effects

        Args:
            state_transition: The ModelStateTransition object containing the input
                            signal and any downstream effects to apply.

        Returns:
            ExchangeTransitionAudit object containing audit information about the transition.
        """
        effects = state_transition.downstream_effects
        self._current_audit = ExchangeTransitionAudit()
        self._state_transition = state_transition

        # Phase 1: Pre-processing for effects that need it
        for effect in effects:
            if isinstance(effect, OrderExecutedEffect):
                self._pre_order_executed(effect)

        # Phase 2: Apply all effects
        for effect in effects:
            if isinstance(effect, OrderAcceptedEffect):
                self._apply_order_accepted(effect)
            elif isinstance(effect, OrderCanceledEffect):
                self._apply_order_canceled(effect)
            elif isinstance(effect, OrderReplacedEffect):
                self._apply_order_replaced(effect)
            elif isinstance(effect, OrderExecutedEffect):
                self._apply_order_executed(effect)
            elif isinstance(effect, TradeEffect):
                self._apply_trade(effect)
            elif isinstance(effect, InstrumentStatusEffect):
                self._apply_instrument_status(effect)
            elif isinstance(effect, CreateInstrumentEffect):
                self._apply_create_instrument(effect)
            elif isinstance(effect, IcebergReplenishmentExtraChildOrder):
                self._apply_iceberg_replenishment_extra_child_order(effect)
            elif isinstance(effect, ModelCleanUpEffect):
                self._apply_clean_up(effect)
            elif isinstance(effect, TradingSessionEffect):
                self._apply_trading_session(effect)

        # Phase 3: Post-processing for effects that need it
        for effect in effects:
            if isinstance(effect, OrderReplacedEffect):
                self._post_order_replaced(effect)
            elif isinstance(effect, OrderExecutedEffect):
                self._post_order_executed(effect)

        self._current_audit.resting_child_order_keys = self._current_audit.affected_child_order_keys - self._current_audit.new_child_order_keys

        for trade in self._current_audit.trades.values():
            for trade_side in trade.trade_sides:
                if trade_side.order_key is None:
                    expected_last_liquidity_indicator = LastLiquidityInd.NEITHER
                elif trade_side.order_key in self._current_audit.resting_child_order_keys:
                    expected_last_liquidity_indicator = LastLiquidityInd.ADDED
                else:
                    expected_last_liquidity_indicator = LastLiquidityInd.REMOVED

                if trade_side.last_liquidity_indicator == LastLiquidityInd.NEITHER:
                    trade_side.last_liquidity_indicator = expected_last_liquidity_indicator
                else:
                    if expected_last_liquidity_indicator != trade_side.last_liquidity_indicator:
                        if self.configuration.enable_consistency_check:
                            self.report_book_builder_error(
                                f"Inconsistent LastLiquidityIndicator {expected_last_liquidity_indicator} {trade_side.last_liquidity_indicator}", id=trade.key)

                if trade_side.last_liquidity_indicator == LastLiquidityInd.ADDED:
                    if (trade_side.observed_iceberg_trade_mode == IcebergTradeMode.HIDDEN
                            and trade_side.iceberg_trade_mode not in [IcebergTradeMode.HIDDEN, IcebergTradeMode.UNDERWATER]):
                        self.report_book_builder_error(
                            f"Inconsistent IcebergTradeMode {trade_side.observed_iceberg_trade_mode} {trade_side.iceberg_trade_mode}",
                            id=trade.key)

                    if (trade_side.observed_iceberg_trade_mode not in [IcebergTradeMode.HIDDEN, IcebergTradeMode.UNDEFINED]
                            and trade_side.iceberg_trade_mode in [IcebergTradeMode.HIDDEN, IcebergTradeMode.UNDERWATER]):
                        self.report_book_builder_error(
                            f"Inconsistent IcebergTradeMode {trade_side.observed_iceberg_trade_mode} {trade_side.iceberg_trade_mode}",
                            id=trade.key)

        for order_book in self._current_audit.affected_order_books:
            self._current_audit.affected_instruments.add(order_book.instrument)
            self._current_audit.affected_underlying.add(order_book.instrument.underlying)

        for instrument in self._current_audit.affected_instruments:
            instrument.status.refresh_status()

        audit = self._current_audit
        self._current_audit = None

        return audit

    def report_book_builder_error(self, annotation, id=""):
        self._current_audit.transition_exceptions.append(
            report_rule_for_state_transition(self._state_transition, annotation,
                False, id=id)
        )
        if self.configuration.crash_on_exceptions:
            raise Exception(f"report_book_builder_error {annotation}")

    def report_observation(self, annotation, status=True, id=""):
        self._current_audit.transition_observations.append(
            report_rule_for_state_transition(self._state_transition, annotation,
                status, id=id)
        )

    def create_child_order(self, parent_order: ParentOrder, effect: OrderAcceptedEffect) -> ChildOrder:
        # Create child order with attributes from effect

        if effect.quantity is not None:
            quantity = effect.quantity
        elif effect.leaves_quantity is not None:
            quantity = (self._current_audit.executed_child_order_executed_quantity.get(effect.key, Decimal(0))
                + effect.leaves_quantity)

        return ChildOrder(
            key=effect.key,
            parent=parent_order,
            price=effect.price,
            quantity=quantity,
            side=effect.side,
            timestamp=effect.timestamp,
            ordtype=effect.ordtype,
            visible_quantity=effect.visible_quantity,
            tif=effect.tif,
            memo=effect.memo,
            testcase=effect.testcase,
            order_status=effect.order_status,
            ready=False,
        )

    def _apply_order_accepted(self, effect: "OrderAcceptedEffect") -> None:
        """
        Apply an OrderAddedEffect to the exchange state.

        Creates a ChildOrder from the effect attributes and adds it to the
        specified order books of the instrument. If book_names is None or empty,
        adds to the default order book.

        The ParentOrder is created if it doesn't exist.
        """
        self._current_audit.testcases.add(effect.testcase)

        # Get or create parent order
        parent_order = self.parent_orders.get(effect.parent_order_key)
        if parent_order is None:
            parent_order = ParentOrder(effect.parent_order_key)
            self.parent_orders[effect.parent_order_key] = parent_order

        # Create child order with attributes from effect
        child_order = self.create_child_order(parent_order, effect)
        self._current_audit.affected_child_order_keys.add(child_order.key)
        self._current_audit.new_child_order_keys.add(child_order.key)

        if effect.order_status is not None and effect.order_status in [
            OrdStatus.CANCELED, OrdStatus.EXPIRED, OrdStatus.FILLED
        ]:
            self._current_audit.non_resting_child_order_keys.add(child_order.key)

        # Set additional attributes
        if effect.peg_offset_value is not None:
            child_order.set_peg_offset_value(effect.peg_offset_value)
        if effect.display_price is not None:
            child_order.set_display_price(effect.display_price)
        if effect.rank_price is not None:
            child_order.set_rank_price(effect.rank_price)
        if effect.peg_price_type is not None:
            child_order.set_peg_price_type(effect.peg_price_type)
        if effect.min_quantity is not None:
            child_order.set_min_quantity(effect.min_quantity)
        if effect.display_method is not None:
            child_order.set_display_method(effect.display_method)
        if effect.display_quantity is not None:
            child_order.set_display_quantity(effect.display_quantity)

        child_order.mark_ready()

        # Add child order to exchange_child_orders collection
        self.exchange_child_orders[child_order.key] = child_order

        # Add to order books
        instrument = self.instruments[effect.instrument_key]
        book_names = effect.book_names

        if book_names:
            for book_name in book_names:
                if book_name in instrument.order_books:
                    order_book = instrument.order_books[book_name]
                    order_book.child_orders[child_order.key] = child_order
                    self._current_audit.affected_order_books.add(order_book)
        else:
            default_book = instrument.get_default_order_book()
            if default_book is not None:
                default_book.child_orders[child_order.key] = child_order
                self._current_audit.affected_order_books.add(default_book)

    def _apply_order_canceled(self, effect: "OrderCanceledEffect") -> None:
        """
        Apply an OrderCanceledEffect to the exchange state.

        Removes the child order from all order books it belongs to.
        If parent_order_key is provided, cancels all child orders associated
        with that parent order.
        """
        if effect.parent_order_key is not None:
            # Cancel all child orders associated with the parent order
            self._cancel_by_parent_order_key(effect)
        else:
            # Cancel single child order by key
            self._cancel_single_order(effect)

    def _cancel_single_order_by_order(self, child_order: ChildOrder) -> None:
        self._current_audit.testcases.add(child_order.testcase)

        self._current_audit.affected_child_order_keys.add(child_order.key)
        self._current_audit.resting_child_order_keys.add(child_order.key)

        self._add_to_affected_order_books(child_order)
        self._remove_from_order_books(child_order)

    def _cancel_single_order(self, effect: "OrderCanceledEffect") -> None:
        """Cancel a single child order by its key."""
        if effect.key not in self.exchange_child_orders:
            self.report_book_builder_error("OrderCanceled key not found", id=effect.key)
            return

        child_order = self.exchange_child_orders[effect.key]
        self._cancel_single_order_by_order(child_order)

        if effect.reason == CancelReason.SELF_TRADE_PREVENTION:
            self._current_audit.canceled_by_stp_child_order_keys.add(effect.key)

    def _cancel_by_parent_order_key(self, effect: "OrderCanceledEffect") -> None:
        """Cancel all child orders associated with a parent order."""
        parent_order = self.parent_orders.get(effect.parent_order_key)
        if parent_order is None:
            self.report_book_builder_error("OrderCanceled parent_order_key not found", id=effect.parent_order_key)
            return

        child_orders_to_cancel = [
            child_order for child_order in parent_order.parent_child_orders.values()
        ]

        for child_order in child_orders_to_cancel:
            self._cancel_single_order_by_order(child_order)

            if effect.reason == CancelReason.SELF_TRADE_PREVENTION:
                self._current_audit.canceled_by_stp_child_order_keys.add(child_order.key)


    def _apply_order_replaced(self, effect: "OrderReplacedEffect") -> None:
        """
        Apply an OrderReplacedEffect to the exchange state.

        Updates the child order with any non-None fields from the effect.
        If new_key is provided, updates the order's key in all collections.
        Removes the order from order books if leaves_quantity becomes 0.
        """

        if effect.parent_order_key is not None:
            if effect.parent_order_key not in self.parent_orders:
                self.report_book_builder_error("OrderReplaced parent key not found", id=effect.parent_order_key)
                return

            parent_order = self.parent_orders[effect.parent_order_key]

            iceberg_strategy_root_child_order = None
            for child_order in parent_order.parent_child_orders.values():
                if child_order.iceberg_strategy_root_child_order is not None:
                    iceberg_strategy_root_child_order = child_order

            if iceberg_strategy_root_child_order is not None:
                self._make_parent_order_one_child(parent_order)

            if len(parent_order.parent_child_orders) != 1:
                self.report_book_builder_error("Only one child order is present for replacement by parent key", id=effect.key)
            key = parent_order.parent_child_orders.get_default_node().key
        else:
            key = effect.key

        if key not in self.exchange_child_orders:
            self.report_book_builder_error("OrderReplaced key not found", id=key)
            return

        child_order = self.exchange_child_orders.get(key)
        parent_order = child_order.parent_order
        self._current_audit.testcases.add(child_order.testcase)

        amend_str = ""

        self._current_audit.affected_child_order_keys.add(child_order.key)
        self._current_audit.new_child_order_keys.add(child_order.key)

        # Handle key change if new_key is provided
        if effect.new_key is not None:
            self._current_audit.affected_child_order_keys.add(effect.new_key)
            self._current_audit.new_child_order_keys.add(effect.new_key)
            child_order.change_key(effect.new_key)

        # Build kwargs for amend with only non-None values
        amend_kwargs = {}

        if effect.price is not None:
            amend_kwargs["price"] = effect.price
            if child_order.price != effect.price:
                amend_str += f" price"
        if effect.quantity is not None:
            if effect.quantity_sign == "+":
                new_quantity = child_order.quantity + effect.quantity
            elif effect.quantity_sign == "-":
                new_quantity = child_order.quantity - effect.quantity
            else:
                new_quantity = effect.quantity
            amend_kwargs["quantity"] = new_quantity

            if child_order.quantity > new_quantity:
                amend_str += f" decrease quantity"
            if child_order.quantity < new_quantity:
                amend_str += f" increase quantity"

        elif effect.leaves_quantity is not None:
            amend_kwargs["quantity"] = child_order.cumulative_quantity + effect.leaves_quantity
            new_quantity = child_order.cumulative_quantity + effect.leaves_quantity
            if child_order.quantity > new_quantity:
                amend_str += f" decrease quantity"
            if child_order.quantity < new_quantity:
                amend_str += f" increase quantity"

        if effect.side is not None:
            amend_kwargs["side"] = effect.side
            if child_order.side != effect.side:
                amend_str += f" side"
        if effect.ordtype is not None:
            amend_kwargs["ordtype"] = effect.ordtype
            if child_order.ordtype != effect.ordtype:
                amend_str += f" ordtype"
        if effect.visible_quantity is not None:
            amend_kwargs["visible_quantity"] = effect.visible_quantity
            if child_order.visible_quantity != effect.visible_quantity:
                amend_str += f" visible_quantity"
        if effect.timestamp is not None:
            amend_kwargs["timestamp"] = effect.timestamp
        if effect.timestamp_override is not None:
            amend_kwargs["timestamp_override"] = effect.timestamp_override
        if effect.peg_offset_value is not None:
            amend_kwargs["peg_offset_value"] = effect.peg_offset_value
            if child_order.peg_offset_value != effect.peg_offset_value:
                amend_str += f" peg_offset_value"
        if effect.peg_price_type is not None:
            amend_kwargs["peg_price_type"] = effect.peg_price_type
            if child_order.peg_price_type != effect.peg_price_type:
                amend_str += f" peg_price_type"
        if effect.min_quantity is not None:
            amend_kwargs["min_quantity"] = effect.min_quantity
            if child_order.min_quantity != effect.min_quantity:
                amend_str += f" min_quantity"
        if effect.display_price is not None:
            amend_kwargs["display_price"] = effect.display_price
            if child_order.display_price != effect.display_price:
                amend_str += f" display_price"
        if effect.rank_price is not None:
            amend_kwargs["rank_price"] = effect.rank_price
            if child_order.rank_price != effect.rank_price:
                amend_str += f" rank_price"

        if effect.new_parent_key is not None:
            if parent_order.key != effect.new_parent_key:
                amend_str += f" parent_key"
                parent_order.change_key(effect.new_parent_key)

        if amend_kwargs:
            child_order.amend(**amend_kwargs)

        if amend_str == "":
            amend_str = " nothing"
        self.report_observation(f"Amended{amend_str}", True, child_order.key)

        self._add_to_affected_order_books(child_order)


        # Handle book_names change if provided
        if effect.book_names is not None:
            # Find the instrument from one of the current order books
            collections = child_order._member_of.get("child_orders", [])
            instrument = None
            for collection in collections:
                if hasattr(collection, 'owner') and hasattr(collection.owner, 'instrument'):
                    instrument = collection.owner.instrument
                    break

            if instrument is not None:
                # Remove from all current order books
                self._remove_from_order_books(child_order)

                # Add to new order books
                for book_name in effect.book_names:
                    if book_name in instrument.order_books:
                        order_book = instrument.order_books[book_name]
                        order_book.child_orders[child_order.key] = child_order
                        self._current_audit.affected_order_books.add(order_book)

    def _apply_order_executed(self, effect: "OrderExecutedEffect") -> None:
        """
        Apply an OrderExecutedEffect to the exchange state.

        Updates the child order's cumulative and leaves quantities.
        Removes the order from order books if leaves_quantity becomes 0.

        For iceberg orders (with visible_quantity):
        - Decrements visible_quantity by the executed quantity
        - If visible_quantity becomes <= 0, resets it to display_quantity
          (capped to leaves_quantity if leaves_quantity < display_quantity)
        - Updates timestamp only when visible_quantity is reset and effect.timestamp is provided

        If trade_match_id is provided, creates or updates a Trade in the audit
        and adds a TradeSide for this execution.
        """
        if effect.key == "":
            return

        if effect.key not in self.exchange_child_orders:
            print(effect.to_dict())
            self.report_book_builder_error("OrderExecuted key not found", id=effect.key)
            return

        child_order = self.exchange_child_orders[effect.key]
        self._current_audit.testcases.add(child_order.testcase)

        self._current_audit.affected_child_order_keys.add(child_order.key)
        self._current_audit.executed_child_order_keys.add(child_order.key)
        self._current_audit.resting_child_order_keys.add(child_order.key)

        price = effect.price
        if price is None:
            price = child_order.price
        quantity = effect.quantity
        if quantity is None:
            quantity = child_order.quantity

        self._add_to_affected_order_books(child_order)

        # Handle trade_match_id - create Trade and TradeSide
        if effect.trade_match_id is not None:
            trade = self.trades.get(effect.trade_match_id)
            if trade is None:
                trade = Trade(effect.trade_match_id, effect.timestamp)
                self.trades[effect.trade_match_id] = trade
            trade_side = TradeSide(
                side=child_order.side,
                price=price,
                quantity=quantity,
                trade=trade,
                session=effect.session,
                testcase=child_order.testcase,
                instrument_key=child_order.instrument.key,
                memo=child_order.memo,
                printable=effect.printable,
                last_liquidity_indicator=effect.last_liquidity_indicator,
                order=child_order,
                observed_iceberg_trade_mode=effect.iceberg_trade_mode,
                contra_broker=effect.contra_broker
            )
            trade.trade_sides.append(trade_side)
            self._current_audit.trades[effect.trade_match_id] = trade

        child_order.execute(price=price, quantity=quantity)

        # Handle visible_quantity for iceberg orders
        visible_quantity_reset = False
        if child_order.visible_quantity is not None:
            # Decrement visible_quantity by executed quantity
            new_visible = child_order.visible_quantity - quantity

            if new_visible <= 0:
                # Reset visible_quantity to display_quantity (capped to leaves_quantity)
                # Opportunity to immediately replenish after every fill
                new_visible = 0

            child_order.set_visible_quantity(new_visible)

        # Update timestamp only when visible_quantity was reset and timestamp is provided
        if visible_quantity_reset and effect.timestamp is not None:
            child_order.set_timestamp(effect.timestamp)

    def _add_to_affected_order_books(self, child_order) -> None:
        """
        Add order books for a child order to affected_books
        """
        collections = child_order._member_of.get("child_orders", [])
        for collection in list(collections):
            if child_order.key in collection:
                self._current_audit.affected_order_books.add(collection.owner)

    def get_order_books_for_child_order_keys(self, keys: Iterable[str]) -> Set[OrderBook]:
        """
        Get the set of all OrderBooks where the given child order keys are located.

        Args:
            keys: An iterable of child order keys

        Returns:
            Set of OrderBook instances containing any of the specified orders
        """
        result: Set[OrderBook] = set()
        for key in keys:
            child_order = self.exchange_child_orders.get(key)
            if child_order is not None:
                collections = child_order._member_of.get("child_orders", [])
                for collection in collections:
                    if hasattr(collection, 'owner') and collection.owner is not None:
                        result.add(collection.owner)
        return result

    def _remove_from_order_books(self, child_order) -> None:
        """
        Remove a child order from all order books it belongs to.
        """
        collections = child_order._member_of.get("child_orders", [])
        for collection in list(collections):
            if child_order.key in collection:
                self._current_audit.affected_order_books.add(collection.owner)
                del collection[child_order.key]
        if child_order.key in child_order.parent_order.parent_child_orders:
            del child_order.parent_order.parent_child_orders[child_order.key]

    def _change_order_key(self, child_order, new_key: str) -> None:
        """
        Change a child order's key in all collections it belongs to.

        Uses the Node.change_key() method to handle the key change properly.
        """
        child_order.change_key(new_key)

    def _pre_order_executed(self, effect: "OrderExecutedEffect") -> None:
        self._current_audit.executed_child_order_executed_quantity[effect.key] = (
            self._current_audit.executed_child_order_executed_quantity.get(effect.key, Decimal(0))
            + effect.quantity)

    def _post_order_replaced(self, effect: "OrderReplacedEffect") -> None:
        child_order = self.exchange_child_orders.get(effect.key)
        if child_order and child_order.leaves_quantity <= 0:
            self._remove_from_order_books(child_order)

    def _post_order_executed(self, effect: "OrderExecutedEffect") -> None:
        child_order = self.exchange_child_orders.get(effect.key)
        if not child_order:
            return

        if child_order.leaves_quantity < 0:
            self.report_book_builder_error("Overfill", id=effect.key)

        # Remove from order books if fully filled
        if child_order.leaves_quantity <= 0:

            hidden_child_order = child_order.iceberg_strategy_root_child_order
            if hidden_child_order is not None:
                hidden_child_order.set_quantity(hidden_child_order.quantity + child_order.quantity)
                hidden_child_order.set_cumulative_quantity(hidden_child_order.cumulative_quantity + child_order.cumulative_quantity)
                self._current_audit.affected_child_order_keys.add(hidden_child_order.key)
                self._add_to_affected_order_books(hidden_child_order)

            self._remove_from_order_books(child_order)
            return

        if child_order.visible_quantity is not None and child_order.visible_quantity <= 0:
            if child_order.display_quantity is not None:
                reset_value = child_order.display_quantity
                # Cap to leaves_quantity if less than display_quantity
                if child_order.leaves_quantity is not None and child_order.leaves_quantity < reset_value:
                    reset_value = child_order.leaves_quantity
                child_order.set_visible_quantity(reset_value, increment_replenishment_counter=True)
                self.report_observation(f"Replenished", True, child_order.key)
                if effect.timestamp is not None:
                    child_order.set_timestamp(effect.timestamp)

    def _apply_trade(self, effect: "TradeEffect") -> None:
        """Apply a TradeEffect to the exchange state. Override in subclasses."""

        # Handle trade_match_id - create Trade and TradeSide
        if effect.trade_match_id is not None:
            trade = self.trades.get(effect.trade_match_id)
            if trade is None:
                trade = Trade(effect.trade_match_id, effect.timestamp)
                self.trades[effect.trade_match_id] = trade

            trade_side = TradeSide(
                side=effect.side,
                price=effect.price,
                quantity=effect.quantity,
                trade=trade,
                session=effect.session,
                testcase=effect.testcase,
                instrument_key=effect.instrument_key,
                memo=effect.memo,
                printable=effect.printable,
                observed_iceberg_trade_mode=IcebergTradeMode.HIDDEN,
                contra_broker=effect.contra_broker
            )
            trade.trade_sides.append(trade_side)
            self._current_audit.trades[effect.trade_match_id] = trade
            self._current_audit.affected_instruments.add(self.instruments[effect.instrument_key])

    def _apply_instrument_status(self, effect: "InstrumentStatusEffect") -> None:
        """
        Apply an InstrumentStatusEffect to the exchange state.

        Updates the instrument's status with session, nbb, and nbo values
        from the effect if they are provided.
        """
        if effect.instrument_key is None:
            return

        instrument = self.instruments.get(effect.instrument_key)
        if instrument is None:
            return

        # Update session if provided
        if effect.session is not None:
            self._current_audit.last_transition = f"{instrument.status.session}->{effect.session}"
            instrument.status.session = effect.session

        # Update external_nbb if provided
        instrument.status.external_nbb = effect.nbb

        # Update external_nbo if provided
        instrument.status.external_nbo = effect.nbo

        self._current_audit.affected_instruments.add(instrument)

    def _apply_create_instrument(self, effect: "CreateInstrumentEffect") -> None:
        """
        Apply a CreateInstrumentEffect to the exchange state.

        Creates a new instrument with the specified book names and aliases,
        and adds it to the exchange's instruments collection.
        """
        if effect.instrument_key is None:
            return

        if effect.instrument_key in self.instruments:
            # temporary disable
            # self.report_book_builder_error("Duplicate instrument key", id=effect.instrument_key)
            return

        # Determine configuration values
        enable_priority_checks = True
        if effect.enable_priority_check is not None:
            enable_priority_checks = effect.enable_priority_check

        enable_limit_price_check = True
        if effect.enable_limit_price_check is not None:
            enable_limit_price_check = effect.enable_limit_price_check

        autofill_enabled = None
        if effect.autofill_enabled is not None:
            autofill_enabled = effect.autofill_enabled

        autofill_broker = None
        if effect.autofill_broker is not None:
            autofill_broker = effect.autofill_broker

        # Create the instrument with book names
        instrument = Instrument(
            key=effect.instrument_key,
            book_names=effect.book_names,
            configuration=InstrumentConfiguration(
                enable_priority_checks=enable_priority_checks,
                enable_limit_price_check=enable_limit_price_check,
                autofill_enabled=autofill_enabled,
                autofill_broker=autofill_broker
            ),
            underlying=effect.underlying
        )

        # Add aliases if provided
        if effect.aliases:
            for symbology, alias in effect.aliases.items():
                instrument.add_alias(symbology, alias)

        # Add instrument to exchange
        self.instruments[effect.instrument_key] = instrument

        self._current_audit.affected_instruments.add(instrument)

    def _make_parent_order_one_child(self, parent_order: "ParentOrder") -> None:
        if len(parent_order.parent_child_orders) == 1:
            # a single child orders no changes
            return

        main_order = parent_order.parent_child_orders.get_default_node()
        retain_quantity = 0
        retain_cumulative_quantity = 0

        remove_orders = []

        for child_order in parent_order.parent_child_orders.values():
            retain_quantity += child_order.quantity
            retain_cumulative_quantity += child_order.cumulative_quantity

            if child_order.key != main_order.key:
                remove_orders.append(child_order)

        self._add_to_affected_order_books(main_order)
        self._current_audit.testcases.add(main_order.testcase)
        self._current_audit.affected_child_order_keys.add(main_order.key)

        main_order.set_quantity(retain_quantity)
        main_order.set_cumulative_quantity(retain_cumulative_quantity)

        for child_order in remove_orders:
            self._cancel_single_order_by_order(child_order)

    def _apply_iceberg_replenishment_extra_child_order(self, effect: "IcebergReplenishmentExtraChildOrder") -> None:
        """
        Apply an IcebergReplenishmentExtraChildOrder effect to the exchange state.
        """

        if effect.parent_order_key not in self.parent_orders:
            self.report_book_builder_error("Parent order iceberg replenishment child order", id=effect.parent_order_key)
            return

        parent_order = self.parent_orders[effect.parent_order_key]
        hidden_child_order = parent_order.parent_child_orders.get_default_node()
        self._current_audit.affected_child_order_keys.add(hidden_child_order.key)

        if hidden_child_order.leaves_quantity == effect.replenished_quantity:
            hidden_child_order.amend(
                timestamp=effect.timestamp,
            )
            hidden_child_order.make_visible()
            hidden_child_order.change_key(effect.new_key)
        else:
            child_order = ChildOrder(
                key=effect.new_key,
                parent=parent_order,
                price=hidden_child_order.price,
                quantity=effect.replenished_quantity,
                side=hidden_child_order.side,
                timestamp=effect.timestamp,
                visible_quantity=None,
                ordtype=hidden_child_order.ordtype,
                tif=hidden_child_order.tif,
                memo=hidden_child_order.memo,
                testcase=hidden_child_order.testcase,
                order_status=hidden_child_order.order_status,
                iceberg_strategy_root_child_order=hidden_child_order)

            self.exchange_child_orders[child_order.key] = child_order
            collections = hidden_child_order._member_of.get("child_orders", [])

            for collection in list(collections):
                if hidden_child_order.key in collection:
                    self._current_audit.affected_order_books.add(collection.owner)
                    collection[child_order.key] = child_order

            self._current_audit.affected_child_order_keys.add(child_order.key)
            self._current_audit.new_child_order_keys.add(child_order.key)

            hidden_child_order.amend(quantity=hidden_child_order.quantity - effect.replenished_quantity,
                visible_quantity=0
            )

    def _apply_trading_session(self, effect: "TradingSessionEffect") -> None:
        """
        Apply a TradingSessionEffect to the exchange state.
        """
        self.trading_session = effect.session

    def _apply_clean_up(self, effect: "ModelCleanUpEffect") -> None:
        """
        Apply a CleanUpEffect to the exchange state.

        Cleans up everything
        """
        print("CleanUp effect")
        self.trading_session = ""

        print(f"trades: {len(self.trades)}")
        self.trades.clear()

        print(f"exchange_child_orders: {len(self.exchange_child_orders)}")
        self.exchange_child_orders.clear()

        print(f"parent_orders: {len(self.parent_orders)}")
        self.parent_orders.clear()

        print(f"instruments: {len(self.instruments)}")
        self.instruments.clear()

        print(f"instrument_groups: {len(self.instrument_groups)}")
        self.instrument_groups.clear()

        print(f"users: {len(self.users)}")
        self.users.clear()

        print(f"user_groups: {len(self.user_groups)}")
        self.user_groups.clear()

    def consume_dirty_orderbooks(self) -> List[OrderBook]:
        """
        Consume all dirty objects from the registry and return the list of OrderBook objects.

        This method drains the dirty registry, filtering for OrderBook instances.
        After this call, the dirty registry will be empty.

        Returns:
            List of OrderBook objects that were marked as dirty
        """
        dirty_items = self._registry.consume()
        order_books = [obj for obj, _, _ in dirty_items if isinstance(obj, OrderBook)]
        return order_books

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "key": self.key,
            "instruments": [inst.to_dict() for inst in self.instruments.values()],
            "parent_orders": [po.to_dict() for po in self.parent_orders.values()],
        }

    def write_to_file(self, file_path: str) -> None:
        """
        Write the exchange state to a JSON file.

        Args:
            file_path: Path to the output file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
