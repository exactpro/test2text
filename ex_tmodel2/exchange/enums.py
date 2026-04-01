from enum import Enum

class Side(str, Enum):
    """FIX Side(54) values, per FIX.Latest EP299."""
    BUY = "1"                   # Buy
    SELL = "2"                  # Sell
    BUY_MINUS = "3"             # Buy minus
    SELL_PLUS = "4"             # Sell plus
    SELL_SHORT = "5"            # Sell short
    SELL_SHORT_EXEMPT = "6"     # Sell short exempt
    UNDISCLOSED = "7"           # Undisclosed (IOI/List Order use)
    CROSS = "8"                 # Cross (counterparty is an exchange)
    CROSS_SHORT = "9"           # Cross short
    CROSS_SHORT_EXEMPT = "A"    # Cross short exempt
    AS_DEFINED = "B"            # As Defined (multileg)
    OPPOSITE = "C"              # Opposite (multileg)
    SUBSCRIBE = "D"             # Subscribe (e.g., CIV)
    REDEEM = "E"                # Redeem (e.g., CIV)
    LEND = "F"                  # Lend (Financing: collateral direction)
    BORROW = "G"                # Borrow (Financing: collateral direction)
    SELL_UNDISCLOSED = "H"      # Sell undisclosed (ESMA RTS 22 "UNDI")

    @classmethod
    def from_fix(cls, value: str) -> "Side":
        """Parse a raw FIX(54) char into Side."""
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown FIX Side value: {value!r}") from exc

    def to_fix(self) -> str:
        """Return the FIX(54) wire value."""
        return self.value

class TimeInForce(str, Enum):
    """FIX TimeInForce(59) values per FIX.Latest EP299."""
    DAY = "0"  # Day
    GTC = "1"  # Good Till Cancel
    OPENING = "2"  # At the Opening
    IOC = "3"  # Immediate or Cancel
    FOK = "4"  # Fill or Kill
    GOOD_TILL_CROSSING = "5"  # Good Till Crossing
    GTD = "6"  # Good Till Date (GTD)
    AT_THE_CLOSE = "7"  # At the Close
    GOOD_THROUGH_CROSSING = "8"  # Good Through Crossing
    AT_CROSSING = "9"            # At Crossing
    GOOD_FOR_TIME = "A"          # Good for Time (GFT)
    GOOD_TILL_EXECUTION = "B"    # Good Till Execution
    GOOD_TILL_CANCEL_OR_TIME = "C"  # Good Till Cancel or Time
    IMMEDIATE_OR_CANCEL_THEN_DAY = "D"  # IOC then Day (exchange extension)
    MARKET_ON_CLOSE = "E"        # Market on Close (MOC)
    NEVER = "F"                  # Never (Do not execute)
    SYS = "S"       # Good for Session (GTS)
    RHO = "R"       # Regular Hours Only (RHO)
    POST_ONLY = "P"       # Post Only (RHO)


    @classmethod
    def from_fix(cls, value: str) -> "TimeInForce":
        """Parse a raw FIX(59) value into TimeInForce."""
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown FIX TimeInForce value: {value!r}") from exc

    def to_fix(self) -> str:
        """Return the FIX(59) wire value."""
        return self.value

