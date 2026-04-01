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


@rule_check(
    rule_description="Order Books EOD",
    rule_tags=["signals"],
)
class RuleCheckSignalOrderBookEOD(RuleCheck):
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

        # Check for non-empty books at EOD and SOD
        signal_type = transition.input_signal.signal_type

        non_empty_count = 0
        all_books_count = 0

        if signal_type in ["EOD"] and len(exchange_next.exchange_child_orders) > 0:
            for symbol, instrument in exchange_next.instruments.items():
                all_books_count += 1

                if len(instrument.instrument_child_orders) == 0:
                    continue

                non_empty_count += 1

                signature = instrument.get_default_order_book().signature(structure_only=True)

                yield self.report_rule(transition,
                    f"{signal_type} order book not empty {signature}",
                    True, testcase=signal_type)

                yield self.report_rule(transition,
                    f"{signal_type} order book not empty {signature} {instrument.key}",
                    True, testcase=signal_type)

            yield self.report_rule(transition,
                f"{signal_type} order book not empty - {non_empty_count} / {all_books_count}",
                non_empty_count == 0, testcase=signal_type)


@rule_check(
    rule_description="Order Books SOD",
    rule_tags=["signals"],
)
class RuleCheckSignalOrderBookSOD(RuleCheck):
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

        # Check for non-empty books at EOD and SOD
        signal_type = transition.input_signal.signal_type

        if signal_type in ["SOD"]:
            for instrument in audit_data.affected_instruments:

                if len(instrument.instrument_child_orders) == 0:
                    continue

                signature = instrument.get_default_order_book().signature(structure_only=True)

                yield self.report_rule(transition,
                    f"{signal_type} order book not empty {signature}",
                    True, testcase=signal_type)

                yield self.report_rule(transition,
                    f"{signal_type} order book not empty {signature} {instrument.key}",
                    True, testcase=signal_type)
