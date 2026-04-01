"""
MD Protocol Reconciliation Rules Module

"""

from decimal import Decimal
from typing import Optional
from typing import Iterator
from ex_tmodel2.exchange import ModelExchange, Side, ChildOrder, OrderBookPriorityComparisonResultEntry, OrderBook, \
    OrdType
from ex_tmodel2.exchange.downstream_effects import OrderAcceptedEffect
from ex_tmodel2.exchange.enums import PegPriceType, OrdStatus, TimeInForce, IcebergTradeMode, TradingSessionSubID, \
    Printable
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

from ex_tmodel2.base.rule_base import report_rule_for_state_transition, report_print_text, RuleRunner
from ex_tmodel2.base.rule_base import rule_check, RuleCheck, ReportedRuleData, NoRelevantCheckClass

def is_market_data_relevant(exchange: ModelExchange, audit_data: ExchangeTransitionAudit, md_prefix: str = "MD:") -> bool:
    # Apply this rule only when MD: instruments are available
    for instrument in audit_data.affected_instruments:
        if instrument.key.startswith(md_prefix):
            return True
        if md_prefix + instrument.key in exchange.instruments:
            return True

    return False


@rule_check(
    rule_description="MarketDataVsTransactionalFeed",
    rule_tags=["reconciliation"],
)
class MarketDataVsTransactionalFeed(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        # Apply this rule only when MD: instruments are available
        if not is_market_data_relevant(exchange, audit_data):
            return

        md_instruments = set()
        tr_instruments = set()

        for order_book in audit_data.affected_order_books:
            instrument = order_book.instrument
            if instrument.key.startswith("MD:"):
                md_instruments.add(instrument.key.split(":")[1])
            elif instrument.key.startswith("MD1:"):
                continue
            elif instrument.key.startswith("SIP:"):
                continue
            else:
                tr_instruments.add(instrument.key)

        num_accepted = 0
        num_accepted_md = 0
        for effect in transition.downstream_effects:
            if isinstance(effect, OrderAcceptedEffect):
                if exchange_next.instruments[effect.instrument_key].configuration.enable_priority_checks:
                    num_accepted += 1
                else:
                    num_accepted_md += 1

        for instrument in audit_data.affected_instruments:
            if instrument.key.startswith("MD:"):
                continue
            if instrument.key.startswith("MD1:"):
                continue
            if instrument.key.startswith("SIP:"):
                continue
            if instrument.key.startswith("IIROC:"):
                instrument.key = instrument.key[len("IIROC:"):]
            instrument_itch = exchange_next.instruments[f"MD:{instrument.key}"]
            order_book = instrument.get_default_order_book()
            order_book_itch = instrument_itch.get_default_order_book()
            market_data = order_book.to_market_data()
            market_data_itch = order_book_itch.to_market_data()

            if market_data.signature() != market_data_itch.signature():
                if md_instruments != tr_instruments or num_accepted > 1 or num_accepted_md > 1:
                    yield self.report_rule(transition,
                       f"Possible timesync order book MD state mismatch signatures tr={len(tr_instruments)} vs md={len(md_instruments)} na={num_accepted} namd={num_accepted_md} {market_data.signature(structure_only=True)}",
                       market_data.signature() == market_data_itch.signature(),
                        description=f"{market_data.signature()} == {market_data_itch.signature()}")
                else:
                    yield self.report_rule(transition,
                       f"MD order book state mismatch signatures {market_data.signature(structure_only=True)}",
                       market_data.signature() == market_data_itch.signature(),
                        description=f"{market_data.signature()} == {market_data_itch.signature()}")
            elif RuleRunner.is_verbose():
                yield self.report_rule(transition,
                   f"MD order book state match signatures {market_data.signature(structure_only=True)}",
                   market_data.signature() == market_data_itch.signature(),
                   description=f"{market_data.signature()} == {market_data_itch.signature()}")



@rule_check(
    rule_description="MarketDataBookChecker",
    rule_tags=["reconciliation"],
)
class MarketDataBookChecker(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        # Apply this rule only when MD: instruments are available
        if not is_market_data_relevant(exchange, audit_data):
            return

        for order_book in audit_data.affected_order_books:
            instrument = order_book.instrument
            if not instrument.key.startswith("MD:"):
                continue
            if not instrument.key.startswith("MD1:"):
                continue
            if not instrument.key.startswith("SIP:"):
                continue
            market_data = order_book.to_market_data()

            is_crossed = market_data.is_crossed()
            is_locked = market_data.is_locked()

            if not is_crossed and not is_locked:
                if RuleRunner.is_verbose():
                    yield self.report_rule(transition,
                       f"MD order well formed {market_data.signature(structure_only=True)}",
                       not is_crossed,
                       description=f"{market_data.signature()}")
            else:
                yield self.report_rule(transition,
                   f"MD order book not crossed {market_data.signature(structure_only=True)}",
                   not is_crossed,
                   description=f"{market_data.signature()}")

                yield self.report_rule(transition,
                   f"MD order book not locked {market_data.signature(structure_only=True)}",
                   not is_locked,
                   description=f"{market_data.signature()}")


@rule_check(
    rule_description="MarketDataCompareAllPrintableVolumes",
    rule_tags=["trades"],
)
class MarketDataCompareAllPrintableVolumes(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        if transition.input_signal.signal_type != "EOD":
            return

        # Apply this rule only when MD: instruments are available
        md_instruments_found = False
        for symbol in exchange_next.instruments:
            if symbol.startswith("MD:"):
                md_instruments_found = True
                break
        if not md_instruments_found:
            return

        trades_printable_volume = {}
        trades_printable_buy = {}
        trades_printable_sell = {}

        for trade in exchange_next.trades.values():
            printable_volume = 0
            for trade_side in trade.trade_sides:
                if trade_side.printable == Printable.NO:
                    continue
                printable_volume += trade_side.quantity

                if trade_side.printable == Printable.NONE:
                    side = OrderBook.normalize_side(trade_side.side)
                    if side == Side.BUY:
                        trades_printable_buy[trade.key] = trade_side.quantity
                    if side == Side.SELL:
                        trades_printable_sell[trade.key] = trade_side.quantity

            trades_printable_volume[trade.key] = printable_volume

        printable_matched = 0

        for key, quantity in trades_printable_volume.items():
            if key.startswith("MD"):
                trade_id = key.split(":")[1]
                if trade_id not in trades_printable_volume:
                    yield self.report_rule(transition,
                           f"No transactional data for MD trade",
                           False, testcase=exchange_next.trades[key].testcase, description=trade_id)
                continue

            if key.startswith("MD1"):
                continue
            if key.startswith("SIP"):
                continue

            itch_trade_id = f"MD:{key}"
            if itch_trade_id not in trades_printable_volume:
                yield self.report_rule(transition,
               f"No MD trade for transactional data",
               False, testcase=exchange_next.trades[key].testcase, description=key)
                continue

            itch_quantity = trades_printable_volume[itch_trade_id]

            buy_quantity = trades_printable_buy.get(key, 0)
            sell_quantity = trades_printable_sell.get(key, 0)

            if quantity == itch_quantity * 2 and buy_quantity == sell_quantity:
                printable_matched += 1
            else:
                if buy_quantity != sell_quantity:
                    yield self.report_rule(transition,
                       f"MD printable quantity mismatch while data is absent for one side in transactional feed",
                       False, testcase=exchange_next.trades[key].testcase, description=f"{key} printable={itch_quantity} buy={buy_quantity} sell={sell_quantity} {exchange_next.trades[key].testcase}")
                else:
                    yield self.report_rule(transition,
                       f"MD printable quantity mismatch",
                       False, testcase=exchange_next.trades[key].testcase, description=f"{key} printable={itch_quantity} buy={buy_quantity} sell={sell_quantity} {exchange_next.trades[key].testcase}")

        yield self.report_rule(transition,
           f"Statistics number of MD printable quantity matches - {printable_matched}",
            True, "00ALL")


@rule_check(
    rule_description="MarketDataCompareOneStatePrintableVolumes",
    rule_tags=["trades"],
)
class MarketDataCompareOneStatePrintableVolumes(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        # Apply this rule only when MD: instruments are available
        if not is_market_data_relevant(exchange, audit_data):
            return

        trades_printable_volume = {}
        trades_printable_buy = {}
        trades_printable_sell = {}
        trades_printable_price = {}
        trades_printable_visibility = {}

        for trade in audit_data.trades.values():
            printable_volume = 0
            for trade_side in trade.trade_sides:
                if trade_side.printable == Printable.NO:
                    continue
                printable_volume += trade_side.quantity

                if trade_side.printable == Printable.NONE:
                    side = OrderBook.normalize_side(trade_side.side)
                    if side == Side.BUY:
                        trades_printable_buy[trade.key] = trade_side.quantity
                    if side == Side.SELL:
                        trades_printable_sell[trade.key] = trade_side.quantity

                trades_printable_price[trade.key] = trade_side.price
                trades_printable_visibility[trade.key] = trade_side.observed_iceberg_trade_mode

            trades_printable_volume[trade.key] = printable_volume

        printable_matched = 0

        for key, quantity in trades_printable_volume.items():
            if key.startswith("MD:"):
                trade_id = key.split(":")[1]
                if trade_id not in trades_printable_volume:
                    yield self.report_rule(transition,
                           f"No transactional data for MD trade",
                           False, testcase=exchange_next.trades[key].testcase, description=trade_id)
                continue

            if key.startswith("MD1:"):
                continue
            if key.startswith("SIP:"):
                continue

            itch_trade_id = f"MD:{key}"
            if itch_trade_id not in trades_printable_volume:
                yield self.report_rule(transition,
               f"No MD trade for transactional data",
               False, testcase=exchange_next.trades[key].testcase, description=key)
                continue

            itch_quantity = trades_printable_volume[itch_trade_id]

            buy_quantity = trades_printable_buy.get(key, 0)
            sell_quantity = trades_printable_sell.get(key, 0)

            is_trade_price_problem = trades_printable_price.get(key, 0) != trades_printable_price.get(itch_trade_id, 0)
            if RuleRunner.is_verbose() or is_trade_price_problem:
                yield self.report_rule(transition,
                   f"MD trade price match from TR",
                   not is_trade_price_problem, testcase=exchange_next.trades[key].testcase,
                   description=f"{key} tr={trades_printable_price.get(key, 0)} md={trades_printable_price.get(itch_trade_id, 0)}")

            is_trade_visibility_problem = trades_printable_visibility.get(key, 0) != trades_printable_visibility.get(itch_trade_id, 0)
            if RuleRunner.is_verbose() or is_trade_visibility_problem:
                yield self.report_rule(transition,
                   f"trade visibility match tr={trades_printable_visibility.get(key, 0)} md={trades_printable_visibility.get(itch_trade_id, 0)}",
                   not is_trade_visibility_problem, testcase=exchange_next.trades[key].testcase,
                   description=f"{key}")

            if quantity == itch_quantity * 2 and buy_quantity == sell_quantity:
                printable_matched += 1

                if RuleRunner.is_verbose():
                    yield self.report_rule(transition,
                       f"MD printable quantity match",
                       quantity == itch_quantity * 2 and buy_quantity == sell_quantity,
                       testcase=exchange_next.trades[key].testcase, description=f"{key} printable={itch_quantity} buy={buy_quantity} sell={sell_quantity} {exchange_next.trades[key].testcase}")

            else:
                if buy_quantity != sell_quantity:
                    yield self.report_rule(transition,
                       f"MD printable quantity mismatch while data is absent for one side in transactional feed",
                       False, testcase=exchange_next.trades[key].testcase, description=f"{key} printable={itch_quantity} buy={buy_quantity} sell={sell_quantity} {exchange_next.trades[key].testcase}")
                else:
                    yield self.report_rule(transition,
                       f"MD printable quantity mismatch",
                       False, testcase=exchange_next.trades[key].testcase, description=f"{key} printable={itch_quantity} buy={buy_quantity} sell={sell_quantity} {exchange_next.trades[key].testcase}")


@rule_check(
    rule_description="SIPMarketDataComparePrintableVolumes",
    rule_tags=["trades"],
)
class SIPMarketDataComparePrintableVolumes(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        # Apply this rule only when MD: instruments are available
        if not is_market_data_relevant(exchange, audit_data):
            return

        # Also check that SIP: instruments are available
        sip_instruments_found = False
        for instrument in audit_data.affected_instruments:
            if instrument.key.startswith("SIP:"):
                sip_instruments_found = True
                break
        if not sip_instruments_found:
            return

        # Collect printable volumes by price for MD: and SIP: trades
        md_volume_by_price = {}
        sip_volume_by_price = {}

        for trade in audit_data.trades.values():
            for trade_side in trade.trade_sides:
                if trade_side.printable == Printable.NO:
                    continue

                price = trade_side.price
                quantity = trade_side.quantity

                if trade.key.startswith("MD:"):
                    md_volume_by_price[price] = md_volume_by_price.get(price, 0) + quantity
                elif trade.key.startswith("SIP:"):
                    sip_volume_by_price[price] = sip_volume_by_price.get(price, 0) + quantity

        # Compare volumes at each price level
        all_prices = set(md_volume_by_price.keys()) | set(sip_volume_by_price.keys())

        for price in sorted(all_prices):
            md_vol = md_volume_by_price.get(price, 0)
            sip_vol = sip_volume_by_price.get(price, 0)

            if md_vol == sip_vol:
                if RuleRunner.is_verbose():
                    yield self.report_rule(transition,
                        f"MD vs SIP printable volume match",
                        True,
                        description=f"price={price} md={md_vol} sip={sip_vol}")
            else:
                yield self.report_rule(transition,
                    f"MD vs SIP printable volume mismatch",
                    False,
                    description=f"price={price} md={md_vol} sip={sip_vol}")