class OrdType(str, Enum):
    """FIX OrdType(40) values per FIX.Latest EP299."""
    MARKET = "1"                      # Market
    LIMIT = "2"                       # Limit
    STOP = "3"                        # Stop / Stop Loss
    STOP_LIMIT = "4"                  # Stop Limit
    MARKET_ON_CLOSE = "5"             # Market on Close (MOC)
    WITH_OR_WITHOUT = "6"             # With or Without
    LIMIT_OR_BETTER = "7"             # Limit or Better
    LIMIT_WITH_OR_WITHOUT = "8"       # Limit with or Without
    ON_BASIS = "9"                    # On Basis
    ON_CLOSE = "A"                    # On Close
    LIMIT_ON_CLOSE = "B"              # Limit on Close
    FOREX_MARKET = "C"                # Forex - Market
    PREVIOUSLY_QUOTED = "D"           # Previously Quoted
    PREVIOUSLY_INDICATED = "E"        # Previously Indicated
    FOREX_LIMIT = "F"                 # Forex - Limit
    FOREX_SWAP = "G"                  # Forex - Swap
    FOREX_PREVIOUSLY_QUOTED = "H"     # Forex - Previously Quoted
    FUNARI = "I"                      # Funari (Japan)
    MARKET_IF_TOUCHED = "J"           # Market If Touched (MIT)
    MARKET_TO_LIMIT = "K"  # Market with Leftover as Limit (MAK)
    PREVIOUS_FUND_VALUATION_POINT = "L"  # Previous Fund Valuation Point (NAV)
    NEXT_FUND_VALUATION_POINT = "M"      # Next Fund Valuation Point (NAV)
    PEGGED = "P"                      # Pegged
    COUNTER_ORDER_SELECTION = "Q"     # Counter-Order Selection (exchange-defined)
    STOP_ON_QUOTE = "S"               # Stop on Quote
    STOP_LIMIT_ON_QUOTE = "T"         # Stop Limit on Quote
    MARKET_WITH_PROTECTION = "U"      # Market with Protection
    LIMIT_WITH_PROTECTION = "V"       # Limit with Protection
    MARKET_ON_OPEN = "W"              # Market on Open
    LIMIT_ON_OPEN = "X"               # Limit on Open

    IMBALANCE = "i"  # Imbalance

    @classmethod
    def from_fix(cls, value: str) -> "OrdType":
        """Parse a raw FIX(40) value into OrdType."""
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown FIX OrdType value: {value!r}") from exc

    def to_fix(self) -> str:
        """Return the FIX(40) wire value."""
        return self.value

class ExecType(Enum):
    """FIX OrdType(150) values per FIX.Latest EP299."""
    NEW = "0"                     # New
    PARTIAL_FILL = "1"            # Partial Fill
    FILL = "2"                    # Fill
    DONE_FOR_DAY = "3"            # Done for day
    CANCELED = "4"                # Canceled
    REPLACED = "5"                # Replaced (Order Cancel/Replace)
    PENDING_CANCEL = "6"          # Pending Cancel (e.g., awaiting confirmation)
    STOPPED = "7"                 # Stopped
    REJECTED = "8"                # Rejected
    SUSPENDED = "9"               # Suspended
    PENDING_NEW = "A"             # Pending New
    CALCULATED = "B"              # Calculated (e.g., pricing based on prior trades)
    EXPIRED = "C"                 # Expired
    RESTATED = "D"                # Restated (broker initiated change)
    PENDING_REPLACE = "E"         # Pending Replace
    TRADE = "F"                   # Trade (non-Fill trade message)
    TRADE_CORRECT = "G"           # Trade Correct
    TRADE_CANCEL = "H"            # Trade Cancel
    ORDER_STATUS = "I"            # Order Status

    @classmethod
    def from_fix(cls, value: str) -> "ExecType":
        """Parse a raw FIX(150) value into ExecType."""
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown FIX ExecType value: {value!r}") from exc

    def to_fix(self) -> str:
        """Return the FIX(150) wire value."""
        return self.value


class DownstreamEffectType(str, Enum):
    """
    Common downstream effect types for state transitions.

    These represent the typical outcomes/effects that result from
    processing input signals in an order management context.
    """
    ORDER_ACCEPTED = "OrderAccepted"      # Order was accepted by the exchange
    ORDER_CANCELED = "OrderCanceled"      # Order was canceled
    ORDER_REPLACED = "OrderReplaced"      # Order was replaced/amended
    ORDER_EXECUTED = "OrderExecuted"      # Order was executed (filled or partially filled)
    TRADE = "Trade"                       # Trade occurred (represents one side of a trade)
    INSTRUMENT_STATUS = "InstrumentStatus"  # Instrument status update (session, NBBO)
    CREATE_INSTRUMENT = "CreateInstrument"  # Create a new instrument
    ICEBERG_REPLENISHMENT_EXTRA_CHILD_ORDER = "IcebergReplenishmentExtraChildOrder"
    # System-level lifecycle effects
    TRADING_SESSION = "TradingSession"
    START_OF_DAY = "StartOfDay"           # Start of trading day or session
    END_OF_DAY = "EndOfDay"               # End of trading day or session
    CLEAN_UP = "CleanUp"                  # Cleanup operation


class CancelReason(str, Enum):
    """
    Reasons for order cancellation.
    """
    OTHER = "Other"                           # Default/unspecified reason
    EXPIRATION = "Expiration"                 # Order expired (e.g., end of day, GTD reached)
    SELF_TRADE_PREVENTION = "SelfTradePrevention"  # Canceled to prevent self-trade

