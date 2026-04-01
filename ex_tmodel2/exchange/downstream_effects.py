from __future__ import annotations

from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from ex_tmodel2.base.base import register_effect
from .model_base import ModelDownstreamEffect
from .enums import (
    DownstreamEffectType, CancelReason, TradingSessionSubID, Printable,
    Side, LastLiquidityInd, IcebergTradeMode
)

if TYPE_CHECKING:
    from .orders import ChildOrder
    from .enums import OrdType, TimeInForce, PegPriceType, DisplayMethod, OrdStatus


@register_effect(DownstreamEffectType.ORDER_ACCEPTED)
class OrderAcceptedEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an order to be created and added to the exchange.

    This effect contains attributes that will be used by the exchange to create
    a ChildOrder and add it to the order book. Unlike OrderAcceptedEffect which
    takes an existing ChildOrder, this effect provides the attributes for deferred
    order creation.

    Attributes:
        key: The key for the ChildOrder to be created
        parent_order_key: The key of the ParentOrder this child belongs to
        instrument_key: The key of the Instrument the order belongs to
        book_names: Optional list of order book names where the order should be added
        price: Order price (optional)
        quantity: Order quantity (optional)
        leaves_quantity: Leaves quantity (optional)
        side: Order side (optional)
        timestamp: Order timestamp (optional)
        ordtype: Order type (optional)
        visible_quantity: Visible quantity for iceberg orders (optional)
        tif: Time in force (optional)
        memo: Memo field (optional)
        testcase: Testcase field (optional)
        order_status: Order status (optional)
        peg_offset_value: Peg offset value for pegged orders (optional)
        peg_price_type: Peg price type for pegged orders (optional)
        min_quantity: Minimum quantity for order execution (optional)
        display_price: Display price (optional)
        rank_price: Rank price for priority calculations (optional)
        display_method: Display method for iceberg/reserve orders (optional)
        display_quantity: Display quantity for iceberg/reserve orders (optional)
    """

    def __init__(
        self,
        key: str,
        parent_order_key: str,
        instrument_key: str,
        book_names: Optional[List[str]] = None,
        price: Optional[Decimal] = None,
        quantity: Optional[Decimal] = None,
        leaves_quantity: Optional[Decimal] = None,
        side: Optional["Side"] = None,
        timestamp: Optional[str] = None,
        ordtype: Optional["OrdType"] = None,
        visible_quantity: Optional[Decimal] = None,
        tif: Optional["TimeInForce"] = None,
        memo: Optional[str] = None,
        testcase: Optional[str] = None,
        order_status: Optional["OrdStatus"] = None,
        peg_offset_value: Optional[Decimal] = None,
        peg_price_type: Optional["PegPriceType"] = None,
        min_quantity: Optional[Decimal] = None,
        display_price: Optional[Decimal] = None,
        rank_price: Optional[Decimal] = None,
        display_method: Optional["DisplayMethod"] = None,
        display_quantity: Optional[Decimal] = None,
        sending_time: Optional[str] = None,
        transact_time: Optional[str] = None,
        orig_sending_time: Optional[str] = None,
        expire_time: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.ORDER_ACCEPTED.value)
        self.key = key
        self.parent_order_key = parent_order_key
        self.instrument_key = instrument_key
        self.book_names = book_names
        self.price = price
        self.quantity = quantity
        self.leaves_quantity = leaves_quantity
        self.side = side
        self.timestamp = timestamp
        self.ordtype = ordtype
        self.visible_quantity = visible_quantity
        self.tif = tif
        self.memo = memo
        self.testcase = testcase
        self.order_status = order_status
        self.peg_offset_value = peg_offset_value
        self.peg_price_type = peg_price_type
        self.min_quantity = min_quantity
        self.display_price = display_price
        self.rank_price = rank_price
        self.display_method = display_method
        self.display_quantity = display_quantity
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["key"] = self.key
        result["parent_order_key"] = self.parent_order_key
        result["instrument_key"] = self.instrument_key
        result["book_names"] = list(self.book_names) if self.book_names is not None else None
        result["price"] = str(self.price) if self.price is not None else None
        result["quantity"] = str(self.quantity) if self.quantity is not None else None
        result["leaves_quantity"] = str(self.leaves_quantity) if self.leaves_quantity is not None else None
        result["side"] = self.side.value if self.side is not None else None
        result["timestamp"] = self.timestamp
        result["ordtype"] = self.ordtype.value if self.ordtype is not None else None
        result["visible_quantity"] = str(self.visible_quantity) if self.visible_quantity is not None else None
        result["tif"] = self.tif.value if self.tif is not None else None
        result["memo"] = self.memo
        result["testcase"] = self.testcase
        result["order_status"] = self.order_status.value if self.order_status is not None else None
        result["peg_offset_value"] = str(self.peg_offset_value) if self.peg_offset_value is not None else None
        result["peg_price_type"] = self.peg_price_type.value if self.peg_price_type is not None else None
        result["min_quantity"] = str(self.min_quantity) if self.min_quantity is not None else None
        result["display_price"] = str(self.display_price) if self.display_price is not None else None
        result["rank_price"] = str(self.rank_price) if self.rank_price is not None else None
        result["display_method"] = self.display_method.value if self.display_method is not None else None
        result["display_quantity"] = str(self.display_quantity) if self.display_quantity is not None else None
        result["sending_time"] = self.sending_time
        result["transact_time"] = self.transact_time
        result["orig_sending_time"] = self.orig_sending_time
        result["expire_time"] = self.expire_time
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderAcceptedEffect":
        """Create an OrderAcceptedEffect from a dictionary."""
        from .enums import OrdType, TimeInForce, PegPriceType, DisplayMethod, OrdStatus

        effect = cls(
            key=data["key"],
            parent_order_key=data["parent_order_key"],
            instrument_key=data["instrument_key"],
            book_names=data.get("book_names"),
            price=Decimal(data["price"]) if data.get("price") else None,
            quantity=Decimal(data["quantity"]) if data.get("quantity") else None,
            leaves_quantity=Decimal(data["leaves_quantity"]) if data.get("leaves_quantity") else None,
            side=Side(data["side"]) if data.get("side") else None,
            timestamp=data.get("timestamp"),
            ordtype=OrdType(data["ordtype"]) if data.get("ordtype") else None,
            visible_quantity=Decimal(data["visible_quantity"]) if data.get("visible_quantity") else None,
            tif=TimeInForce(data["tif"]) if data.get("tif") else None,
            memo=data.get("memo"),
            testcase=data.get("testcase"),
            order_status=OrdStatus(data["order_status"]) if data.get("order_status") else None,
            peg_offset_value=Decimal(data["peg_offset_value"]) if data.get("peg_offset_value") else None,
            peg_price_type=PegPriceType(data["peg_price_type"]) if data.get("peg_price_type") else None,
            min_quantity=Decimal(data["min_quantity"]) if data.get("min_quantity") else None,
            display_price=Decimal(data["display_price"]) if data.get("display_price") else None,
            rank_price=Decimal(data["rank_price"]) if data.get("rank_price") else None,
            display_method=DisplayMethod(data["display_method"]) if data.get("display_method") else None,
            display_quantity=Decimal(data["display_quantity"]) if data.get("display_quantity") else None,
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        return effect


@register_effect(DownstreamEffectType.ORDER_CANCELED)
class OrderCanceledEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an order being canceled.

    This effect is produced when an order is removed from the order book
    due to a cancellation request or system action.

    Attributes:
        key: The key of the ChildOrder that was canceled
        reason: The reason for cancellation (default: CancelReason.OTHER)
        timestamp: Optional timestamp of the cancellation
        parent_order_key: Optional parent order key to cancel all child orders
            associated with that parent order instead of a single child order
    """

    def __init__(
        self,
        key: Optional[str],
        reason: CancelReason = CancelReason.OTHER,
        timestamp: Optional[str] = None,
        parent_order_key: Optional[str] = None,
        sending_time: Optional[str] = None,
        transact_time: Optional[str] = None,
        orig_sending_time: Optional[str] = None,
        expire_time: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.ORDER_CANCELED.value)
        self.key = key
        self.reason = reason
        self.timestamp = timestamp
        self.parent_order_key = parent_order_key
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["key"] = self.key
        result["reason"] = self.reason.value
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        if self.parent_order_key is not None:
            result["parent_order_key"] = self.parent_order_key
        result["sending_time"] = self.sending_time
        result["transact_time"] = self.transact_time
        result["orig_sending_time"] = self.orig_sending_time
        result["expire_time"] = self.expire_time
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderCanceledEffect":
        """Create an OrderCanceledEffect from a dictionary."""
        effect = cls(
            key=data["key"],
            reason=CancelReason(data["reason"]) if data.get("reason") else CancelReason.OTHER,
            timestamp=data.get("timestamp"),
            parent_order_key=data.get("parent_order_key"),
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        return effect


@register_effect(DownstreamEffectType.ORDER_REPLACED)
class OrderReplacedEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an order being replaced/amended.

    This effect is produced when an existing order is modified
    (e.g., price or quantity change) via a cancel/replace operation.

    Attributes:
        key: The key of the ChildOrder that was replaced
        new_key: New key if the order key is being changed, None otherwise
        new_parent_key: New key for the parent order if being changed, None otherwise
        parent_order_key: Optional parent order key to replace all child orders
            associated with that parent order instead of a single child order
        book_names: Optional list of order book names where the order should be moved
        price: New price if amended, None otherwise
        quantity: New quantity if amended, None otherwise
        quantity_sign: Sign for quantity adjustment (e.g., "+" or "-"), None otherwise
        side: New side if amended, None otherwise
        ordtype: New order type if amended, None otherwise
        visible_quantity: New visible quantity if amended, None otherwise
        timestamp: New timestamp if amended, None otherwise
        timestamp_override: Override timestamp if amended, None otherwise
        peg_offset_value: New peg offset value if amended, None otherwise
        peg_price_type: New peg price type if amended, None otherwise
        min_quantity: New minimum quantity if amended, None otherwise
        display_price: New display price if amended, None otherwise
        rank_price: New rank price if amended, None otherwise
        tif: New time in force if amended, None otherwise
    """

    def __init__(
        self,
        key: Optional[str] = None,
        new_key: Optional[str] = None,
        new_parent_key: Optional[str] = None,
        parent_order_key: Optional[str] = None,
        sending_time: Optional[str] = None,
        transact_time: Optional[str] = None,
        orig_sending_time: Optional[str] = None,
        expire_time: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.ORDER_REPLACED.value)
        self.key = key
        self.new_key = new_key
        self.new_parent_key = new_parent_key
        self.parent_order_key = parent_order_key
        self.book_names: Optional[List[str]] = None
        self.price: Optional[Decimal] = None
        self.quantity: Optional[Decimal] = None
        self.quantity_sign: Optional[str] = None
        self.leaves_quantity: Optional[Decimal] = None
        self.side: Optional["Side"] = None
        self.ordtype: Optional["OrdType"] = None
        self.visible_quantity: Optional[Decimal] = None
        self.timestamp: Optional[str] = None
        self.timestamp_override: Optional[str] = None
        self.peg_offset_value: Optional[Decimal] = None
        self.peg_price_type: Optional["PegPriceType"] = None
        self.min_quantity: Optional[Decimal] = None
        self.display_price: Optional[Decimal] = None
        self.rank_price: Optional[Decimal] = None
        self.tif: Optional["TimeInForce"] = None
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["key"] = self.key
        result["new_key"] = self.new_key
        result["new_parent_key"] = self.new_parent_key
        if self.parent_order_key is not None:
            result["parent_order_key"] = self.parent_order_key
        result["book_names"] = list(self.book_names) if self.book_names is not None else None
        result["price"] = str(self.price) if self.price is not None else None
        result["quantity"] = str(self.quantity) if self.quantity is not None else None
        result["quantity_sign"] = self.quantity_sign
        result["leaves_quantity"] = str(self.leaves_quantity) if self.leaves_quantity is not None else None
        result["side"] = self.side.value if self.side is not None else None
        result["ordtype"] = self.ordtype.value if self.ordtype is not None else None
        result["visible_quantity"] = str(self.visible_quantity) if self.visible_quantity is not None else None
        result["timestamp"] = self.timestamp
        result["timestamp_override"] = self.timestamp_override
        result["peg_offset_value"] = str(self.peg_offset_value) if self.peg_offset_value is not None else None
        result["peg_price_type"] = self.peg_price_type.value if self.peg_price_type is not None else None
        result["min_quantity"] = str(self.min_quantity) if self.min_quantity is not None else None
        result["display_price"] = str(self.display_price) if self.display_price is not None else None
        result["rank_price"] = str(self.rank_price) if self.rank_price is not None else None
        result["tif"] = self.tif.value if self.tif is not None else None
        result["sending_time"] = self.sending_time
        result["transact_time"] = self.transact_time
        result["orig_sending_time"] = self.orig_sending_time
        result["expire_time"] = self.expire_time
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderReplacedEffect":
        """Create an OrderReplacedEffect from a dictionary."""
        from .enums import OrdType, PegPriceType, TimeInForce

        effect = cls(
            key=data.get("key"),
            new_key=data.get("new_key"),
            new_parent_key=data.get("new_parent_key"),
            parent_order_key=data.get("parent_order_key"),
        )
        effect.book_names = data.get("book_names")
        effect.price = Decimal(data["price"]) if data.get("price") else None
        effect.quantity = Decimal(data["quantity"]) if data.get("quantity") else None
        effect.quantity_sign = data.get("quantity_sign")
        effect.leaves_quantity = Decimal(data["leaves_quantity"]) if data.get("leaves_quantity") else None
        effect.side = Side(data["side"]) if data.get("side") else None
        effect.ordtype = OrdType(data["ordtype"]) if data.get("ordtype") else None
        effect.visible_quantity = Decimal(data["visible_quantity"]) if data.get("visible_quantity") else None
        effect.timestamp = data.get("timestamp")
        effect.timestamp_override = data.get("timestamp_override")
        effect.peg_offset_value = Decimal(data["peg_offset_value"]) if data.get("peg_offset_value") else None
        effect.peg_price_type = PegPriceType(data["peg_price_type"]) if data.get("peg_price_type") else None
        effect.min_quantity = Decimal(data["min_quantity"]) if data.get("min_quantity") else None
        effect.display_price = Decimal(data["display_price"]) if data.get("display_price") else None
        effect.rank_price = Decimal(data["rank_price"]) if data.get("rank_price") else None
        effect.tif = TimeInForce(data["tif"]) if data.get("tif") else None
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        return effect


@register_effect(DownstreamEffectType.ORDER_EXECUTED)
class OrderExecutedEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an order execution (fill or partial fill).

    This effect is produced when an order matches with another order
    and a trade occurs.

    Attributes:
        key: The key of the ChildOrder that was executed
        price: Execution price
        quantity: Execution quantity
        timestamp: Optional timestamp to update on the order after execution
        trade_match_id: Optional identifier for the trade match
        session: Trading session
        printable: Whether this execution is printable
        last_liquidity_indicator: Indicates if order added or removed liquidity
        iceberg_trade_mode: Mode indicating how the iceberg order was traded
    """

    def __init__(
        self,
        key: str,
        price: Decimal[str] = None,
        quantity: Decimal[str] = None,
        timestamp: Optional[str] = None,
        trade_match_id: Optional[str] = None,
        session: Optional[TradingSessionSubID] = None,
        printable: Printable = Printable.NONE,
        last_liquidity_indicator: LastLiquidityInd = LastLiquidityInd.NEITHER,
        iceberg_trade_mode: IcebergTradeMode = IcebergTradeMode.UNDEFINED,
        sending_time: Optional[str] = None,
        transact_time: Optional[str] = None,
        orig_sending_time: Optional[str] = None,
        expire_time: Optional[str] = None,
        contra_broker: Optional[str] = None,
        trd_reg_timestamp: Optional[str] = None,
        brok_pref: bool = False,
    ) -> None:
        super().__init__(DownstreamEffectType.ORDER_EXECUTED.value)
        self.key = key
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.trade_match_id = trade_match_id
        self.session = session
        self.printable = printable
        self.last_liquidity_indicator = last_liquidity_indicator
        self.iceberg_trade_mode = iceberg_trade_mode
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time
        self.contra_broker = contra_broker
        self.trd_reg_timestamp = trd_reg_timestamp
        self.brok_pref = brok_pref

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["key"] = self.key
        # Use "None" string for None values to preserve legacy format
        result["price"] = str(self.price) if self.price is not None else "None"
        result["quantity"] = str(self.quantity) if self.quantity is not None else "None"
        result["timestamp"] = self.timestamp
        if self.trade_match_id is not None:
            result["trade_match_id"] = self.trade_match_id
        if self.session is not None:
            result["session"] = self.session
        result["printable"] = self.printable.value
        result["last_liquidity_indicator"] = self.last_liquidity_indicator.value
        result["iceberg_trade_mode"] = self.iceberg_trade_mode.value
        result["sending_time"] = self.sending_time
        result["transact_time"] = self.transact_time
        result["orig_sending_time"] = self.orig_sending_time
        result["expire_time"] = self.expire_time
        result["contra_broker"] = self.contra_broker
        result["trd_reg_timestamp"] = self.trd_reg_timestamp
        result["brok_pref"] = self.brok_pref
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderExecutedEffect":
        """Create an OrderExecutedEffect from a dictionary."""
        # Handle "None" string from old files
        price_str = data.get("price")
        quantity_str = data.get("quantity")
        effect = cls(
            key=data["key"],
            price=Decimal(price_str) if price_str and price_str != "None" else None,
            quantity=Decimal(quantity_str) if quantity_str and quantity_str != "None" else None,
            timestamp=data.get("timestamp"),
            trade_match_id=data.get("trade_match_id"),
            session=TradingSessionSubID(data["session"]) if data.get("session") else None,
            printable=Printable(data["printable"]) if data.get("printable") else Printable.NONE,
            last_liquidity_indicator=LastLiquidityInd(data["last_liquidity_indicator"]) if data.get("last_liquidity_indicator") else LastLiquidityInd.NEITHER,
            iceberg_trade_mode=IcebergTradeMode(data["iceberg_trade_mode"]) if data.get("iceberg_trade_mode") else IcebergTradeMode.UNDEFINED,
            contra_broker=data.get("contra_broker"),
            brok_pref=data.get("brok_pref", False)
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        effect.trd_reg_timestamp = data.get("trd_reg_timestamp") if data.get("trd_reg_timestamp") else None
        return effect


@register_effect(DownstreamEffectType.TRADE)
class TradeEffect(ModelDownstreamEffect):
    """
    Downstream effect representing one side of a trade execution.

    This effect contains all the parameters needed to populate a TradeSide object.

    Attributes:
        side: The side of the order (buy/sell)
        price: Execution price
        quantity: Execution quantity
        instrument_key: The key of the Instrument
        trade_match_id: Identifier for the trade match
        memo: Memo field from the order
        testcase: Testcase field from the order
        session: Trading session
        printable: Whether this execution is printable
        timestamp: Optional timestamp to update on the order after execution
    """

    def __init__(
        self,
        price: Decimal,
        quantity: Decimal,
        instrument_key: str,
        side: Optional[Side] = None,
        trade_match_id: Optional[str] = None,
        memo: Optional[str] = None,
        testcase: Optional[str] = None,
        session: Optional[TradingSessionSubID] = None,
        printable: Printable = Printable.NONE,
        timestamp: Optional[str] = None,
        orig_time: Optional[str] = None,
        sending_time: Optional[str] = None,
        transact_time: Optional[str] = None,
        orig_sending_time: Optional[str] = None,
        expire_time: Optional[str] = None,
        effective_time: Optional[str] = None,
        trd_reg_timestamp: Optional[str] = None,
        event_time: Optional[str] = None,
        contra_broker: Optional[str] = None,
        brok_pref: bool = False,
    ) -> None:
        super().__init__(DownstreamEffectType.TRADE.value)
        self.key = trade_match_id
        self.side = side
        self.price = price
        self.quantity = quantity
        self.instrument_key = instrument_key
        self.trade_match_id = trade_match_id
        self.memo = memo
        self.testcase = testcase
        self.session = session
        self.printable = printable
        self.timestamp = timestamp
        self.orig_time = orig_time
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time
        self.effective_time = effective_time
        self.trd_reg_timestamp = trd_reg_timestamp
        self.event_time = event_time
        self.contra_broker = contra_broker
        self.brok_pref = brok_pref

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        if self.side is not None:
            result["side"] = self.side.value
        if self.price is not None:
            result["price"] = str(self.price)
        if self.quantity is not None:
            result["quantity"] = str(self.quantity)
        result["instrument_key"] = self.instrument_key
        if self.trade_match_id is not None:
            result["trade_match_id"] = self.trade_match_id
        if self.memo is not None:
            result["memo"] = self.memo
        if self.testcase is not None:
            result["testcase"] = self.testcase
        if self.session is not None:
            result["session"] = self.session.value
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        result["printable"] = self.printable.value
        if self.orig_time is not None:
            result["orig_time"] = self.orig_time
        if self.sending_time is not None:
            result["sending_time"] = self.sending_time
        if self.transact_time is not None:
            result["transact_time"] = self.transact_time
        if self.orig_sending_time is not None:
            result["orig_sending_time"] = self.orig_sending_time
        if self.expire_time is not None:
            result["expire_time"] = self.expire_time
        if self.effective_time is not None:
            result["effective_time"] = self.effective_time
        if self.trd_reg_timestamp is not None:
            result["trd_reg_timestamp"] = self.trd_reg_timestamp
        if self.event_time is not None:
            result["event_time"] = self.event_time
        if self.contra_broker is not None:
            result["contra_broker"] = self.contra_broker
        if self.brok_pref is not None:
            result["brok_pref"] = self.brok_pref
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeEffect":
        """Create a TradeEffect from a dictionary."""
        # Handle "None" string from old files
        price_str = data.get("price")
        quantity_str = data.get("quantity")
        effect = cls(
            price=Decimal(price_str) if price_str and price_str != "None" else None,
            quantity=Decimal(quantity_str) if quantity_str and quantity_str != "None" else None,
            instrument_key=data["instrument_key"],
            side=Side(data["side"]) if data.get("side") else None,
            trade_match_id=data.get("trade_match_id"),
            memo=data.get("memo"),
            testcase=data.get("testcase"),
            session=TradingSessionSubID(data["session"]) if data.get("session") else None,
            printable=Printable(data["printable"]) if data.get("printable") else Printable.NONE,
            timestamp=data.get("timestamp"),
            contra_broker=data.get("contra_broker"),
            brok_pref=data.get("brok_pref", False)
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.orig_time = data.get("orig_time") if data.get("orig_time") else None
        effect.effective_time = data.get("effective_time") if data.get("effective_time") else None
        effect.trd_reg_timestamp = data.get("trd_reg_timestamp") if data.get("trd_reg_timestamp") else None
        effect.event_time = data.get("event_time") if data.get("event_time") else None
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        return effect


@register_effect(DownstreamEffectType.INSTRUMENT_STATUS)
class InstrumentStatusEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an instrument status update.

    This effect is produced when instrument status changes such as
    session changes or NBBO updates.

    Attributes:
        instrument_key: The key of the Instrument
        session: Trading session identifier (optional)
        nbb: National Best Bid price (optional)
        nbo: National Best Offer price (optional)
    """

    def __init__(
        self,
        instrument_key: str,
        session: Optional[str] = None,
        nbb: Optional[Decimal] = None,
        nbo: Optional[Decimal] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.INSTRUMENT_STATUS.value)
        self.instrument_key = instrument_key
        self.session = session
        self.nbb = nbb
        self.nbo = nbo

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["instrument_key"] = self.instrument_key
        result["session"] = self.session
        result["nbb"] = str(self.nbb) if self.nbb is not None else None
        result["nbo"] = str(self.nbo) if self.nbo is not None else None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstrumentStatusEffect":
        """Create an InstrumentStatusEffect from a dictionary."""
        effect = cls(
            instrument_key=data["instrument_key"],
            session=data.get("session"),
            nbb=Decimal(data["nbb"]) if data.get("nbb") else None,
            nbo=Decimal(data["nbo"]) if data.get("nbo") else None,
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        return effect

@register_effect(DownstreamEffectType.CREATE_INSTRUMENT)
class CreateInstrumentEffect(ModelDownstreamEffect):
    """
    Downstream effect representing an instrument to be created.

    This effect is produced when a new instrument needs to be added
    to the exchange.

    Attributes:
        instrument_key: The unique key for the instrument
        book_names: List of order book names to create for this instrument
        aliases: Dictionary mapping symbology to alias (e.g., {"RIC": "AAPL.O"})
        enable_priority_check: Whether to enable priority checking for this instrument
        enable_limit_price_check: Whether to enable limit price checking for this instrument
    """

    def __init__(
        self,
        instrument_key: str,
        book_names: Optional[List[str]] = None,
        aliases: Optional[Dict[str, str]] = None,
        enable_priority_check: Optional[bool] = None,
        enable_limit_price_check: Optional[bool] = None,
        underlying: Optional[str] = None,
        autofill_enabled: Optional[str] = None,
        autofill_broker: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.CREATE_INSTRUMENT.value)
        self.instrument_key = instrument_key
        self.book_names = book_names
        self.aliases = aliases
        self.enable_priority_check = enable_priority_check
        self.enable_limit_price_check = enable_limit_price_check
        self.underlying = underlying
        self.autofill_enabled = autofill_enabled
        self.autofill_broker = autofill_broker

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["instrument_key"] = self.instrument_key
        result["book_names"] = list(self.book_names) if self.book_names is not None else None
        result["aliases"] = self.aliases
        result["enable_priority_check"] = self.enable_priority_check
        result["enable_limit_price_check"] = self.enable_limit_price_check
        result["underlying"] = self.underlying
        result["autofill_enabled"] = self.autofill_enabled
        result["autofill_broker"] = self.autofill_broker
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreateInstrumentEffect":
        """Create a CreateInstrumentEffect from a dictionary."""
        effect = cls(
            instrument_key=data["instrument_key"],
            book_names=data.get("book_names"),
            aliases=data.get("aliases"),
            enable_priority_check=data.get("enable_priority_check"),
            enable_limit_price_check=data.get("enable_limit_price_check"),
            underlying=data.get("underlying"),
            autofill_enabled=data.get("autofill_enabled") or None,
            autofill_broker=data.get("autofill_broker") or None,
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        return effect

@register_effect(DownstreamEffectType.ICEBERG_REPLENISHMENT_EXTRA_CHILD_ORDER)
class IcebergReplenishmentExtraChildOrder(ModelDownstreamEffect):
    """
    Iceberg replenishment as additional child order

    Attributes:
        parent_order_key: The key of the parent order
        new_key:
        replenished_quantity: The quantity of the replenished order
    """

    def __init__(self, parent_order_key: str,
                 new_key: str,
                 replenished_quantity: Decimal,
                 timestamp: str = None,
                 orig_time: Optional[str] = None,
                 sending_time: Optional[str] = None,
                 transact_time: Optional[str] = None,
                 orig_sending_time: Optional[str] = None,
                 expire_time: Optional[str] = None,
                 effective_time: Optional[str] = None,
                 trd_reg_timestamp: Optional[str] = None,
                 event_time: Optional[str] = None,
                 ) -> None:
        super().__init__(DownstreamEffectType.ICEBERG_REPLENISHMENT_EXTRA_CHILD_ORDER.value)
        self.parent_order_key = parent_order_key
        self.new_key = new_key
        self.replenished_quantity = replenished_quantity
        self.timestamp = timestamp
        self.sending_time = sending_time
        self.transact_time = transact_time
        self.orig_sending_time = orig_sending_time
        self.expire_time = expire_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["parent_order_key"] = self.parent_order_key
        result["new_key"] = self.new_key
        result["replenished_quantity"] = str(self.replenished_quantity) if self.replenished_quantity is not None else "None"
        result["timestamp"] = self.timestamp
        result["sending_time"] = self.sending_time
        result["transact_time"] = self.transact_time
        result["orig_sending_time"] = self.orig_sending_time
        result["expire_time"] = self.expire_time
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IcebergReplenishmentExtraChildOrder":
        """Create a IcebergReplenishmentExtraChildOrder from a dictionary."""
        replenished_quantity_str = data.get("replenished_quantity")

        effect = cls(
            parent_order_key=data["parent_order_key"],
            new_key=data["new_key"],
            replenished_quantity=Decimal(replenished_quantity_str) if replenished_quantity_str and replenished_quantity_str != "None" else None,
            timestamp=data["timestamp"]
        )
        effect.state_transition_timestamp = data.get("state_transition_timestamp")
        effect.sending_time = data.get("sending_time") if data.get("sending_time") else None
        effect.transact_time = data.get("transact_time") if data.get("transact_time") else None
        effect.orig_sending_time = data.get("orig_sending_time") if data.get("orig_sending_time") else None
        effect.expire_time = data.get("expire_time") if data.get("expire_time") else None
        return effect
