"""
Auction Uncross Rules Module

This module contains rule checks for validating auction uncross events.
Auctions (opening, closing, volatility, etc.) collect orders during a
call period and then execute them in a single uncross event at a
calculated auction price.

This module validates:
- Trade integrity during auction uncross
- Order book state before and after uncross (crossed/locked detection)
- Statistics about affected order books
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
    rule_description="Auction Priority",
    rule_tags=["matching"],
)
class RuleCheckAuction(RuleCheckOrderBookPriorityBase):
    """
    Rule check that validates execution priority
    """
    def __init__(self):
        # Minimum number of trades
        super().__init__()
        self.is_auction = True

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if audit_data.last_transition != "SubastaApertura->Continuo":
            return no_relevant

        # Skip if there are new orders - this is not an auction uncross
        if len(audit_data.new_child_order_keys) != 0:
            return no_relevant

        yield from super().check(exchange, transition, exchange_next, audit_data)



@rule_check(
    rule_description="Auction Uncross",
    rule_tags=["matching"],
)
class RuleCheckAuctionUncross(RuleCheck):
    """
    Rule check that validates trades during auction uncross events.

    This rule is triggered when executions occur without any new orders
    being added (characteristic of auction uncross). It validates:
    - Trade structure and integrity via base class checks
    - Reports statistics on affected order books
    - Tracks crossed/locked book states before and after uncross

    The rule collects and reports:
    - Number of affected order books
    - Number of executed orders
    - Number of trades generated
    - Non-empty, crossed, and locked book counts (before/after)

    This information helps verify that auctions properly uncross the
    order book and resolve any locked/crossed conditions.
    """
    def __init__(self):
        # Minimum number of trades
        super().__init__()

    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        testcase = None

        if audit_data.last_transition != "SubastaApertura->Continuo":
            return no_relevant

        yield self.report_rule(transition,
             f"Statistics trades={len(audit_data.trades)} executed orders={len(audit_data.executed_child_order_keys)}",
            True)

        open_prices = {"visible": {}, "hidden": {}}
        open_status = {"visible": {}, "hidden": {}}
        open_status_one = {"visible": {}, "hidden": {}}

        for instrument in audit_data.affected_instruments:
            if not instrument.configuration.enable_priority_checks:
                continue

            for order_book in exchange.instruments[instrument.key].order_books.values():
                for order in order_book.child_orders.values():
                    testcase = order.testcase

                market_data = order_book.to_market_data()
                market_data_with_hidden = order_book.to_market_data(include_hidden=True)

                md_str = f"{market_data_with_hidden.signature(structure_only=True)}"

                is_hidden_present = not market_data_with_hidden.compare(market_data)["equal"]
                if is_hidden_present:
                    md_str += f" visible {market_data.signature(structure_only=True)}"

                if market_data_with_hidden.is_crossed():
                    md_str += f" crossed"
                if market_data_with_hidden.is_locked():
                    md_str += f" locked"

                symbol = instrument.key
                auction_price = market_data.calculate_equilibrium_data()
                auction_price_with_hidden = market_data_with_hidden.calculate_equilibrium_data()

                if auction_price is not None:
                    number_of_max_executable_volume_levels = market_data.count_levels_at_max_executable_volume()
                    num_of_min_imbalance = market_data.count_levels_at_max_executable_and_min_imbalance()
                    pressure = market_data.get_pressure()

                    status_str = f"max_volume={number_of_max_executable_volume_levels} min_imbalance={num_of_min_imbalance} pressure={pressure}"
                    open_status["visible"][symbol] = status_str
                    status_one_str = f"max_volume_found={number_of_max_executable_volume_levels==1} min_imbalance_found={num_of_min_imbalance==1} pressure={pressure}"
                    open_status_one["visible"][symbol] = status_one_str

                    yield self.report_rule(transition,
                        f"Calculation number of levels {status_str}",
                        True, testcase=testcase)

                    open_prices["visible"][symbol] = auction_price

                # Copy of the above code with market_data -> market_data_with_hidden
                if auction_price_with_hidden is not None and is_hidden_present:
                    number_of_max_executable_volume_levels = market_data_with_hidden.count_levels_at_max_executable_volume()
                    num_of_min_imbalance = market_data_with_hidden.count_levels_at_max_executable_and_min_imbalance()
                    pressure = market_data_with_hidden.get_pressure()

                    status_str = f"max_volume={number_of_max_executable_volume_levels} min_imbalance={num_of_min_imbalance} pressure={pressure}"
                    open_status["hidden"][symbol] = status_str
                    status_one_str = f"max_volume_found={number_of_max_executable_volume_levels==1} min_imbalance_found={num_of_min_imbalance==1} pressure={pressure}"
                    open_status_one["hidden"][symbol] = status_one_str

                    yield self.report_rule(transition,
                        f"Calculation number of levels with hidden {status_str}",
                        True, testcase=testcase)

                    open_prices["hidden"][symbol] = auction_price_with_hidden

                yield self.report_rule(transition,
                f"Order book before {md_str}",
                    True, testcase=testcase)

        uncross_prices = {}
        for trade in audit_data.trades.values():
            for trade_side in trade.trade_sides:
                symbol = trade_side.instrument_key

                if not exchange.instruments[symbol].configuration.enable_priority_checks:
                    continue

                if symbol not in uncross_prices:
                    uncross_prices[symbol] = trade_side.price
                else:
                    yield report_rule_for_state_transition(transition,
               f"{self.rule_description} All trades have the same price during uncross",
                        trade_side.price == uncross_prices[symbol], testcase=trade_side.testcase)
                order_book = exchange.instruments[symbol].get_default_order_book()

                auction_price = open_prices["visible"].get(symbol)
                auction_status = open_status["visible"].get(symbol)
                auction_status_one = open_status_one["visible"].get(symbol)
                auction_price_details = f"{trade_side.instrument_key} calc={auction_price} vs trade={trade_side.price} {auction_status}"

                auction_price_with_hidden = open_prices["hidden"].get(symbol)
                auction_status_with_hidden = open_status["hidden"].get(symbol)
                auction_status_one_with_hidden = open_status_one["hidden"].get(symbol)
                auction_price_details_with_hidden = f"{trade_side.instrument_key} calc={auction_price_with_hidden} vs trade={trade_side.price} {auction_status_with_hidden}"

                result = (auction_price_with_hidden == trade_side.price) or (auction_price == trade_side.price)

                yield report_rule_for_state_transition(transition,
               f"{self.rule_description} Trade price matches auction price {auction_status}",
                    result,
                    testcase=trade_side.testcase,
                    description=auction_price_details)

                yield report_rule_for_state_transition(transition,
               f"{self.rule_description} [Summary] Trade price matches auction price {auction_status_one}",
                    result,
                    testcase=trade_side.testcase,
                    description=auction_price_details)

                if auction_price_with_hidden and auction_status_with_hidden != auction_price:

                    yield report_rule_for_state_transition(transition,
                   f"{self.rule_description} Trade price matches auction price with hidden {auction_status_with_hidden}",
                        result,
                        testcase=trade_side.testcase,
                        description=auction_price_details_with_hidden)

                    yield report_rule_for_state_transition(transition,
                   f"{self.rule_description} [Summary] Trade price matches auction price with hidden {auction_status_one_with_hidden}",
                        result,
                        testcase=trade_side.testcase,
                        description=auction_price_details_with_hidden)
