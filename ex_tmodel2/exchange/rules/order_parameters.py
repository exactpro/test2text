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
    OrdType, Trade
from ex_tmodel2.exchange.enums import PegPriceType
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text, no_relevant, RuleRunner
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass

TRANSACT_TIME_TAG = "#datetime"

@rule_check(
    rule_description="Expirations",
    rule_tags=["orders"],
)
class RuleCheckNonRestingExpirations(RuleCheck):
    """
    """
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if len(audit_data.non_resting_child_order_keys) == 0:
            return no_relevant

        for order_key in audit_data.non_resting_child_order_keys:
            if order_key in exchange_next.exchange_child_orders:
                order = exchange_next.exchange_child_orders[order_key]

                yield report_rule_for_state_transition(transition,
                    f"Non-resting order is not in the book ordtype={order.ordtype} tif={order.tif} order_status={order.order_status} {order.instrument.status.session}",
                    order_key not in exchange_next.exchange_child_orders)

                for order_book in order.instrument.order_books.values():
                    yield report_print_text(order_book.print_contents())

            elif RuleRunner.is_verbose():
                yield report_rule_for_state_transition(transition,
                    f"Non-resting order is not in the book",
                    order_key not in exchange_next.exchange_child_orders)

