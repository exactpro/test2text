"""
Trade class
"""

from decimal import Decimal
from typing import List, TYPE_CHECKING, Optional

from .model_base import ModelNode
from .enums import Side, LastLiquidityInd, IcebergTradeMode, TradingSessionSubID, Printable

if TYPE_CHECKING:
    from .orders import ChildOrder


class TradeSide:
    """
    Represents one side of a trade execution.

    Attributes:
        side: The side of the order (buy/sell)
        price: Execution price
        quantity: Execution quantity

        order: The child order that was executed
        (subject for removal)
    """

    def __init__(
        self,
        side: Side,
        price: Decimal,
        quantity: Decimal,
        trade: "Trade",
        session: TradingSessionSubID,
        testcase: str,
        instrument_key: str,
        memo: str,
        contra_broker: str,
        printable: Printable,
        last_liquidity_indicator: LastLiquidityInd = LastLiquidityInd.NEITHER,
        order: Optional["ChildOrder"] = None,
        observed_iceberg_trade_mode: IcebergTradeMode = IcebergTradeMode.UNDEFINED
    ) -> None:
        self.trade = trade
        trade.testcase = testcase

        self.side = side
        self.price = price
        self.quantity = quantity
        self.printable = printable
        self.session = session
        self.instrument_key = instrument_key
        self.memo = memo
        self.testcase = testcase
        self.contra_broker = contra_broker

        self.last_liquidity_indicator = last_liquidity_indicator

        # self.visible_quantity = None
        self.order_key = None
        self.leaves_quantity = None
        self.cumulative_quantity = None
        self.limit_price = None
        self.rank_price = None
        self.iceberg_trade_mode = None

        self.observed_iceberg_trade_mode = observed_iceberg_trade_mode

        if order is not None:
            self.order_key = order.key
            self.leaves_quantity = order.quantity - quantity
            self.cumulative_quantity = order.cumulative_quantity + quantity
            self.limit_price = order.price
            self.rank_price = order.price if order.rank_price is None else order.rank_price

            """
            if order.visible_quantity is not None:
                self.visible_quantity = order.visible_quantity - quantity
                if self.visible_quantity < 0:
                    self.visible_quantity = 0
            """

            if order.visible_quantity is None:
                self.iceberg_trade_mode = IcebergTradeMode.VISIBLE
            elif order.visible_quantity == 0:
                self.iceberg_trade_mode = IcebergTradeMode.HIDDEN
            elif order.visible_quantity == quantity:
                self.iceberg_trade_mode = IcebergTradeMode.FULL_PEAK
            elif order.visible_quantity > quantity:
                self.iceberg_trade_mode = IcebergTradeMode.PART_PEAK
            else:
                self.iceberg_trade_mode = IcebergTradeMode.UNDERWATER

    def __str__(self) -> str:
        """
        Return a string representation of the TradeSide (excluding order attribute).

        Returns:
            Formatted string with all TradeSide attributes except the order reference.
        """
        return (
            f"{self.trade.key} "
            f"side={self.side.name if self.side is not None else None} "
            f"order_key={self.order_key} "
            f"memo={self.memo} "
            f"{self.last_liquidity_indicator.name if self.last_liquidity_indicator is not None else None} "
            f"price={self.price} "
            f"{self.printable} "
            f"quantity={self.quantity} "
            f"leavesqty={self.leaves_quantity} "
            f"cumqty={self.cumulative_quantity} "
            f"{self.iceberg_trade_mode.name if self.iceberg_trade_mode is not None else None} "
            f"{self.observed_iceberg_trade_mode.name if self.observed_iceberg_trade_mode is not None else None} "
            f"limit_price={self.limit_price} "
            f"instrument={self.instrument_key} "
            f"contra_broker={self.contra_broker} "
        )

class Trade(ModelNode):
    """
    Represents an execution / fill / trade print.

    Attributes:
        trade_sides: List of trade sides that were executed in this trade
    """

    def __init__(self, key: str,
                 timestamp: Optional[str] = None) -> None:
        super().__init__(key)
        self.trade_sides: List[TradeSide] = []
        self.timestamp = timestamp
        self.testcase = None
