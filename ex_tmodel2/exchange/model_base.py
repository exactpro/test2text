""" 
Base classes for the digital twin toolkit
"""

from ex_tmodel2.base.base import (
    Node,
    State,
    Collection,
    InputSignal,
    DownstreamEffect,
    StateTransition,
    TransitionAudit,
)
from ex_tmodel2.base.system_effects import EndOfDayEffect, CleanUpEffect, StartOfDayEffect, TradingSessionEffect

# Model layer aliases for base classes
ModelNode = Node
ModelState = State
ModelCollection = Collection
ModelInputSignal = InputSignal
ModelDownstreamEffect = DownstreamEffect
ModelStateTransition = StateTransition
ModelTransitionAudit = TransitionAudit
ModelEndOfDayEffect = EndOfDayEffect
ModelTradingSessionEffect = TradingSessionEffect
ModelCleanUpEffect = CleanUpEffect
ModelStartOfDayEffect = StartOfDayEffect