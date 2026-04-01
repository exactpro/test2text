from typing import Dict, Any, Optional

from .base import DownstreamEffect, register_effect
from ex_tmodel2.exchange.enums import DownstreamEffectType


@register_effect(DownstreamEffectType.START_OF_DAY)
class StartOfDayEffect(DownstreamEffect):
    """
    Effect representing start of a trading day or session.

    Attributes:
        date: The date being started (ISO format string)
        session: Optional session identifier
    """

    def __init__(
        self,
        date: Optional[str] = None,
        session: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.START_OF_DAY.value)
        self.date = date
        self.session = session

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StartOfDayEffect":
        return cls(
            date=data.get("date"),
            session=data.get("session"),
        )


@register_effect(DownstreamEffectType.END_OF_DAY)
class EndOfDayEffect(DownstreamEffect):
    """
    Effect representing end of a trading day or session.

    Attributes:
        date: The date being ended (ISO format string)
        session: Optional session identifier
    """

    def __init__(
        self,
        date: Optional[str] = None,
        session: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.END_OF_DAY.value)
        self.date = date
        self.session = session

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EndOfDayEffect":
        return cls(
            date=data.get("date"),
            session=data.get("session"),
        )


@register_effect(DownstreamEffectType.CLEAN_UP)
class CleanUpEffect(DownstreamEffect):
    """
    Effect representing a cleanup operation.

    Attributes:
        scope: What to clean up (e.g., "orders", "trades", "all")
        reason: Optional reason for cleanup
    """

    def __init__(
        self,
        scope: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.CLEAN_UP.value)
        self.scope = scope
        self.reason = reason

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CleanUpEffect":
        return cls(
            scope=data.get("scope"),
            reason=data.get("reason"),
        )

@register_effect(DownstreamEffectType.TRADING_SESSION)
class TradingSessionEffect(DownstreamEffect):
    """
    Downstream effect representing a trading session update.

    Attributes:
        session: Trading session identifier (optional)
    """

    def __init__(
        self,
        session: Optional[str] = None,
    ) -> None:
        super().__init__(DownstreamEffectType.TRADING_SESSION.value)
        self.session = session

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["session"] = self.session
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingSessionEffect":
        """Create an TradingSessionEffect from a dictionary."""
        return cls(
            session=data.get("session"),
        )
