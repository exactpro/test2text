"""
Instrument Sessions Module

This module contains rule checks for session transitions
"""

from decimal import Decimal
from typing import Optional
from typing import Iterator

from ex_tmodel2.exchange import ModelExchange, Side, ChildOrder, OrderBookPriorityComparisonResultEntry, OrderBook, \
    OrdType
from ex_tmodel2.exchange.enums import PegPriceType
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text, no_relevant
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass


@rule_check(
    rule_description="Session Transition",
    rule_tags=["sessions"],
)
class RuleCheckSessionTransitions(RuleCheck):
    """
    Rule check order book consistency
    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if audit_data.last_transition == "":
            return no_relevant

        valid_transitions = [
            "SubastaApertura->Continuo",
            "None->PreApertura",
            "PreApertura->SubastaApertura",
        ]

        yield report_rule_for_state_transition(transition,
            f"Session Transition {audit_data.last_transition}",
            audit_data.last_transition in valid_transitions)
