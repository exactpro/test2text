"""
Matching Rules Module

This module contains rule checks for validating order book matching priority.
It ensures that when trades occur, orders are executed in the correct priority
order according to exchange matching rules (e.g., price-time priority).
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
from ex_tmodel2.exchange.rules.base_matching import RuleCheckOrderBookPriorityBase

TRANSACT_TIME_TAG = "#datetime"

@rule_check(
    rule_description="Regular",
    rule_tags=["matching"],
)
class RuleCheckOrderBookPriority(RuleCheckOrderBookPriorityBase):
    """
    Rule check for regular (continuous trading) order book priority validation.

    This rule validates that during regular continuous trading sessions,
    orders are matched according to proper price-time priority. It extends
    the base matching rule but excludes auction trades (where executions
    occur without new orders being added).

    The rule is skipped when:
    - Executions occur with no inbound messages new orders/replaces (auction uncross scenario)

    For all other cases, it delegates to the base priority checking logic
    to verify that resting orders were filled in the correct sequence.
    """

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        # Skip auction trades - these are handled by RuleCheckAuction
        # Auction trades have executions but no new orders (uncross scenario)
        if len(audit_data.executed_child_order_keys) == 0:
            return no_relevant

        if audit_data.last_transition == "SubastaApertura->Continuo":
            return no_relevant

        # Delegate to base class for standard priority checking
        for rule in super().check(exchange, transition, exchange_next, audit_data):
            yield rule
