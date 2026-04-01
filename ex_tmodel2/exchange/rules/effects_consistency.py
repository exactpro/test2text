"""
Effects Consistency Module

This module contains rule checks for validating the consistency of downstream effects.
It detects situations where multiple independent trading signals may have been incorrectly merged into
a single state transition, which typically indicates concurrency issues or data aggregation problems.

Clean signal separation is important for accurate rule checking and trade
reconstruction.
"""

from decimal import Decimal
from typing import Optional
from typing import Iterator

from ex_tmodel2.exchange import ModelExchange, Side, ChildOrder, OrderBookPriorityComparisonResultEntry, OrderBook, \
    OrdType
from ex_tmodel2.exchange.downstream_effects import OrderExecutedEffect, OrderAcceptedEffect
from ex_tmodel2.exchange.enums import PegPriceType, Printable
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass

@rule_check(
    rule_description="Downstream Effects Consistency",
    rule_tags=["signals"],
)
class RuleCheckDownstreamEffectsConsistency(RuleCheck):
    """
    Rule check that validates signal consistency in state transitions via downstream effects.

    This rule detects when multiple independent input
    signals have been mixed. This can happen due to:
    - Concurrency effects in the source data
    - Incorrect transaction boundaries
    - Data aggregation issues

    When multiple add orders are detected, it suggests the transition
    cannot be cleanly split into individual transactions for analysis.
    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        num_executions = 0
        num_accepted = 0

        for effect in transition.downstream_effects:
            if isinstance(effect, OrderExecutedEffect):
                if effect.printable == Printable.NONE:
                    num_executions += 1
            if isinstance(effect, OrderAcceptedEffect):
                if exchange_next.instruments[effect.instrument_key].configuration.enable_priority_checks:
                    num_accepted += 1

        if num_accepted > 1:
            yield self.report_rule(transition,
                f"OrderAcceptedEffect count - {num_accepted}",
                True)

        if num_executions % 2 != 0:
            yield self.report_rule(transition,
                f"OrderExecutedEffect odd count - {num_executions}",
                True)
