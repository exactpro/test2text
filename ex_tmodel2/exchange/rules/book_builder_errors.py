"""
Book Builder Errors Module

This module contains rule checks for detecting and reporting errors that occur
during the book building process. Book builder errors typically indicate issues
with order processing, such as missing orders, invalid state transitions, or
data inconsistencies in the exchange model.

These errors are captured during the transition processing and reported here
for diagnostic purposes.
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
    rule_description="Book Builder",
    rule_tags=["errors"],
)
class BookBuilderErrors(RuleCheck):
    """
    Rule check that reports book builder errors from state transitions.

    This rule surfaces any exceptions or errors that occurred during the
    processing of a state transition by the ModelExchange. These errors
    are collected in the ExchangeTransitionAudit and indicate problems
    such as:
    - Order not found when processing cancel/replace/execute effects
    - Invalid state changes
    - Data consistency issues

    All transition exceptions are yielded as rule check failures for
    investigation and debugging.
    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        # Yield all exceptions that occurred during transition processing
        for problem in audit_data.transition_exceptions:
            yield problem



@rule_check(
    rule_description="Observations",
    rule_tags=["errors"],
)
class BookBuilderObservations(RuleCheck):
    """
    Rule check that reports a set of audit events.

    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        # Yield all exceptions that occurred during transition processing
        for problem in audit_data.transition_observations:
            yield problem