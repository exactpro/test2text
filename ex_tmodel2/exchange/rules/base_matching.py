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

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass

TRANSACT_TIME_TAG = "#datetime"

class RuleCheckOrderBookPriorityBase(RuleCheck):
    """
    Rule check that validates order book priority during trade execution.

    This rule verifies that when multiple resting orders are executed against
    an aggressive order, they are filled in the correct priority order.
    It checks:
    - Price-time priority among executed resting orders
    - Fully filled orders have higher priority than partially filled visible orders
    - Orders excluded due to Self-Trade Prevention (STP) are properly accounted for

    Use customisation options to control rule reporting details.
    """

    def __init__(self):
        # Optional custom comparison function for priority checks
        self.compare_func = None

        self.is_customise_include_comparison_stats = True
        self.is_customise_include_orderbook_structure = True
        self.is_customise_output_summary_line = True
        self.over_customise_include_order_tags = " over " # make it empty string not to output it

        self.is_auction = False

    def describe_order_in_order_priority_rule(self, order: ChildOrder) -> str:
        """
        Generate a human-readable description of an order for priority rule reporting.

        Args:
            order: The child order to describe

        Returns:
            A string describing the order's state (new/part-filled), type, peg type,
            and amendment count for diagnostic output.
        """
        order_str = f"{order.ordtype}".replace("OrdType.", "")

        if order.peg_price_type:
            order_str += f" {order.peg_price_type}"

        if order.amend_counter > 0:
            order_str += f" amended"
            if order.amend_counter > 1:
                order_str += f" {order.amend_counter} times"

        if order.replenishment_counter > 0:
            order_str += f" replenished"
            if order.replenishment_counter > 1:
                order_str += f" {order.replenishment_counter} times"

        if order.execution_counter > 0:
            order_str += f" executed"
            if order.execution_counter > 1:
                order_str += f" {order.execution_counter} times"

        if order.visible_quantity is not None:
            if order.visible_quantity > 0:
                order_str += " Iceberg"
            else:
                order_str += " Hidden"

        if order.peg_offset_value is not None:
            if order.peg_offset_value > 0:
                order_str += f" peg_offset>0"
            else:
                order_str += f" peg_offset<0"

        return f"'{order_str}'"

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if len(audit_data.executed_child_order_keys) > 0:
            for order_book in exchange.get_order_books_for_child_order_keys(audit_data.executed_child_order_keys):

                if not order_book.instrument.configuration.enable_priority_checks:
                    continue

                resting_executed_keys = list(order_book.child_orders.filter_present_keys(
                    audit_data.executed_child_order_keys & audit_data.resting_child_order_keys))

                if len(resting_executed_keys) == 0:
                    continue

                excluded_other_keys = {}

                for excluded_key in audit_data.canceled_by_stp_child_order_keys:
                    excluded_other_keys[excluded_key] = "Resting Canceled by STP"

                if self.is_auction:
                    aggresive_side = ''
                else:
                    aggresive_side = 'Sell' if order_book.child_orders[
                                                   resting_executed_keys[0]].side == Side.BUY else 'Buy'

                observations = order_book.check_orders_priority(resting_executed_keys,
                    comparison_func=self.compare_func,
                    excluded_other_keys=excluded_other_keys)

                full_filled_resting_executed_keys = set()
                part_filled_resting_executed_keys = set()

                # Also check fully filled orders have higher priority than part-filled fully visible
                for key in resting_executed_keys:
                    if key not in exchange_next.exchange_child_orders:
                        if exchange.exchange_child_orders[key].visible_quantity is None:
                            full_filled_resting_executed_keys.add(key)
                    else:
                        if exchange_next.exchange_child_orders[key].visible_quantity is None:
                            part_filled_resting_executed_keys.add(key)

                if len(full_filled_resting_executed_keys) > 0 and len(part_filled_resting_executed_keys) > 0:
                    observations.extend(order_book.check_orders_priority(full_filled_resting_executed_keys,
                        comparison_func=self.compare_func,
                        subset_of_other_keys=part_filled_resting_executed_keys))

                for entry in observations:
                    order1 = order_book.child_orders[entry.key1]
                    order2 = order_book.child_orders[entry.key2]

                    order1_str = self.describe_order_in_order_priority_rule(order1)
                    order2_str = self.describe_order_in_order_priority_rule(order2)

                    details_str = ""
                    if self.is_customise_include_comparison_stats:
                        details_str +=  f" {len(resting_executed_keys)} trades {len(observations)} comparisons"
                    if self.is_customise_include_orderbook_structure:
                        details_str += " " + order_book.signature(structure_only=True)
                    if self.over_customise_include_order_tags != None:
                        details_str += f" {order1_str}{self.over_customise_include_order_tags}{order2_str}"

                    if details_str != "":
                        yield self.report_rule(transition,
                             f"{aggresive_side} reason={entry.reason}{details_str}",
                             entry.has_higher_priority, testcase=order1.testcase,
                            description=f"{entry.key1} {entry.key2} {order1.memo} {order2.memo}"
                        )

                    if self.is_customise_output_summary_line:
                        yield self.report_rule(transition,
                             f"[Summary] {aggresive_side} reason={entry.reason}",
                             entry.has_higher_priority, testcase=order1.testcase)

                    if entry.has_higher_priority is False:
                        yield report_print_text(f"{entry.reason} {entry.has_higher_priority} {entry.key1} {entry.key2} {order1.memo} {order2.memo}")
                        yield report_print_text(order_book.print_contents())

                if len(observations) == 0:
                    details_str = ""
                    if self.is_customise_include_orderbook_structure:
                        details_str += " " + order_book.signature(structure_only=True)

                    yield self.report_rule(transition,
                         f"{aggresive_side}{details_str} {len(resting_executed_keys)} trades Nothing to compare",
                        True)

