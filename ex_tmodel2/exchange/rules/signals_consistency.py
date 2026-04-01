"""
Signal Consistency Module

This module contains rule checks for validating the consistency of input signals
and their downstream effects. It detects situations where multiple independent
trading signals may have been incorrectly merged into a single state transition,
which typically indicates concurrency issues or data aggregation problems.

Clean signal separation is important for accurate rule checking and trade
reconstruction.
"""

from decimal import Decimal
from typing import Optional
from typing import Iterator

from ex_tmodel2.exchange import ModelExchange, Side, ChildOrder, OrderBookPriorityComparisonResultEntry, OrderBook, \
    OrdType
from ex_tmodel2.exchange.enums import PegPriceType
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass

TRANSACT_TIME_TAG = "#datetime"


@rule_check(
    rule_description="Signal Consistency",
    rule_tags=["signals"],
)
class RuleCheckSignalDownstreamEffects(RuleCheck):
    """
    Rule check that validates signal consistency in state transitions.

    This rule detects when multiple new child orders appear in a single
    transition, which usually indicates that multiple independent input
    signals have been mixed together. This can happen due to:
    - Concurrency effects in the source data
    - Incorrect transaction boundaries
    - Data aggregation issues

    When multiple new orders are detected, it suggests the transition
    cannot be cleanly split into individual transactions for analysis.
    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        # Several new statements usually mean that the traffic can't be easily
        # split into transactions. Most of the time this is due to concurrency
        # effects in the source data where multiple orders arrived simultaneously.
        if transition.input_signal.signal_type != "EOD":
            if len(audit_data.new_child_order_keys) > 1:
                # Check that there is no more inbounds than instruments
                if len(audit_data.new_child_order_keys) > len(audit_data.affected_instruments):
                    yield self.report_rule(transition,
                        f"Several {len(audit_data.new_child_order_keys)} input signals mixed",
                        False)

            # TODO: do we need to check for zero testcases
            if len(audit_data.testcases) > 1:
                yield self.report_rule(transition,
                    f"testcases per state transition - {len(audit_data.testcases)}",
                    False)