class PegPriceType(str, Enum):
    """FIX PegPriceType(1094) values"""
    LAST = "1"          # Last
    MID = "2"           # Mid
    OPENING = "3"       # Opening
    MARKET = "4"        # Market
    PRIMARY = "5"       # Primary
    FIXED = "6"         # Fixed local best bid or offer
    VWAP = "7"          # VWAP
    TRAILING = "8"      # Trailing Stop
    LIMIT = "9"         # Limit

    @classmethod
    def from_fix(cls, value: str) -> "Side":
        """Parse a raw PegPriceType(1094) char into Side."""
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown FIX PegPriceType value: {value!r}") from exc

    def to_fix(self) -> str:
        """Return the PegPriceType(1094) wire value."""
        return self.value

class DisplayMethod(Enum):
    """FIX DisplayMethod(1084) values"""
    INITIAL = "1"       # Initial display quantity
    NEW = "2"           # New display quantity each refresh
    RANDOM = "3"        # Randomized display quantity
    UNDISCLOSED = "4"   # Not displayed (hidden)

    @classmethod
    def from_fix(cls, value: str) -> "DisplayMethod":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Unknown DisplayMethod FIX value: {value}")


class OrdStatus(str, Enum):
    """
    FIX Protocol Tag 39 — OrdStatus
    Indicates the current status of an order.
    """

    NEW = "0"                # New
    PARTIALLY_FILLED = "1"   # Partially filled
    FILLED = "2"             # Filled
    DONE_FOR_DAY = "3"       # Done for day
    CANCELED = "4"           # Canceled
    REPLACED = "5"           # Replaced
    PENDING_CANCEL = "6"     # Pending cancel
    STOPPED = "7"            # Stopped
    REJECTED = "8"           # Rejected
    SUSPENDED = "9"          # Suspended
    PENDING_NEW = "A"        # Pending new
    CALCULATED = "B"         # Calculated
    EXPIRED = "C"            # Expired
    ACCEPTED_FOR_BIDDING = "D"  # Accepted for bidding
    PENDING_REPLACE = "E"    # Pending replace

    @classmethod
    def from_fix(cls, value: str) -> "OrdStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Unknown OrdStatus FIX value: {value}")


class LastLiquidityInd(str, Enum):
    """
    FIX Tag 851 - LastLiquidityInd
    Indicates whether the last fill added or removed liquidity.
    """
    NEITHER = "0"        # Neither added nor removed liquidity
    ADDED = "1"          # Added Liquidity (passive / maker)
    REMOVED = "2"        # Removed Liquidity (aggressive / taker)
    ROUTED_OUT = "3"     # Liquidity Routed Out (executed away from venue)
    AUCTION = "4"        # Auction execution

    @classmethod
    def from_fix(cls, value: str) -> "LastLiquidityInd":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Unknown LastLiquidityInd value: {value}")


class IcebergTradeMode(str, Enum):
    UNDEFINED = "0"    # Not set
    VISIBLE = "1"      # Trade against fully visible order
    HIDDEN = "2"       # Trade against fully hidden order
    PART_PEAK = "3"    # Partial trade against iceberg peak
    FULL_PEAK = "4"    # Full trade of the iceberg peak
    UNDERWATER = "5"   # Trade that covers both visible and underlying part


class TradingSessionSubID(Enum):
    """
    FIX Tag 625 - TradingSessionSubID

    Identifies a sub-session within a TradingSessionID (Tag 336).
    Commonly used to distinguish phases like opening auction, continuous trading, etc.
    """

    PRE_OPEN = "1"          # Pre-open / pre-market phase
    OPENING = "2"           # Opening auction or opening phase
    CONTINUOUS = "3"        # Continuous trading
    CLOSING = "4"           # Closing auction or closing phase
    POST_CLOSE = "5"        # Post-close / after-market
    INTRADAY_AUCTION = "6"  # Intraday auction (e.g. volatility interruption)

    # Market-specific / less common
    QUIESCENT = "7"         # Quiescent / inactive period
    BATCH = "8"             # Batch trading
    SCHEDULED_AUCTION = "9" # Scheduled auction (non-open/close)

    @classmethod
    def from_fix(cls, value: str) -> "TradingSessionSubID":
        """Create enum from FIX value."""
        return cls(value)


class Printable(str, Enum):
    """
    Indicates whether a trade execution is printable.
    """
    YES = "Y"    # Printable
    NO = "N"     # Not printable
    NONE = ""    # Not specified