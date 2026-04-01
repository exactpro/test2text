"""
Trade Rules Module

This module contains rule checks for consistency in trade sides
"""

from decimal import Decimal
from typing import Optional
from typing import Iterator

from ex_tmodel2.exchange import ModelExchange, Side, ChildOrder, OrderBookPriorityComparisonResultEntry, OrderBook, \
    OrdType
from ex_tmodel2.exchange.enums import PegPriceType, LastLiquidityInd, Printable, IcebergTradeMode
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text, no_relevant, RuleRunner
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass
from ex_tmodel2.exchange.trades import TradeSide


@rule_check(
    rule_description="AllTradesPrices",
    rule_tags=["trades"],
)
class RuleCheckAllTradesPrices(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if transition.input_signal.signal_type != "EOD":
            return no_relevant

        good_limit_price_count = 0
        good_trade_price_match_count = 0

        for trade in exchange_next.trades.values():
            price = None
            is_problem = False

            for trade_side in trade.trade_sides:
                testcase = trade_side.testcase
                instrument = exchange_next.instruments[trade_side.instrument_key]
                ignore_limit_price = False
                if instrument.configuration.enable_limit_price_check is False:
                    ignore_limit_price = True

                if RuleRunner.is_verbose():
                        yield report_rule_for_state_transition(transition,
                           f"Trade in Session {instrument.status.session}",
                           True, testcase=testcase)

                if price is None:
                    price = trade_side.price
                else:
                    good_trade_price_match_count += 1

                    if price != trade_side.price or RuleRunner.is_verbose():
                        yield self.report_rule(transition,
                           f"Trade price match on both sides",
                           price == trade_side.price, testcase=testcase, description=trade.key + " " + testcase)

                    if OrderBook.normalize_side(trade_side.side) == Side.BUY:
                        if trade_side.limit_price is not None:
                            if trade_side.limit_price < trade_side.price or RuleRunner.is_verbose():
                                yield self.report_rule(transition,
                               f"Trade buy limit price >= trade price{' (Ignore)' if ignore_limit_price and trade_side.limit_price < trade_side.price else ''}",
                               ignore_limit_price or trade_side.limit_price >= trade_side.price, testcase=trade_side.testcase, description=trade.key + " " + testcase)

                            if trade_side.limit_price < trade_side.price:
                                is_problem = True
                            else:
                                good_limit_price_count += 1

                    if OrderBook.normalize_side(trade_side.side) == Side.SELL:
                        if trade_side.limit_price is not None:
                            if trade_side.limit_price > trade_side.price or RuleRunner.is_verbose():
                                yield self.report_rule(transition,
                               f"Trade sell limit price <= trade price{' (Ignore)' if ignore_limit_price and trade_side.limit_price > trade_side.price else ''}",
                               ignore_limit_price or trade_side.limit_price <= trade_side.price, testcase=trade_side.testcase, description=trade.key + " " + testcase)

                            if trade_side.limit_price > trade_side.price:
                                is_problem = True
                            else:
                                good_limit_price_count += 1

                    is_problem = is_problem or (trade_side.price != price)

            if is_problem:
                for trade_side in trade.trade_sides:
                    yield report_print_text(f"{trade_side.side} {trade_side.quantity}@{trade_side.price}")

        yield self.report_rule(transition,
           f"Statistics number limit price violation checks - {good_limit_price_count}",
            True, testcase="00ALL")
        yield self.report_rule(transition,
           f"Statistics number of trades prices match on both sides - {good_trade_price_match_count}",
            True, testcase="00ALL")


@rule_check(
    rule_description="AllTradesPrintableNoneQuantityMatching",
    rule_tags=["trades"],
)
class RuleCheckAllTradesPrintableNoneQuantityMatching(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if transition.input_signal.signal_type != "EOD":
            return no_relevant

        good_trade_quantity_match_count = 0
        good_unspecified_printable_both_sides_count = 0

        trade_stats = {}

        for trade in exchange_next.trades.values():

            buy_found = 0
            sell_found = 0

            quantity = None
            is_problem = False
            observed_iceberg_trade_mode = IcebergTradeMode.UNDEFINED

            for trade_side in trade.trade_sides:
                testcase = trade_side.testcase

                trade_str = f"{trade_side.side} {trade_side.last_liquidity_indicator} {trade_side.iceberg_trade_mode} {trade_side.printable}"
                trade_stats[trade_str] = trade_stats.get(trade_str, 0) + 1

                if trade_side.printable != Printable.NONE:
                    continue

                if OrderBook.normalize_side(trade_side.side) == Side.BUY:
                    buy_found += 1

                if OrderBook.normalize_side(trade_side.side) == Side.SELL:
                    sell_found += 1

                if quantity is None:
                    quantity = trade_side.quantity
                    observed_iceberg_trade_mode = trade_side.observed_iceberg_trade_mode
                else:
                    is_problem = is_problem or (trade_side.quantity != quantity)

                    if trade_side.observed_iceberg_trade_mode != observed_iceberg_trade_mode:
                        is_problem = True
                        yield self.report_rule(transition,
                       f"Mismatch {observed_iceberg_trade_mode} {trade_side.observed_iceberg_trade_mode} sides",
                        False, testcase=testcase, description=trade.key + " " + testcase
                        )

            sides_are_ok = True
            if buy_found + sell_found not in [0, 2]:
                yield self.report_rule(transition,
               f"Trade has {buy_found + sell_found} sides",
                False, testcase=testcase, description=trade.key + " " + testcase
                )
                sides_are_ok = False
            if sell_found == 1 and buy_found != 1:
                yield self.report_rule(transition,
           f"Trade has buy side",
                    False, testcase=testcase, description=trade.key + " " + testcase)
                sides_are_ok = False
            if buy_found == 1 and sell_found != 1:
                yield self.report_rule(transition,
        f"Trade has sell side",
                    False, testcase=testcase, description=trade.key + " " + testcase)
                sides_are_ok = False

            if sides_are_ok:
                good_unspecified_printable_both_sides_count += 1

            if is_problem:
                for trade_side in trade.trade_sides:
                    yield report_print_text(f"{trade_side.side} {trade_side.quantity}@{trade_side.price}")

        yield self.report_rule(transition,
           f"Statistics number of trades quantity match on both sides - {good_trade_quantity_match_count}",
            True, testcase="00ALL")
        yield self.report_rule(transition,
           f"Statistics number of trades with printable=unspecified with both sides present - {good_unspecified_printable_both_sides_count}",
            True, testcase="00ALL")

        for description, count in trade_stats.items():
            yield self.report_rule(transition,
               f"Statistics number of {description} - {count}",
               True, testcase="00ALL")


@rule_check(
    rule_description="AllTradesPrintable",
    rule_tags=["trades"],
)
class RuleCheckAllTradesPrintable(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if transition.input_signal.signal_type != "EOD":
            return no_relevant

        all_sides_printable = {}

        for trade in exchange_next.trades.values():

            sides_printable_count = {}
            sides_printable_quantity = {}

            for trade_side in trade.trade_sides:
                testcase = trade_side.testcase

                sides_printable_count[trade_side.printable] = sides_printable_count.get(trade_side.printable, 0) + 1
                sides_printable_quantity[trade_side.printable] = sides_printable_quantity.get(trade_side.printable, 0) + trade_side.quantity
                all_sides_printable[trade_side.printable] = all_sides_printable.get(trade_side.printable, 0) + 1

            if sides_printable_count.get(Printable.YES, 0) > 1:
                yield self.report_rule(transition,
                   f"Trade printable=Y count={sides_printable_count.get(Printable.YES, 0)}",
                True, testcase=testcase, description=trade.key + " " + testcase)

            if sides_printable_count.get(Printable.NO, 0) > 1:
                yield self.report_rule(transition,
                   f"Trade printable=N count={sides_printable_count.get(Printable.NO, 0)}",
                    True, testcase=testcase, description=trade.key + " " + testcase)

        for printable, count in all_sides_printable.items():
            yield self.report_rule(transition,
               f"Statistics number of printable={printable} - {count}",
               True, testcase="00ALL")


@rule_check(
    rule_description="TradeSides",
    rule_tags=["trades"],
)
class RuleCheckTradeSide(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        for trade in audit_data.trades.values():
            for trade_side in trade.trade_sides:
                if trade_side.side == Side.CROSS:
                    continue

                instrument = exchange_next.instruments[trade_side.instrument_key]
                ignore_limit_price = False
                if instrument.configuration.enable_limit_price_check is False:
                    ignore_limit_price = True

                status = True

                if trade_side.leaves_quantity == 0:
                    trade_str = " Full fill"
                elif trade_side.leaves_quantity > 0:
                    trade_str = " Part fill"
                else:
                    if trade_side.last_liquidity_indicator == LastLiquidityInd.ADDED:
                        trade_str = " Overfill"
                        status = False
                    else:
                        trade_str = " Trade more than before replace"

                    yield report_print_text(f"{trade.timestamp} {trade_side}")

                trade_str += f" {trade_side.side} {trade_side.last_liquidity_indicator} {trade_side.iceberg_trade_mode}"

                yield self.report_rule(transition,
                    f"Trade{trade_str}", status,
                        testcase=trade_side.testcase)

                if OrderBook.normalize_side(trade_side.side) == Side.BUY:
                    if trade_side.limit_price is not None:
                        if trade_side.limit_price < trade_side.price or RuleRunner.is_verbose():
                            yield self.report_rule(transition,
                               f"Trade buy limit price >= trade price{' (Ignore)' if ignore_limit_price and trade_side.limit_price < trade_side.price else ''}",
                               ignore_limit_price or trade_side.limit_price >= trade_side.price, testcase=trade_side.testcase)

                if OrderBook.normalize_side(trade_side.side) == Side.SELL:
                    if trade_side.limit_price is not None:
                        if trade_side.limit_price > trade_side.price or RuleRunner.is_verbose():
                            yield self.report_rule(transition,
                               f"Trade sell limit price <= trade price{' (Ignore)' if ignore_limit_price and trade_side.limit_price > trade_side.price else ''}",
                               ignore_limit_price or trade_side.limit_price <= trade_side.price, testcase=trade_side.testcase)
